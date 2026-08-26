---
name: worktree-doctor
description: Diagnose broken git worktree registrations. Use before ever running `git worktree prune`. Trigger on "prunable", "worktree", "gitdir", "moved the folder", "worktree list shows", "cannot commit from".
---

# `prunable` does not mean abandoned

Moving a worktree folder leaves git's **admin-side** pointer (`<repo>/.git/worktrees/<n>/gitdir`) behind while the **worktree-side** `.git` file stays correct. `git worktree list` shows both cases identically. **The fixes are opposites.**

| State | Test | Fix |
|---|---|---|
| **RELOCATED** | the folder exists somewhere else and has a `.git` file | `git worktree repair <path>` — restores the link, **keeps the branch** |
| **DELETED** | the folder is genuinely gone | `git worktree prune` — but check the branch first |

## Real incident, 2026-08-22

Seven worktrees showed `prunable` after folders moved from `~/dev` to `~/dev/Product1`. `prune` would have severed **five branches with unmerged work**. `git worktree repair` fixed all seven, non-destructively.

Precedent in the same repo: `docs/TAG_PRUNE_RECOVERY_2026-08-21.txt` is the recovery ledger for 91 release tags a prune destroyed the day before.

## Before any prune

1. Read the admin `gitdir`; if the path is missing, **search for the folder by name** before concluding it is gone.
2. If genuinely gone, read `<repo>/.git/worktrees/<n>/HEAD` for the branch and check `git branch --merged origin/main`.
3. Note: pruning removes only the **registration**. The branch ref survives — verify that rather than assuming it.

## Also

A repo with `core.bare=true` and a populated working tree cannot `git status` or commit. That is usually a bare-repo-plus-worktrees layout, not corruption — commit from a worktree, or unset `core.bare`.
