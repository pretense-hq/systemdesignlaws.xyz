---
name: stale-sweep
description: Sweep a multi-repo workspace for staleness — sync state, dirty trees, stale branches, broken worktrees, release drift, PR backlog. Trigger on "stale", "clean up", "workspace health", "how many branches", "are we in sync".
---

# Report staleness; never fix it silently

Run `scripts/stale-audit.sh` (read-only, exits 0 clean / 1 stale / 2 blocking). It prints the fix command rather than running it, because every "cleanup" here has a destructive twin: prune vs repair, `git add -A` vs a 59MB `node_modules`, branch delete vs unmerged work.

## What it checks

Repo sync (ahead/behind/dirty, detached HEAD, off-main checkouts) · stale branches by commit age · **relocated vs deleted worktrees** · release integrity (npm/CDN/tags/signatures) · open PR backlog.

## Judgement calls it deliberately leaves to a human

- **Off-main checkouts** are usually intentional (release branches, dep sweeps). Flag, don't fix.
- **A diverged repo** may hold the only copy of something. `pull --rebase` only when nothing tracked is modified, and abort cleanly on conflict rather than leaving a half-rebase.
- **Untracked scratch** is not dirt if it is regenerated output — gitignore it instead of deleting it.

## The failure this tool itself had

Its first version recommended `prune` for relocated worktrees, which would have destroyed five branches. Recommending a destructive command for a non-destructive problem is a defect in the tool, not a judgement call for the reader.

## The sweep must prove it iterated

A loop that ran once is indistinguishable from a loop that ran N times: it exits 0 and prints a
plausible line. Observed: `for r in $REPOS` under **zsh** ran a single iteration with the whole
list as one word, creating a directory whose name was all eight repo names concatenated. zsh
does not word-split an unquoted parameter; bash does — so a loop copied from bash silently
degrades to one iteration, and the sweep reports on one repo while claiming the workspace.

```bash
repos=(${=REPOS})            # zsh: explicit split.  bash: repos=($REPOS)
(( ${#repos[@]} == EXPECTED )) || { echo "swept ${#repos[@]}, expected EXPECTED"; exit 2; }
```
Count what you examined and compare it with what you meant to examine. *Silence is never
success*: a sweep that reports clean after looking at one item is the same defect as one that
looked at none.

## Self-test
Point it at a workspace holding a relocated worktree: it must say **repair** and never `prune`.
Then remove one repo from the list it is given: it must fail the iteration count rather than
report clean on the remainder.
