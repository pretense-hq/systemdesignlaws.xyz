---
name: regulatory-citation-discipline
description: Never write a point value, criterion number, or eligibility verdict without checking the primary source. Use when producing a gap register, SPRS score, POA&M, or any document citing a regulation. Trigger on "POA&M", "SPRS score", "CMMC", "NIST 800-171", "how many points", "is it POA&M eligible", "32 CFR 170", "gap register", "which control number".
---

# A fabricated point value can invert the answer

Not "introduce an error" — **invert**. The wrong number produced the opposite eligibility verdict,
in a document destined for an assessor.

## The incident

A gap register carried this row:

```
3.1.4 | 5 points | POA&M-eligible: No
```
Both numbers were wrong, and the second was wrong *because* the first was:

| Field | Written | Primary source |
|---|---|---|
| Point value for 3.1.4 | **5** | **1** — DoD Assessment Methodology v1.2.1 |
| POA&M eligible | **No** | **Yes** — 32 CFR 170.21(a)(2)(ii) makes 1-pointers eligible |

Under the methodology, 5-point and 3-point requirements are largely barred from deferral;
**1-pointers are eligible**. Inflating 1 → 5 flipped a deferrable gap into a hard blocker. A
founder reading that register would have concluded they could not certify, and spent weeks
remediating something they were entitled to schedule.

The failure was not analysis. It was writing a number from memory into a table because the table
had a column for it.

## The cheapest detector — reconcile against a total the document already states

The same document stated its own score: **0.65**. That number only reconciles with **1 point** for
3.1.4, not 5. The document contained its own contradiction, and nothing compared the two.

**Any document with per-item values and an aggregate carries a free check.** Sum the parts; they
must equal the stated whole. This is `decisions.md` §4 applied to arithmetic — two sources
claiming the same fact, so make one derive from the other or assert they agree.

```python
assert abs(sum(rows["points"]) - STATED_TOTAL) < 1e-9, \
    f"per-row points sum to {sum(rows['points'])}, document states {STATED_TOTAL}"
```
Run it before anyone reads the register. It costs one line and would have caught this.

## Rules

1. **No point value, criterion number, or eligibility verdict from memory.** Cite the primary
   source in the row itself — methodology version and CFR paragraph, not "per CMMC".
2. **Version-pin the methodology.** *DoD Assessment Methodology* **v1.2.1**. Point values have
   changed between revisions; an uncited number is unauditable.
3. **Cite the paragraph that decides, not the part.** `32 CFR 170.21(a)(2)(ii)` — the subsection
   is the whole content of the claim.
4. **State eligibility as a derivation, not a fact.** `1 pt -> eligible per 170.21(a)(2)(ii)`. A
   bare `Yes`/`No` hides the reasoning and cannot be checked.
5. **Reconcile against every total the document states.**

## The six requirements barred from POA&M deferral — 32 CFR 170.21(a)(2)(iii)

Carry this list; it is small, fixed, and it is the exception that overrides the point-value rule.
These **cannot** be deferred regardless of score:

| # | Requirement |
|---|---|
| 3.1.20 | External connections (limit connection to and use of external systems) |
| 3.1.22 | Control public information (control CUI posted or processed on publicly accessible systems) |
| 3.5.3 | Multifactor authentication |
| 3.13.11 | FIPS-validated cryptography (employ FIPS-validated crypto to protect CUI) |
| 3.13.16 | Protect CUI at rest (confidentiality of CUI at rest) |
| 3.14.6 | Monitor communications for attacks |

Check membership in this list **before** applying the point-value rule — it is a hard override, and
a 1-point requirement inside it is still not deferrable.

## The `§` trap

Verify how your citation is **served**, not how you typed it. A platform's text extraction rendered
every `§` as `$`, so `§170.21(a)(2)(iii)` reached the assessor as `$170.21(a)(2)(iii)` — an
unresolvable string. Write `32 CFR 170.21(a)(2)(iii)` and avoid depending on the glyph. See
[[platform-evaluator-as-witness]].

## Pre-publication checklist

- [ ] Every point value traced to DoD Assessment Methodology v1.2.1, cited in-row.
- [ ] Every eligibility verdict written as a derivation with its CFR paragraph.
- [ ] Membership in the 170.21(a)(2)(iii) six checked before anything else.
- [ ] Per-row values reconcile with every total the document states.
- [ ] Citations survive the platform's text extraction (no bare `§` dependency).
- [ ] `decisions.md` §6: before declaring a gap a blocker, name the boring explanation — most often
      the number is wrong, not the posture.

## Self-test
Seed the exact defect this skill describes into a fixture, confirm the check reports it,
then remove the check and confirm the fixture now passes. A check never seen to fail is
not evidence.
