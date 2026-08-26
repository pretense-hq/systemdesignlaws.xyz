---
name: commit-by-default
description: Put every file, folder and piece of work under version control — safely. Triage what to commit, what to ignore, what is superseded, and what must never be pushed. Trigger on "push everything", "commit all", "cleanup", "add -A", "back up my work", "is this in git", "nothing is in git".
---

# Disk is not a backup — and `git add -A` is not the answer, it is the accident

Uncommitted work is one laptop from gone. But the naive fix is worse than the problem: a single
`add -A` has, in real workspaces, staged 24 GB of nested worktrees, a live bearer token, and
6.4 GB of chat history. Commit everything **through a triage**, never in one sweep.

## Every untracked path is exactly one of four things

| Bucket | Test | Action |
|---|---|---|
| **WORK** | unique, authored, no live secret | commit |
| **IGNORE** | regenerated, huge, or contains a nested `.git` | gitignore rule; keep on disk |
| **SUPERSEDED** | a fuller or newer copy already exists in a repo | drop — never an N+1 source of truth |
| **NEVER** | live credential, PII, or a deleted-upstream branch | leave local; say why in the PR |

Misfiling into WORK is the expensive direction. When unsure, IGNORE — it is reversible.

## The seven steps

1. **Survey, after fetching.** Per repo: branch, remote, upstream, ahead/behind,
   `status --porcelain -uall`. A stale `origin/*` lies — it has shown "0 behind" on a branch
   that was two commits behind and one whose upstream had been **deleted**.
2. **Classify untracked before staging anything.** `du -sh` every untracked directory and look
   for a `.git` *file* inside it. This is the step that catches nested worktrees, and it is the
   step people skip.
3. **Trace duplicates.** `find -name <basename>` across sibling repos, then `cmp`. "Already in
   git" is a reason to drop, not to commit a second copy.
4. **Decide supersession by size and mtime, not by filename.** The local copy is often the
   *older* fork. Diff the two and list what exists only in the one you plan to delete — a single
   unique function can be a hardening you are about to throw away.
5. **Secret-scan, then verify every hit by opening the file.** Shape is not proof, and a name is
   not proof. Classify by **value**: `API_KEY=""` is a config template. Files whose first line
   says `# SYNTHETIC … NOT REAL` are test fixtures — deleting them breaks a benchmark.
6. **Push in dependency order.** Gitignore-fix commits go **first**; they are the guard that
   protects every later add. An unpushed commit that hardens `.gitignore` is the highest-value
   thing in the repo.
7. **Verify, then report what you skipped** — explicitly, in the PR body.

## Ignore rules must be exact, never blanket

`.claude/worktrees/` — **not** `.claude/`. The blanket form also swallows `.claude/skills/`,
which is where the release process lives. Prove it both ways after writing the rule:

```bash
git check-ignore -v .claude/worktrees   # must MATCH
git check-ignore -v .claude/skills      # must NOT match (exit 1)
```

## A worktree cannot be committed into its own repo

It is a checkout of the same repository — committing it nests the repo inside itself. **The work
is the branch, not the directory.** Ask only: is that branch on a remote?

```bash
git worktree list --porcelain | awk '/^branch /{print $2}' | while read b; do
  git branch -r --contains "$(git rev-parse "${b#refs/heads/}")" >/dev/null || echo "UNPUSHED: $b"
done
```
Push the unpushed ones and gitignore the directories. Moving gigabytes achieves nothing this
does not.

## `prunable` never means "safe to prune"

Check **both** halves: the directory is genuinely gone **and** the commit is on a remote. A
relocated worktree also reports `prunable`, and pruning it has severed live branches.

## Refuses to do silently
Prune a worktree on one half of the check · delete a file a service still reads · rewrite
history · commit a file it has not opened.

## Self-test
Point it at a fixture containing a nested `.git` worktree and a fake live-shaped key. It must
refuse both. Delete its guards and re-run: it must now fail. A check that cannot fail is not
evidence.
