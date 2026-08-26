---
name: learning-to-skill
description: Turn a lesson learned into a durable skill, memory, or ticket entry — once, in one place. Trigger on "we learned", "that was surprising", "next time", "capture this", "add to memory", "why did that happen", or any moment a belief changed.
---

# A lesson learned twice was never captured

## Trigger
Any moment a belief changed: a false alarm disproved, a near-miss caught, a correction from a
human, or the **second** time the same manual reasoning is performed.

## The capture test — all three must hold

- **Non-obvious** — a careful engineer could have got it wrong.
- **Durable** — still true next month, not just on this branch.
- **Actionable** — it changes a decision, not merely interesting.

Fails any one? Do not write it. A library of trivia is a library nobody reads.

## One home per fact

| Kind | Home |
|---|---|
| Reusable procedure | a skill |
| Fact about this system | memory |
| Relevant to one ticket only | the ticket |

Never all three. Two places claiming one fact is the N+1 source of truth that goes stale
silently.

## Record the failure, not just the rule

The rule alone is forgettable; the failure is what makes it stick. Write what was believed, what
was actually true, and **the reason the wrong belief was plausible**. Prefer:

> *`prunable` does not mean deletable — a relocated worktree reports it too, and pruning one
> severed five branches. Check both halves: directory gone AND commit on a remote.*

over "be careful with worktrees".

## Check before writing

Search existing skills and memory first. If it is already captured, **update that entry** rather
than adding a near-duplicate — and if the existing one is now wrong, correct it and say so.
A stale memory that names the wrong file as authoritative is worse than none: it is trusted.

## Where a skill lives

In the repo, version-controlled with the code it governs. A skill in an untracked home is a
skill with no backup and no review. If copies exist in several repos, designate one canonical
and add a check that asserts they agree.

## Self-test
Feed it an obvious restatement of an existing skill: it must decline to create a duplicate and
point at the existing home. Feed it a fact true only for today's branch: it must decline as
not durable.
