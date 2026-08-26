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
git check-ignore -v .claude/worktrees/   # must MATCH -- note the trailing slash
git check-ignore -v .claude/skills       # must NOT match (exit 1)
```

### `check-ignore` answers about a path, not about a rule

A directory-only pattern reports **NO MATCH when the directory does not exist** — so a
correctly-guarded repo and one carrying no rule at all return the identical exit 1. Measured
across eight repos: three had no rule whatsoever, and the verification pass reported PASS.

Query a path the pattern can actually match — a **trailing slash**, or anything inside it —
rather than the bare directory name. Verified on git 2.53.0, rule `.claude/worktrees/` present:

| query | directory absent | directory present |
|---|---|---|
| `.claude/worktrees` | **exit 1 — the false green** | exit 0 |
| `.claude/worktrees/` | exit 0 | exit 0 |
| `.claude/worktrees/.probe` | exit 0 | exit 0 |

`--no-index` does **not** fix this; it still exits 1.

### Two more traps — and the direction of your assertion decides the query

There are **three** traps, and each fix is blind to the others. Which ones bite you depends on
whether you are asserting a path *must* be ignored or *must not* be.

| # | Trap | Symptom | Fix |
|---|---|---|---|
| a | directory **absent** | plain exits 1 → false **green** | trailing slash |
| b | path is **tracked** | plain exits 1 *regardless of a matching rule* → false **green** | `--no-index` |
| c | `.gitignore` is **CRLF** | a lone `\r` is a one-char pattern, and `--no-index` + a trailing-slash **directory** query spuriously matches it → false **red** | query a real **file** path |

So the two directions need different queries, and using one for both leaves a check that cannot fail:

```bash
# "must be ignored"  (dir often absent -> trap a):
git check-ignore -q '.claude/worktrees/'                    # trailing slash, no --no-index

# "must NOT be ignored" (files are tracked -> traps b and c):
probe=$(git ls-files '.claude/skills/*/SKILL.md' | head -1)
[ -n "$probe" ] && git check-ignore -q --no-index "$probe"  # real FILE path
```

**Measured, 2026-08-26.** A release gate asserted *".claude/skills is ignored in 0 repos"* and
exited 0 **with a real `.claude/skills/` rule planted** — trap (b), vacuous for as long as the
files stayed tracked. Adding `--no-index` exposed it, and immediately produced a false red in
4 of 8 repos whose `.gitignore` is CRLF throughout — trap (c). Only the real-file query is
right in both directions.

**No tracked file means no assertion.** If `ls-files` returns nothing there is nothing to test;
report UNVERIFIED, never PASS.

**Both arms, every time.** Plant a genuine rule and confirm the check fails naming *only* the
repo you planted it in; then remove it and confirm it passes. A check that has only ever been
seen green is not evidence — and the false red is as informative as the false green, because it
tells you the query is matching something other than what you meant. Creating a throwaway directory first also
works, but needs no cleanup if you just add the slash. Then run the control: in a repo with no
such rule the trailing-slash form must **still** exit 1, or you have only made the check
unfalsifiable. When the question is really *"is the rule present"*, read the rule:
`grep -n worktrees .gitignore` — no output means NO RULE, which is a different answer from
*unmatched*.

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

## Identity is per-repo, and a stale one is invisible

`user.email` resolves per repository, and a local value silently overrides the global one.
Measured in an eight-repo workspace: one repo carried a test-fixture identity
(`user.name=task797 <test@example.com>`) while seven siblings were correct — two commits landed
attributed to the fixture. Nothing warns. The commit succeeds and reads as ordinary.

```bash
for d in */.git; do r=${d%/.git}; printf '%-24s %s <%s>\n' "$r" \
  "$(git -C "$r" config user.name)" "$(git -C "$r" config user.email)"; done
```
Run it **before** the first commit in each repo. Correcting authorship afterwards means
rewriting history, which this skill refuses — so this is the only cheap moment to catch it.

## Refuses to do silently
Prune a worktree on one half of the check · delete a file a service still reads · rewrite
history · commit a file it has not opened.

## Self-test
Point it at a fixture containing a nested `.git` worktree and a fake live-shaped key. It must
refuse both. Delete its guards and re-run: it must now fail. A check that cannot fail is not
evidence.
