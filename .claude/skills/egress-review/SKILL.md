---
name: egress-review
description: Review any change touching the proxy egress path, the mutator, the scanner, or config that reaches egress. P0, outweighs all other concerns. Trigger on "review this diff", "egress", "mutation", "proxy change", "scanner", before merging anything in apps/proxy or packages/mutator.
---

# Mutation integrity outranks everything

`mutation.md`: at egress, secrets/PII are **ALWAYS reversibly MUTATED** — tokenised out, byte-exactly reversed back in. Never one-way redacted, never passed through raw. "Redaction" is a legacy label; reason in **mutation** terms.

## Lead every review with `## MUTATION`. BLOCK on any of:

1. A detected secret reaching upstream un-mutated (bypass, detector gap, egress mode off)
2. Round-trip not byte-exact — lost/rotated salt, token collision, unreversible map
3. Reversible mutation becoming one-way redaction or pass-through
4. **A new content type / route / encoding that skips the mutation path**
5. A new egress detector not flowing through the reversible path

## Never approve on unit tests alone

Require an explicit round-trip assertion (`mutate → egress → reverse` restores exact bytes) **plus non-vacuity**: `tests/live/mutation-gate.sh` asserts every class three ways — RECALL (detector names it), MUTATION (raw value gone from bytes), REVERSAL (byte-exact) — because a round trip alone is a false-green generator. If a detector stops firing, mutate is a no-op, reverse is a no-op, and `diff` reports no difference. **Green, on a run where a live secret reached the provider.**

## Known coverage holes — check whether the diff widens or narrows them

Non-POST returns before any scan and drops the body · non-JSON POST hard-400s · non-JSON responses have their body discarded · no multipart, no WebSocket, no request decompression · identifier mutation fires only inside ```-fenced blocks · two tree walkers disagree on depth · the residual egress gate is local-egress only.

## Config counts as egress

A malformed `pretense.yaml` used to fall back to DEFAULTS, which carries `airgap.enabled:false` — silently routing an air-gapped deployment to a hosted provider. Config that reaches egress is egress.
