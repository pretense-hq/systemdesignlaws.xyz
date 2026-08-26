---
name: user-journey
description: Map each stage of the customer journey to the technical capability that carries it, and find the stage that is actually broken. Use when prioritising, when adoption is flat, before a launch, or when deciding what to build next. Trigger on "user journey", "funnel", "onboarding", "activation", "why aren't people using", "what should we build".
portable: false
portable_reason: the 11-stage capability table maps THIS product's own commands and signals. Losing option: genericise rows 4-5 ('pretense scan'/'pretense run') -- rejected, the other nine rows are equally specific, so it would pass the grep while remaining entirely about this product.
---

# Every journey stage is a capability, and one of them is broken

Prioritise by walking the journey and asking, at each stage, **which measured signal proves this stage works.** A stage with no signal is not "fine", it is unmeasured.

## The stages, and the capability that carries each

| # | Stage | Capability | The signal that proves it works |
|---|---|---|---|
| 1 | Discover | marketing site | which Vercel project actually serves the apex domain |
| 2 | Install | `install.sh` / `install.ps1` / npm | a download that 200s on **every** advertised platform |
| 3 | Verify the install | checksum + signature | `SHA256SUMS` **and** a cosign bundle that resolves |
| 4 | First value | `pretense scan` | a detector firing on the user's own code |
| 5 | Route traffic | `pretense run` / `proxy start` | a request reaching the proxy at all |
| 6 | Run unattended | the daemon | the service actually starting under launchd/systemd |
| 7 | See protection | mutation + reversal | `secretsBlocked > 0` **for that org** |
| 8 | Hit a limit | metering | a usage row with an idempotency key |
| 9 | Pay | checkout | a completed subscription in test mode |
| 10 | Grow the team | seats / orgs | a second member on the same org |
| 11 | Prove it to an auditor | the coverage ledger | coverage % computed from `audit.db` |

## How to use it

Walk the stages **in order** and stop at the first one whose signal is absent or zero. That is the constraint. Work above it is wasted; work below it is invisible.

## What this surfaced here (2026-08-22, measured)

- **Stage 2** — the Windows binary 404'd on every download and fell back to npm silently.
- **Stage 3** — eight consecutive releases carried no signature.
- **Stage 6** — all three service units invoked a flag the CLI never declared, so **the daemon had never started on any machine**.
- **Stage 7** — **ten of eleven orgs had `secretsBlocked = 0`.** Every secret the product has ever caught belonged to one internal org.
- **Stage 8** — `idempotencyKey` NULL on 100% of 14,525 events.
- **Stage 9** — Enterprise had a published price and no working checkout.

**Stage 7 is the constraint.** A compliance product that has caught nothing for ten of eleven customers has a value-demonstration problem, and no amount of stage-8/9 billing work moves it. Fix the signal before the funnel.

## The discipline

Never infer a stage works because the code exists. Resolve the DNS, fetch the artefact, query the table. A stage is proven by a signal, not by a implementation.
