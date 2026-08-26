---
name: approval-matrix
description: Route a change to the right approvers and record their sign-off. Use before a release, a pricing change, a public claim, a schema migration, or anything externally visible. Trigger on "who approves", "sign-off", "approval", "can we ship", "release checklist", "stakeholder".
---

# Eleven approvers, each with one question and one piece of evidence

An approval without evidence is a signature on nothing. Each role below blocks on **one** question and accepts **one** artefact. If the artefact does not exist, the answer is "not yet", not "probably fine".

| # | Role | Blocks on | Evidence that satisfies it |
|---|---|---|---|
| 1 | **Product** | Does this move a stated metric? | The metric named *before* the build, measured after |
| 2 | **Engineering** | Is it correct, and proven correct? | Local gate green + a false-green proof (delete it, see red) |
| 3 | **Security** | Can a secret reach a provider un-mutated? | A byte-exact round-trip assertion with non-vacuity |
| 4 | **Compliance** | Does this change SOC2/ISO/CMMC posture? | The failing-test delta, and which are overdue |
| 5 | **Legal** | Consent, DPA, works council, wiretap? | Written review for anything capturing user traffic |
| 6 | **Finance / FinOps** | What does this cost us per unit? | Build minutes, storage, egress — measured, not estimated |
| 7 | **Revenue / Sales** | Can a customer actually buy it? | A completed checkout in test mode |
| 8 | **Marketing** | Is every public claim true today? | Each claim traced to a command that verifies it |
| 9 | **Support** | Can we diagnose this at 3am? | A runbook with the exact commands |
| 10 | **Data** | Is the migration reversible and tenant-scoped? | Forward-compatible migration + a row count of who fails the new gate |
| 11 | **SRE / Release** | Can we take it back in 60 seconds? | A rollback command **tested in CI**, not documented |

## Deterministic routing

- Externally visible **and** not derivable → the owning role decides, and you record it.
- Touching egress / entitlement / data-loss → **3, 4 and 11 are mandatory**, no exceptions.
- A public claim → **8**, always. "Marketing said it" is not evidence; a passing check is.
- Pricing → **1, 6, 7**. Entitlement and pricing are different questions; keep one field doing one job.

## The anti-pattern

Collecting eleven signatures on a change nobody verified. **Evidence first, signatures second.** If you cannot produce the artefact, name that as the blocker instead of asking for an approval that would be uninformed.
