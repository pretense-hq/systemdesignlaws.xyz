# API Gateway for System Design Interviews

**TL;DR** - An API gateway is the single front door for client traffic. It routes, authenticates, rate limits, reshapes payloads, terminates TLS and records telemetry so backend services share one copy of those features. Draw one for multi-service public APIs; skip it when there is one backend.

>> 30-second elevator pitch: "A load balancer spreads traffic over a stateless gateway fleet in three zones. The gateway authenticates the caller, applies per-user rate limits and routes by path to the owning service. Outbound calls to third parties leave through a separate egress proxy."

---

## What You Will Learn

> **Core jobs** - routing, authentication, rate limiting, transformation, TLS termination, observability
>
> **Neighbors** - gateway vs load balancer vs service mesh
>
> **Interview judgment** - when the box earns its place and when it is noise
>
> **Operations** - sizing, zone failure, single point of failure
>
> **Egress gateway** - the outbound mirror image

---

## The Starting Point

Picture a ride-sharing app split into rider, driver, pricing and payments services. With a separate entry point per service, the client must know four hostnames, and four teams each write their own token checks, rate limits and certificate handling. The weakest copy becomes the way in.

**What is an API gateway?** A reverse proxy between external clients and internal services that understands application-level requests (paths, headers, tokens). It applies shared policy once, then forwards each request to the service that owns it.

<!-- DIAGRAM: Mobile and web clients -> load balancer -> gateway fleet -> rider, driver, pricing, payments services; gateway box lists auth, rate limit, routing, logging -->

{{PAYWALL}}

---

## What a Gateway Does

### Routing

The gateway maps a request to a backend by path prefix, host or header: /rides goes to the rider service, /payments to payments. Clients see one stable address, so you can split or move services while clients keep the same app version. Weighted routes enable canaries, such as 5% of /pricing traffic to a new version.

### Authentication

**What is authentication?** Proving who the caller is. The gateway validates the token on every request, answers invalid ones with a 401 before they consume backend capacity, and forwards a trusted identity header downstream. Fine-grained authorization ("may this user cancel this ride?") stays in the owning service, which has the data to decide.

### Rate Limiting

**What is rate limiting?** Capping how many requests a caller may make per time window. A token bucket per user or API key allows short bursts while enforcing an average rate. Over-limit callers get a 429.

The trap: with a limit of 100 requests per minute and 9 gateway instances counting locally, round-robin spreading lets one user through up to 9 x 100 = 900 requests per minute. The fix is a shared counter in an in-memory store that every instance increments, at the cost of one extra in-zone round trip per request, typically under a millisecond. Decide in advance whether to fail open or fail closed if that store goes down.

### Request and Response Transformation

The gateway can rewrite headers, translate protocols (JSON at the edge, binary RPC inside), strip internal fields, or merge several backend calls into one response. Keep it mechanical; business logic in the gateway makes every product change touch a shared component.

### TLS Termination

**What is TLS termination?** Decrypting HTTPS at the gateway so handshakes and certificates are managed in one place. Behind it, traffic is either re-encrypted, often with mutual TLS where both sides present certificates, or sent in plain text on a trusted network. For payments or health data, re-encrypt.

### Observability

Every request passes through, so the gateway emits access logs, latency histograms, status-code counts and a trace ID that downstream services propagate.

<!-- DIAGRAM: Request pipeline inside the gateway: TLS decrypt -> authenticate -> rate limit check against shared counter -> route lookup -> transform -> forward, with a trace ID attached at the start -->

---

## Gateway vs Load Balancer vs Service Mesh

- **Load balancer** - Spreads traffic across identical replicas at layer 4 (TCP) or layer 7 (HTTP). Knows replica health; user identity is the gateway's job.
- **API gateway** - Layer 7 policy for north-south traffic (clients entering the system). Knows identities, quotas, routes and versions.
- **Service mesh** - A proxy beside every service instance handling east-west traffic (service to service): mutual TLS, retries, timeouts, per-hop telemetry.

They stack: client -> layer 4 load balancer -> gateway fleet -> services, with a mesh between services. The quick test: if a component decides based on who the caller is, it is a gateway.

<!-- DIAGRAM: North-south arrow from internet through load balancer and gateway; east-west arrows between services passing through sidecar proxies labeled mesh -->

---

## When to Draw One in an Interview

**Draw it when:**

- Three or more services sit behind a public API.
- Third-party developers call the API, so keys, quotas and versioning matter.
- The prompt is a rate limiter, public API platform or multi-tenant SaaS.

**It is noise when:**

- There is one backend. A load balancer is enough.
- The interview is about storage, ranking or a data pipeline. Draw one box labeled "gateway (auth, rate limit)" and move on.
- Callers are internal batch jobs.

>> Strong candidates name the gateway, state the two or three jobs it does in this design, and spend their time on the core of the design.

---

## Scaling and the Single Point of Failure

The follow-up is always "is this a single point of failure?" It is one logical point deployed as many stateless instances. State lives in external stores, so any instance serves any request.

**Sizing estimate.** Assume a peak of 50,000 requests per second, and that one instance handles 10,000 per second with auth and rate limiting on (an assumption; benchmark your stack). Base need: 50,000 / 10,000 = 5 instances. To survive losing one of 3 zones, run 3 per zone, 9 total. After a zone loss, 6 x 10,000 = 60,000 per second remains, which is 20% headroom over peak (60,000 / 50,000 = 1.2).

**Availability math.** Serial components multiply. A gateway at 99.99% in front of a service at 99.9% gives 0.9999 x 0.999 = 0.9989, about 99.89%. Replication is what keeps the gateway's share small. For scale, 99.9% still allows 0.001 x 8,760 hours = 8.76 hours of downtime a year.

**Other risks.** A config push reaches every route at once, so roll config out gradually. Per-route timeouts and circuit breakers keep one slow service contained so connections stay free.

<!-- DIAGRAM: Nine gateway instances across zones A, B, C behind a load balancer; zone C crossed out; remaining six instances carry 60k rps -->

---

## The Egress Gateway

An **egress gateway** is the outbound mirror: a proxy that every request leaving a private network must pass through. Network rules block direct internet access, so the proxy is the single exit.

- **Destination allowlist** - The reachable set is the approved external hosts, so even a compromised workload sends data to approved hosts alone.
- **Credential stripping** - Removes tokens, cookies and internal headers that belong inside the network.
- **Credential injection** - Real third-party secrets live in the proxy alone, which attaches the real key on the way out, so stolen workload memory holds zero reusable credentials.
- **SSRF defense** - When the system fetches user-supplied URLs (webhooks, link previews), the proxy refuses private ranges such as 10.0.0.0/8 and the 169.254.169.254 cloud metadata address.
- **Audit** - One log of every external call.

The trade-off: inspecting HTTPS bodies means the proxy decrypts them, so workloads must trust a proxy-issued certificate authority. That makes the proxy a high-value target needing the same hardening and redundancy as the inbound gateway.

<!-- DIAGRAM: Workloads in a private network -> egress gateway (allowlist, strip credentials, inject key, log) -> approved third-party API; blocked arrows to an unknown host and to the metadata address -->

---

## Summary

- **Gateway** - one front door for routing, auth, rate limits, transformation, TLS and telemetry.
- **Load balancer** spreads load; **mesh** governs service-to-service calls.
- **Availability** - stateless fleet across zones, shared counter store, gradual config rollout.
- **Egress gateway** - controls what leaves: allowlists, credential handling, SSRF blocking.

---

## Common Deep Dives (Interview Q&A)

### "Is the gateway a single point of failure?"

Logically yes; physically it is many replicas. Run a stateless fleet across three zones, size it to survive a zone loss, and roll out config gradually.

### "Where should authorization happen?"

Token and scope checks at the gateway; resource-level checks in the owning service.

### "How do you rate limit across many instances?"

Shared counters keyed by user and window. Local counters multiply the limit by the instance count.

### "How do you keep a service's secrets inside the network?"

Force outbound traffic through an egress gateway that allowlists destinations, strips or injects credentials, and logs every call.

{{SUBSCRIBE}}

{{BUTTON:Read More Articles|https://newsletter.systemdesignlaws.xyz}}
