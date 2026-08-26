---
name: rescue-orphaned-refs
description: Rescue commits whose upstream repository no longer exists, before a routine cleanup destroys them. Five workarounds ranked by whether they actually get the work off-machine. Trigger on "Repository not found", "dead remote", "remote is gone", "commits only exist locally", "git fetch --all fails", "remove the old remote", "archive these branches".
portable: true
---


**The situation.** A remote is unreachable (`Repository not found`) but its *tracking refs*
still hold commits that exist nowhere else. Here: 23 commits across 5 branches, ~2 years of
work, last copy on one laptop.

**The two traps that make this urgent, and quiet.**
1. *Tracking refs are not a backup.* `git remote remove <dead>` deletes them. The obvious
   "clean up the dead remote" tidy-up is the thing that destroys the work — the same shape as
   `git worktree prune` on a `prunable` entry.
2. *`git fetch --all` exits 1 on the dead remote*, so any gate that fetches looks broken, which
   pressures someone into removing it. Fix the symptom at the most reversible layer instead:
   `git config remote.<name>.skipFetchAll true` (one line, `--unset` reverts, deletes nothing).

## Diagnose first: is it gone, or can't you see it?

```bash
gh repo view <owner>/<repo>          # "Could not resolve to a Repository" = gone
gh repo view <owner>/<a-known-private-repo>   # CONTROL: proves the token can see private repos
```
Without the control arm you cannot tell *deleted* from *no permission* — and the fixes differ.

## The ladder

| # | Workaround | Gets it off-machine? | Verdict |
|---|---|---|---|
| W1 | **Local tags** at each tracking-ref SHA | no | ✅ do first — zero cost, survives `remote remove` |
| W2 | **`git bundle create … --all`** | portable, not yet off-machine | ✅ do second — one verifiable file |
| W3 | Push branches to a live remote | yes | ⚠️ may be blocked (see below) |
| W4 | Rewrite history to remove the blocker | yes | ❌ changes every SHA — destroys the artifact's identity |
| W5 | Widen the token scope, then W3 | yes | ✅ the real fix; needs the human |

**W1 and W2 cost nothing and remove the "one careless command" risk immediately. Do them before
diagnosing anything else.**

```bash
git tag -f "archive/<remote>/<branch>" "$(git rev-parse refs/remotes/<remote>/<branch>)"
git bundle create ~/archive-$(date +%F).bundle --all
git bundle verify ~/archive-$(date +%F).bundle
git clone --bare ~/archive-*.bundle /tmp/t && git -C /tmp/t tag -l   # PROVE it restores
```
**Verify the bundle by restoring it, not by its exit code.** `git bundle verify` printing a hash
algorithm is not a restore test.

## Before you conclude a scope block needs a human: check the TRANSPORT

**Check the remote's TRANSPORT before concluding a scope block needs a human.**

    git remote -v            # https:// or git@ ?
    ssh -T git@github.com    # already authenticated?

Measured 2026-08-26: a push was rejected with *"refusing to allow an **OAuth App**
to create or update workflow `.github/workflows/test.yml` without `workflow` scope"*
and this was reported as human-only ("run `gh auth refresh -s workflow`").

**It was not.** The restriction is a property of the **OAuth App auth path**, not the
repo, the ref type, or the tree. The blocked repo was the only one of 8 still on an
**HTTPS** remote; its 7 siblings were already on `git@github.com:`. SSH authenticates by
key, is not an OAuth App, and is not subject to the check. Pushing over SSH succeeded on
the first attempt — no scope change, no browser auth, no history rewrite, every SHA
preserved (the offending `test.yml` is present in the pushed tree).

**Read the error's subject noun.** "refusing to allow an *OAuth App*" names the actor,
not the resource — that is the clue that a different auth path is unaffected.

`--dry-run` cannot test this: the check fires in the server's pre-receive hook, which a
dry run never reaches. Push for real, or you have proved nothing.

## When W3 is blocked: GitHub workflow scope

```
! [remote rejected] … refusing to allow an OAuth App to create or update workflow
  `.github/workflows/*.yml` without `workflow` scope
```
It applies to **any ref whose tree contains a workflow file** — measured: **tags do not bypass
it** either. It is not about the branch name or ref type.

The fix is a scope widening the human runs, because it is a browser auth flow:
```bash
gh auth refresh -h github.com -s workflow
```
**Do not "solve" this by stripping the workflow file.** That is W4: it rewrites every SHA, so the
pushed branches no longer correspond to the refs you were rescuing.

## Shell traps that hid all of this

- **zsh eats `$var:`** — `"$br:refs/heads/$dest"` parses `$br:r` as the `:r` *root modifier*,
  yielding `…mainefs/heads/…`. Always brace: `"${br}:refs/heads/${dest}"`. bash does not do this;
  zsh is the macOS default.
- **Piping hides the failure.** All six pushes errored, but `… | grep | head` made the loop exit
  0 and the runner report success.
- **Verify the end state with a different command than the one that did the work.**
  `git ls-remote --heads origin '<pattern>'` asked the remote directly and returned nothing, and
  the unbacked count stayed at 23 — which is how both failures were caught.
