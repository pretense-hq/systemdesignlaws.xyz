---
name: auto-merge-gated
description: Merge pull requests automatically, gated on evidence that actually ran rather than on a CI badge. Trigger on "auto merge", "merge the PRs", "ship it", "can this merge", "enable auto-merge", "merge when green".
---

# Gate the merge on the thing that actually runs

Where CI is dead or absent, a green tick is **not a weak signal — it is noise shaped like a
signal**, and keying a merge to it is a false green with a merge button.

## Establish what the signals mean before trusting one

```bash
gh run list --limit 10 --json conclusion,name     # all startup_failure => nothing ran
gh api repos/<org>/<repo>/branches/main/protection  # 403/404 => no required checks at all
```
On a plan without branch protection, `gh pr merge --auto` waits for required checks, finds none,
and **merges instantly on no evidence**. The permission was never the constraint; there is no
constraint. That is exactly why the gate must be self-imposed.

## Merge only when all four hold

1. The **local gate** (or whatever check genuinely executes) exits 0 for that repo.
2. The diff touches **no excluded path**.
3. The branch is not behind its base — the diff is what was reviewed.
4. Post-merge verification is defined **before** merging, including how to undo it.

## Never auto-merges — routes to a human

- Egress, mutation, or scanner paths — a defect there is always a block
- Licence, entitlement, or signed-claim verification
- **Database migrations** — a failed migration aborts every later deploy, rollback included
- Anything removing a capability an existing paying customer has today
- Credential rotation — not a merge at all

Everything else is ordinary work and should merge without ceremony. A gate that blocks
everything gets switched off; a gate that says yes to safe work survives.

## Merged is not deployed

Verify the **artifact**, not the merge. A build can report Ready with an **empty alias list** —
git, PR, and build all saying shipped while production serves something hours old. Backends that
deploy manually deploy *nothing* on merge. Probe the running thing for the commit sha.

## Prove the gate can fail

Before trusting a green run, break one item deliberately and confirm non-zero. A gate never seen
to fail is not a gate. A skipped check reports SKIP and **still fails** in release mode — you
cannot ship on checks that did not run.

## Self-test
A PR touching a migration and a PR with a red local gate: it must refuse both. A PR with a green
GitHub check and no local evidence: it must refuse that too.
