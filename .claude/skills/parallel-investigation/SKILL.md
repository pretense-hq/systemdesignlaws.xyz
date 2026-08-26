---
name: parallel-investigation
description: Fan out independent read-only investigations at the same time, grade every claim before depending on it, and delegate writes only behind isolation. Trigger on "investigate", "audit", "find out", "check whether", "look into", "why is", "delegate", "spawn agents", "in parallel", "subagent", "second opinion", or any question with two or more independent sub-questions.
---

# Independent questions are asked at the same time

Sequential investigation is a choice, and usually the wrong one. A secret scan, a duplicate
trace, and a dependency check are three agents in one round trip, not three turns.

The golden rule: **a delegating agent owns the result, not the transcript.** You spawn an agent
to do the reading, and you keep its one-paragraph conclusion — never the file dumps.

## Delegate only when breadth, confidence, or scale earns it

Delegation has setup cost. Spend it deliberately.

| Situation | Do it yourself | Delegate |
|---|---|---|
| Known file, single fact | read it | no — this is the most common waste |
| "Where/how is X done across the codebase?" | no | fan out read-only explorers |
| Designing a non-trivial change | no | planning agents |
| Confirming your own fix is correct | risky alone | an adversarial probe |
| Many independent **edits** | serial and slow | one isolated worktree per unit |

## Fan out when the sub-questions do not depend on each other

Give each agent a **distinct surface** so two never read the same files, and ask each for the
conclusion plus the command that produced it. Two agents told to "look at the parser" do the
same work twice; partition the search space explicitly.

Worked example — before adding a new case to a classifier, three explorers ran at once: one
mapped the existing cases by group, one traced the exact set of places a new case must be
registered (pattern table, call site, fixture data, and the benign look-alike that keeps it
from over-matching), one confirmed the invariant the change must not break. The plan was
written from three conclusions instead of from re-reading the whole package. **The reusable
part: find out how many places a new entity must be registered in *before* you register it in
the first one.**

**Stay sequential** when the second question's *shape* depends on the first's answer: you cannot
scope a migration before you know which schema is live.

## Parallel writes need isolation, not care

**Never parallelize writes into one tree.** Two agents editing the same working copy corrupt
each other's edits, and the damage looks like a bad merge rather than a process error.

When several edits are genuinely independent, give each agent its **own worktree** so they
cannot collide. The precondition is real independence: no shared state and no "must land first"
ordering. If one unit must merge before another, that is a sequence, not a fan-out. Worktrees
cost setup time and disk, so use them only when agents actually write — for read-only fan-out
they are pure overhead.

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

## The finder is the worst judge of the finding

Agents are confident even when wrong, so **never act on an unverified finding** — confirm it
against the code before you edit. Structurally: keep the agent that *finds* separate from the
agent that *checks*.

A review built this way runs independent finders, each on one angle (correctness, collisions,
fake-looking values, taxonomy), then an independent verifier adversarially re-checks every
candidate before it is reported, marking each **CONFIRMED** or **PLAUSIBLE**. Separating the
roles is the point: whoever found a bug is invested in it being real.

After a risky fix, spawn one agent whose entire job is to **refute** it — feed it hostile inputs
and ask "show me where this still fails." One such probe confirmed a set of separator fixes and
surfaced a remaining gap as a documented known limitation instead of a silent one.

**Prefer diverse skeptics over redundant confirmers.** Five agents asked "is this right?" mostly
agree with each other. One asked "prove this is wrong" earns its cost.

## Rule out the boring explanation before declaring a defect

Name the dullest cause that produces this exact output and disprove it with one command. Real
examples, all initially reported as defects, all wrong:

- 19 files matched a live-credential regex — 13 opened with `# SYNTHETIC … NOT REAL`
- a value "differed" from the vault — a trailing newline on one side of the hash
- an un-reversed token in output — a small model that did not echo it verbatim

The same discipline catches a missed bug *and* stops an invented one.

## Reuse an agent's context, or discard it on purpose

A fresh agent starts blank. To continue work an agent already has context for, send it a
follow-up rather than re-spawning and re-explaining. Re-brief a *new* agent only when you
want an unbiased perspective — a second-opinion reviewer must not inherit the first one's
assumptions. Both are correct; choose which one you want and say why.

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
evidence. Then hand it a single known-file lookup: it must answer directly rather than delegate.
