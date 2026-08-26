---
name: parallel-investigation
description: Fan out independent read-only investigations at the same time, and grade every claim before depending on it. Trigger on "investigate", "audit", "find out", "check whether", "look into", "why is", or any question with two or more independent sub-questions.
---

# Independent questions are asked at the same time

Sequential investigation is a choice, and usually the wrong one. A secret scan, a duplicate
trace, and a dependency check are three agents in one round trip, not three turns.

## Fan out when the sub-questions do not depend on each other

Give each agent a **distinct surface** so two never read the same files, and ask each for the
conclusion plus the command that produced it — not file dumps.

**Stay sequential** when the second question's *shape* depends on the first's answer: you cannot
scope a migration before you know which schema is live. **Never parallelize writes** to one tree.

## Grade every claim before depending on it

| Grade | Meaning |
|---|---|
| **MEASURED** | a command produced it; the command is quoted |
| **INFERRED** | reasoned from a name, a size, a timestamp, a commit subject |
| **UNVERIFIED** | no obtainable evidence |

**UNVERIFIED is never PASS.** An item that cannot be evidenced has not been checked, and
recording it as passed is how a false green enters a report.

Resolve every INFERRED claim the plan *depends on* **before** the step that depends on it. In one
audit, four inferred claims were checked in twenty minutes: two were wrong, and one of those
would have deleted a live hardening.

## Rule out the boring explanation before declaring a defect

Name the dullest cause that produces this exact output and disprove it with one command. Real
examples, all initially reported as defects, all wrong:

- 19 files matched a live-credential regex — 13 opened with `# SYNTHETIC … NOT REAL`
- a value "differed" from the vault — a trailing newline on one side of the hash
- an un-reversed token in output — a small model that did not echo it verbatim

The same discipline catches a missed bug *and* stops an invented one.

## Retract in writing, with the root cause

A retracted finding that leaves no trace gets re-raised next quarter. Keep the wrong claim, the
correction, **and** the reason it was wrong ("I grepped rendered HTML instead of opening the
source"). That last line is the part that prevents recurrence.

## Plan before executing
State the approach, the losing option, and why it lost. A decision recorded only in chat will be
re-litigated.

## Self-test
Give it a question with two independent halves and one dependent half. It must parallelize the
two, sequence the third, and grade each result — refusing to mark PASS anything it could not
evidence.
