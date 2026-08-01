# Introduction

**TL;DR** - A system design interview tests whether you can turn a vague prompt ("design Instagram") into a working architecture under time pressure. It is not about memorizing components. It is about a repeatable method: clarify requirements, estimate scale, sketch a high-level design, then go deep on the two or three parts that actually matter. This series teaches that method plus the building blocks every design reuses.

>> 30-second framing: "A system design interview is a structured conversation. I drive it with a framework - requirements first, then a simple design, then targeted deep dives on the bottlenecks. The interviewer is checking how I reason about trade-offs at scale, not whether I can recite a list of databases."

---

## What a System Design Interview Actually Measures

A coding interview has a right answer. A system design interview does not. The prompt is deliberately open: "Design a URL shortener," "Design Twitter," "Design a ride-sharing service." Your job is to impose structure on ambiguity.

Interviewers evaluate four things. **Requirements gathering** - do you scope the problem before building, or do you start drawing boxes blindly? **High-level design** - can you produce a coherent architecture that satisfies the requirements? **Deep dives** - when pushed on a specific component, do you understand the trade-offs? **Communication** - can you explain decisions and adjust when challenged?

![How a system design interview is scored across four dimensions](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/interview-scenarios.svg)

The most common failure mode is jumping straight to a solution. A candidate hears "design Twitter" and immediately starts talking about Redis and Kafka. Strong candidates pause, ask what scale we are targeting, what the read/write ratio looks like, and which features are in scope. That pause is the single biggest signal of seniority.

![Read-heavy versus write-heavy workloads shape every design decision](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/read-write-ratio.svg)

---

## The Delivery Framework

Every problem in this series uses the same skeleton. Memorize the skeleton, not the answers.

> **Step 1 - Requirements.** Separate functional requirements (what the system does: post a tweet, view a feed) from non-functional requirements (how well it does it: availability, latency, consistency). Pin down scale: daily active users, requests per second, data volume.
> **Step 2 - Core entities and API.** Define the nouns (User, Tweet, Follow) and the endpoints that act on them. This forces clarity before architecture.
> **Step 3 - High-level design.** Draw the boxes: clients, load balancer, application servers, databases, caches, queues. Make it satisfy the functional requirements end to end.
> **Step 4 - Deep dives.** Pick the two or three hardest parts and go deep. This is where the interview is won or lost.

![The delivery framework as a repeatable four-step skeleton](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/decision-tree.svg)

The deep dive is the part candidates underinvest in. Anyone can draw a load balancer in front of three servers. The interview separates levels by asking: what happens when one shard gets ten times the traffic of the others? What happens when the cache and database disagree? How do you avoid double-charging a user when a request retries?

{{PAYWALL}}

---

## The Building Blocks You Will Reuse

Almost every design is assembled from the same parts. Learn these once and you stop relearning them per problem.

### Scaling Reads and Writes

Reads and writes scale differently and fail differently. Reads dominate most consumer systems at ratios of 100:1 or higher, so you optimize them with replicas and caches. Writes are harder because they must be durable and ordered, so you scale them with sharding, queues, and append-only logs.

![Three-tier progression for scaling reads](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/scaling-reads-overview.svg)

![Scaling writes with sharding, batching, and queues](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/scaling-writes-overview.svg)

**Vertical scaling** means a bigger machine: more RAM, faster disk, more cores. It is simple and buys time, but it has a hard ceiling. **Horizontal scaling** means more machines working together. It scales further but adds coordination problems. Always reach for the database's own headroom before adding machines.

![Vertical versus horizontal scaling trade-offs](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/vertical-vs-horizontal.svg)

### Indexing and Data Modeling

An **index** is a sorted lookup structure that points to rows. Without one, the database does a full table scan, reading every row. With one, it jumps to the answer, turning an O(n) scan into an O(log n) lookup.

![B-tree index versus full table scan](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/indexing-btree.svg)

![Composite index and the leftmost-prefix rule](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/composite-index.svg)

**Denormalization** stores redundant data so reads avoid expensive joins. You trade storage and write complexity for read speed - a recurring theme.

![Denormalization trades storage for read speed](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/denormalization-tradeoff.svg)

### Replication

**Replication** copies data to additional servers. Writes go to a primary; reads can spread across replicas. This adds read capacity and redundancy, but introduces **replication lag**: a replica can briefly serve stale data after a write.

![Read replicas with leader-follower replication](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/read-replicas-flow.svg)

![Replication lag and the read-your-own-writes problem](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/replication-lag-problem.svg)

![Write-ahead log shipping between primary and replica](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/wal-replication.svg)

### Sharding

When one database cannot hold the data or absorb the writes, **sharding** splits it across many. The hard part is choosing a shard key that spreads load evenly without creating hot spots.

![Functional sharding by business domain](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/functional-sharding.svg)

![Geographic sharding for global traffic](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/geographic-sharding.svg)

![Hash-based sharding distributes records evenly](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/sharding-distribution.svg)

### Caching

A **cache** keeps hot data in memory so reads skip the database entirely. The default pattern is **cache-aside**: check the cache, fall back to the database on a miss, then populate the cache. The recurring danger is stale data and cache invalidation.

![Cache layers from client to CDN to application](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/caching-layers-overview.svg)

![Cache-aside read path](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/cache-aside-flow.svg)

![CDN edge caching for global low latency](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/cdn-edge-caching.svg)

### Concurrency and Contention

When many requests touch the same row, you get races: double bookings, lost updates, oversold inventory. **Pessimistic locking** blocks others while you work; **optimistic locking** lets everyone proceed and rejects conflicts at commit. Picking the right one depends on how often conflicts actually happen.

![Dealing with contention overview](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/dealing-with-contention-overview.svg)

![Optimistic versus pessimistic locking](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/dc-optimistic-vs-pessimistic.svg)

### Real-time and Asynchronous Work

Some features need updates pushed to clients (chat, live scores); others need slow work moved off the request path (video transcoding, report generation). The first is a networking problem; the second is a queueing problem.

![Real-time update mechanisms from polling to WebSockets](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/real-time-updates-overview.svg)

![Where each protocol sits in the OSI model](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/rt-osi-layers.svg)

![Synchronous request path versus asynchronous worker queue](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/lt-sync-vs-async.svg)

### Multi-step Processes

Real systems coordinate steps that can each fail: reserve seat, charge card, send confirmation. You need ways to retry safely and undo partial work, which is where idempotency and sagas come in.

![Coordinating multi-step workflows with retries and compensation](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/multi-step-processes-overview.svg)

### Numbers to Know

Good estimates separate plausible designs from hand-waving. Memorize an order-of-magnitude latency table: memory access in nanoseconds, an SSD read in microseconds, a cross-continent round trip in the low hundreds of milliseconds. These numbers justify why you cache, why you put a CDN at the edge, and why a synchronous cross-region call is a bad idea.

![Latency numbers every engineer should know](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/latency-comparison.svg)

---

## How to Use This Series

The curriculum has three layers. **Core concepts** teach the building blocks above in isolation. **Key technologies** (Redis, Kafka, Cassandra, and others) show how real systems implement those concepts. **Question breakdowns** put it all together on named problems like Bit.ly, Ticketmaster, and Uber.

![How the parts compose into a complete system](https://raw.githubusercontent.com/jimmymalhan/systemdesignlaws.xyz/feature/newsletter-agent-system/newsletter/plots/svg/scaling-summary.svg)

Work the concepts first so the question breakdowns feel like assembly rather than discovery. By the time you reach "Design Twitter," you should recognize it as a read-heavy feed problem (fan-out, caching, replication) rather than a blank page.

---

## Common Interview Questions

- **Do I need to know exact numbers in estimation?** No. Order-of-magnitude is enough. The point is to justify decisions, for example "100M daily users at 10 requests each is roughly 12,000 requests per second average, with peaks several times higher."
- **Should I start with the database schema or the API?** Define core entities and the API first. The schema follows from access patterns you discover during deep dives.
- **How many deep dives should I cover?** Two or three done well beats five done shallowly. Let the interviewer steer toward what they care about.
- **What if I do not know a specific technology?** Reason from first principles. Describe the behavior you need (durable ordered writes, low-latency lookups) and the interviewer will recognize the component even if you forget its name.
- **Is it bad to change my design mid-interview?** No. Revising a decision when shown a new constraint is exactly the senior behavior interviewers reward. Stubbornly defending a bad choice is the failure.

---

## Summary

A system design interview rewards method over memorization. Drive the conversation with the delivery framework: requirements, entities and API, high-level design, then deep dives. Build every design from the same reusable parts - scaling, indexing, replication, sharding, caching, concurrency control, real-time, and asynchronous processing - and justify each choice with rough numbers and explicit trade-offs.

>> The candidates who pass are not the ones who know the most components. They are the ones who scope ruthlessly, design the simplest thing that works, and go deep exactly where the system would actually break.

{{SUBSCRIBE}}

{{BUTTON:Read More Articles|https://newsletter.systemdesignlaws.xyz}}
