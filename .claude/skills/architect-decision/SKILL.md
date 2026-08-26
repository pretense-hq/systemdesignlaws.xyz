---
name: architect-decision
description: Make a determinate architectural call and record the losing option. Use when two or more designs are viable, when someone asks "should we X or Y", or before any change to egress, entitlement, pricing, or a data-loss path. Trigger on "which approach", "design decision", "should we", "trade-off", "architecture".
---

# Architect a decision, don't survey options

`decisions.md` rule 0: **a question with one defensible answer is not a decision; it is a lookup you have not done yet.** Do the lookup before asking anyone.

## The procedure

1. **Apply the escalation test.** Escalate only when BOTH: irreversible/externally-visible AND not derivable from a stated goal, rule, or the codebase. Only (1) → propose action + rollback, then act. Only (2) → pick what serves the stated goal, write down the loser, proceed. Neither → just decide, silently.
2. **Enforce at the most reversible layer that achieves the goal.** `sales/checkout/config` > `application logic` > `signed claim/fail-closed`. Push lower only when a customer could bypass the higher layer to their own gain.
3. **Write the losing option down, in the code**, not just the ticket. Worked example in-repo: `start.ts` `--background` is an accepted no-op, and the comment says *why* self-daemonising would be wrong under launchd/systemd. The next reader does not re-litigate it.
4. **Derive; never add an N+1th source of truth** (rule 4). If you cannot collapse two sources in this change, add a test asserting they agree.

## Anti-patterns seen in this repo

- **Surveying instead of deciding.** "Here are three options" when the rules already pick one.
- **A pin that becomes a second source of truth.** `mutation-gate.sh` documents this against itself: a hardcoded `PINNED_VERSION` drifted from the registry silently.
- **Deciding at the least reversible layer.** A seat minimum in a signed licence refuses every solo Enterprise account; at checkout it strands nobody.

## Output

A decision, a one-line rationale naming the rule that determined it, and the losing option with why it lost. If you cannot name the rule, you are surveying, not deciding.
