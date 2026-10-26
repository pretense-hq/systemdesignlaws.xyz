# Design a Distributed Rate Limiter

**TL;DR** - Enforce limits in the gateway, keep per-client state in sharded Redis, run each check as one atomic Lua script, default to token bucket, and decide in advance what happens when Redis is down.

>> 30-second elevator pitch: "Each gateway asks a shared Redis cluster, via one atomic Lua script, whether this client has budget left. I default to token bucket, enforce locally per region with async sync, and pick fail-open or fail-closed per endpoint."

---

## What You Will Learn

> **The core design** - requirements and capacity math, entities and API, where the limiter lives
>
> **Deep Dives** - token bucket vs sliding window log vs sliding window counter, atomic checks with Lua, multi-region enforcement, fail-open vs fail-closed

---

## Requirements

**What is a rate limiter?** A component that counts requests per client over time and rejects those over a configured budget, usually with HTTP 429 Too Many Requests. It shields backends, blunts abuse like credential stuffing, and enforces plan quotas.

**Functional**
- Limit by user ID, API key, IP, or endpoint, with rules per plan.
- Return 429 with remaining budget and a retry-after hint.
- Change rules at runtime, with zero redeploys.

**Non-functional**
- **Scale** - 1M checks/sec at peak across 100M active client keys.
- **Latency** - under 1 ms added at p50, 5 ms at most.
- **Accuracy** - small overshoot is fine; systematic double-spending must be prevented.
- **Availability** - the API must stay up through a limiter outage.

**Capacity math.** A Redis primary handles roughly 100K simple ops/sec. A Lua script costs more, so budget 50K checks/sec per shard: 1,000,000 / 50,000 = 20 primaries, plus 50% headroom = 30 primaries, plus one replica each = 60 nodes. Token bucket state is two fields; with key and overhead, call it 100 bytes. 100M keys x 100 bytes = 10 GB, about 333 MB per shard. Throughput sizes the cluster; memory fits with room to spare.

---

## Core Entities and API

- **Rule** - scope (user, key, IP, endpoint), algorithm, capacity, refill rate or window. Stored in a config DB, cached in each gateway, refreshed every 30 s.
- **Client key** - the identity being limited, such as an API key plus endpoint.
- **Bucket state** - tokens remaining and last refill time in milliseconds, with a TTL so idle keys expire.

The internal API is one call: check limit (client key, rule ID, cost), returning allowed, remaining, and retry-after. The gateway turns a rejection into 429 with X-RateLimit-Remaining and Retry-After headers.

---

## High-Level Design

<!-- DIAGRAM: Clients to load balancer to gateway with limiter middleware to sharded Redis; rules DB feeding gateway cache; allowed requests reach backends, rejected get 429 -->

Client-side limiters are trivially bypassed, and a standalone limiter service adds a hop. Gateway middleware already authenticates every request, so it knows the client key before calling Redis.

Flow: resolve the client key, look up the rule in the local cache, send one script call to the Redis shard owning that key, then forward or return 429. Redis Cluster hashes keys across shards, so adding shards adds throughput.

{{PAYWALL}}

---

## Deep Dive 1: Choosing the Algorithm

<!-- DIAGRAM: Timelines for fixed window boundary burst, token bucket drain and refill, sliding log timestamps, sliding counter weighting -->

**What is a fixed window counter?** One counter per minute, reset on the boundary. With 100/min, a client sends 100 at 0:59 and 100 at 1:00: 200 requests in two seconds.

**What is a token bucket?** A bucket holds up to capacity tokens, refilled at a fixed rate; each request spends one, and an empty bucket rejects. Refill is computed lazily: tokens = min(capacity, tokens + elapsed x rate). With capacity 20, rate 10/s, 4 tokens left and 0.5 s elapsed: 4 + 0.5 x 10 = 9 tokens.

**What is a sliding window log?** Store every accepted request's timestamp in a sorted set, drop entries older than the window, and allow if the count is under the limit. Exact, but memory grows with traffic: 100M keys x 100 entries x 64 bytes = 640 GB, versus 10 GB for token bucket.

**What is a sliding window counter?** Keep this window's count and the previous window's, and weight the previous one by how much still overlaps. Limit 100/min, previous minute 80, current 30, 15 seconds in: the previous window covers 45/60 = 0.75 of the rolling minute, so the estimate is 80 x 0.75 + 30 = 90. Allowed. It assumes the previous minute was evenly spread, which is close enough.

- **Token bucket** - Pros: controlled bursts, two fields of state. Cons: two knobs to tune. The default.
- **Sliding window log** - Pros: exact. Cons: memory scales with volume. Only for low-volume, high-stakes limits like logins.
- **Sliding window counter** - Pros: smooth, tiny state. Cons: approximate. For strict per-minute limits.

---

## Deep Dive 2: Atomicity in Redis with Lua

<!-- DIAGRAM: Two gateways both read tokens = 1 and both allow, versus one Lua script serializing them so the second rejects -->

Naively, the gateway reads the bucket, computes, and writes back. Two nodes serving the same client at once both read tokens = 1, both allow, and both write 0.

**What is a Lua script in Redis?** A small program Redis runs to completion before executing any other command. Read, refill math, decision and write become one atomic step in one round trip.

The script reads the bucket, takes the current time from Redis itself so gateway clock drift is irrelevant, refills and decides, then writes back with a TTL equal to the time to refill to capacity (20 / 10 per second = 2 seconds).

Trap: INCR then a separate EXPIRE runs as two separate commands; if the caller dies between them, the key persists forever and the client stays blocked. In Redis Cluster, every key a script touches must share a hash slot, so keep each check to one key.

---

## Deep Dive 3: Multi-Region

<!-- DIAGRAM: Three regions with local Redis; option A routes each key to a home region, option B enforces locally and syncs counts every 500 ms -->

Calling a central Redis from every region costs 70-150 ms per request, far past the 5 ms budget. Three options work:

- **Split the limit** - each of N regions gets limit / N. Simple, but a client whose traffic all lands in one region gets a third of its budget.
- **Home region** - route each API key to one region at DNS or the edge and enforce there. Exact; most clients call from one place, so few requests pay a cross-region hop. Right for billing quotas.
- **Local plus async sync** - each region enforces against its own count plus the last-known remote counts, broadcast every 500 ms. Worst case, every region spends the same remaining budget before hearing from the others: up to 3x the remaining budget per sync interval with 3 regions. Fine for abuse protection, since one client rarely sprays every region.

---

## Deep Dive 4: Fail-Open vs Fail-Closed

<!-- DIAGRAM: Redis timeout at 5 ms branches to fail open, fail closed, or a per-node local limiter -->

**What is fail-open?** Allow the request when the limiter is down or times out. Backends lose protection exactly when something is already wrong. Right for ordinary reads.

**What is fail-closed?** Reject when the limiter is down or times out. Protects SMS sends, payments and login endpoints, at the cost of an outage on those paths.

The middle path is an in-memory limiter on each gateway. With a 1,000/min limit and 50 nodes behind an even load balancer, each node allows 1,000 / 50 = 20/min per key: approximate but bounded. Wrap the Redis call in a 5 ms timeout and a circuit breaker so a sick shard trips to the fallback instead of slowing every request.

---

## Common Interview Questions

- **"Why share counters instead of counting in each gateway's memory?"** - Each node sees a slice of traffic, so the effective limit multiplies by node count.
- **"Why Redis instead of a database?"** - Every request is a write. At 1M writes/sec you need in-memory speed, and losing a counter only grants a brief extra burst.
- **"How do you handle one abusive client?"** - It hammers a single shard. Cache rejections at the gateway until retry-after passes, so the client stops reaching Redis.
- **"How do you roll out a new rule safely?"** - Run it in shadow mode, logging would-be rejections, then enforce once the numbers look right.

---

## Summary

- **Placement** - gateway middleware with shared Redis state.
- **Algorithm** - token bucket by default; sliding counter for strict per-minute limits.
- **Atomicity** - one Lua script per check, Redis clock, TTL on every key.
- **Multi-region** - home region for quotas, local plus async sync for abuse.
- **Failure** - 5 ms timeout, circuit breaker, open or closed per endpoint.

{{SUBSCRIBE}}

{{BUTTON:Read More Articles|https://newsletter.systemdesignlaws.xyz}}
