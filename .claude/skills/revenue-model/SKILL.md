---
name: revenue-model
description: Size revenue, ROI, and client budget from measured production usage rather than assumptions. Trigger on "revenue", "pricing", "MRR", "ROI", "what should we charge", "budget for clients", "metering", "mutation tokens".
---

# Measure the meter before you price it

## Ground every figure in production

Read-only aggregate SELECTs, no PII. The billing unit here already exists: `CliUsageEvent.identifiersMutated` / `.secretsBlocked`. **The gap is billing, not measurement.**

## The checks that change the answer

1. **Is the meter wired?** Grep for consumers of the metering functions. Here, `reportUsage` / `meterForStripe` / `createCheckoutSession` / `STRIPE_PRICE_IDS` had **zero consumers outside their own tests**, and price IDs were placeholders. Overage was computed and discarded.
2. **Is usage deduplicated?** `idempotencyKey` was NULL on **100%** of events despite a unique index built for it. Billing un-deduplicated events charges customers for retries.
3. **Who is actually in the data?** One org was 99.4% of events and 100% of secrets caught — internal dogfooding. **Exclude it from revenue and from every efficacy claim.**
4. **Does the limit agree with itself?** The free cap was documented as 1,000 in three places and 10,000 in two, and the field named `/month` was enforced per 7 days. Measured against real orgs, that choice quadrupled the paying population.

## Enforcement verb

For anything in the network path: **rate limit, never refuse.** Refusal is an outage. It also dissolves a bootstrap loop — under fail-closed, the licence server is reachable only *through* the proxy asking permission to run.

## The ROI statement a client can verify

coverage % = mutated ÷ (mutated + unparsed), read from `audit.db`. Tokens consumed = secrets that would otherwise have reached a provider in plaintext. **The denominator is the product.**
