---
name: token-capability-refusal
description: What to do when a credential authenticates fine but the token's TYPE or FLAGS disqualify it from one specific operation. Five workarounds, ranked, with the failure mode of each, and how to get the provider's real error out of a CLI that swallows it. Trigger on "403 Forbidden", "forbidden by your security policy", "may not perform this action", "dist-tag rm fails", "bypass_2fa", "without `workflow` scope", "refusing to allow an OAuth App", "the token works for publish but not for X", "whoami succeeds but the write fails".
---

# A token that authenticates is not a token that is allowed

The confusing case is not a bad credential. It is a **good** credential that the provider
refuses for one operation because of how the token was minted. `whoami` succeeds, reads
succeed, some writes succeed — and one specific call returns 403.

**The tell:** authentication demonstrably works, the failure is scoped to a single verb or
endpoint, and the CLI's error text is generic boilerplate about "your security policy".

## Step 1 — get the real error. The CLI is hiding it.

Package managers wrap the provider's response in their own message and discard the body.
The debug log usually does not have it either. Call the endpoint directly:

```bash
curl -s -o /tmp/body -w "HTTP %{http_code}\n" -X DELETE \
  -H "Authorization: Bearer $TOKEN" "https://<registry>/<path>"
cat /tmp/body
```

Measured example — npm printed *"403 Forbidden ... a package version that is forbidden by
your security policy"*, which is misleading. The actual body was:

> `Granular access tokens that bypass two-factor authentication may not perform this action.`

That sentence is the whole diagnosis, and the CLI never showed it.

## Step 2 — read the refusal's SCOPE, because it decides which workarounds are possible

- **"...tokens that <property> may not perform this action"** → the token TYPE is disqualified.
  No amount of extra authentication helps. Workarounds 2 and 3 below are dead on arrival.
- **"...requires two-factor authentication"** → the SESSION is under-authenticated. Supplying
  the second factor works. Workaround 2 is the answer.
- **"...without `<name>` scope"** → the token is missing a SCOPE. The type is fine and the
  session is fully authenticated; the credential simply was never minted with this
  permission. Workaround 5, but the cheap version — a re-authorization of the *existing*
  identity, not a new credential.

Do not skip this distinction. It is the difference between a one-command fix and a
credential the user must mint.

### Measured: a scope refusal attaches to the CONTENT, not to the operation

Pushing a branch to GitHub with an OAuth token that lacks `workflow`:

> `refusing to allow an OAuth App to create or update workflow `.github/workflows/test.yml` without `workflow` scope`

The instinct is to look for a ref that side-steps the check — push a tag instead of a
branch, push a different branch, push with `--no-verify`. **Measured: tags do not bypass
it.** The check reads the *tree the ref points at*, so it fires for any ref whose content
contains a workflow file, regardless of ref type. There is no ref-shaped way around it.

Confirm the diagnosis in one command before theorising — the scope list is printed:

```bash
gh auth status                 # "Token scopes: 'gist', 'read:org', 'repo'"  ← no 'workflow'
git ls-files | grep '\.github/workflows'   # and the tree does contain one
```
Two facts, and the refusal is fully explained: the scope is absent and the content is present.

**The fix is to add the scope to the identity you already have:**

```bash
gh auth refresh -h github.com -s workflow
```
This is a browser consent flow, so it needs a human at a keyboard — but it keeps the same
account and the same token record, and it is seconds rather than a credential hand-off.

**Do not strip the workflow file to get the push through.** Removing `.github/workflows/*`
from the history rewrites every commit SHA, which destroys the identity of the very commits
being pushed — catastrophic when the reason for pushing is to *preserve* them. It also
silently deletes the repo's CI. The refusal is asking for one scope; answer that question
instead of mutating the payload.

## Step 3 — inspect the token's own flags, then look for a sibling

Most registries expose the caller's tokens. Ask, rather than assume:

```bash
curl -s -H "Authorization: Bearer $TOKEN" "https://registry.npmjs.org/-/npm/v1/tokens?perPage=100"
```

Print flags only, never values. Two facts decide everything: does THIS token carry the
disqualifying property, and does any OTHER token lack it.

## The five workarounds, ranked

**1. Use a different existing token that lacks the flag.** Free and instant when it exists.
*Failure mode:* there is only one token. Enumerate before assuming — on 2026-08-23 the
account had exactly one, `bypass_2fa: True`, so this died immediately. One command tells you.

**2. Supply the second factor inline (`--otp=<code>`).** *Failure mode:* useless when the
refusal is type-level (Step 2). The token is rejected before the OTP is considered, so this
looks like "the OTP is wrong" and sends you debugging the wrong thing.

**3. Do it in the provider's web UI.** *Failure mode:* the surface may not exist. npm has no
dist-tag management page at all, so no amount of browser automation reaches it. **Check that
the UI exposes the operation before opening a browser** — this is where hours get lost.

**4. Reach the goal by a non-destructive equivalent.** Sometimes "delete" is not required —
repointing, superseding, or documenting achieves the intent. *Failure mode:* when the
requirement is genuinely ABSENCE (a tag must not exist), no amount of repointing satisfies it.
Be honest about which you are facing instead of shipping a near-miss.

**5. Mint a new credential without the flag — or re-authorize the existing one.** The one that
actually works. Requires a human, so make it a **single precise ask**: the exact setting to
change, the exact scope needed, and the exact place to store the result. A vague "please make a
new token" costs another round trip. *Prefer re-authorization when the provider offers it*
(`gh auth refresh -h github.com -s <scope>`): same identity, same stored token, nothing to
copy, and no second credential to rotate later. Minting is the fallback, not the default.

## Never route around a blocked delete with something destructive

If `dist-tag rm` is refused, `unpublish` is not the fallback — it removes versions users
depend on. A blocked destructive operation is often the platform protecting you. Treat the
refusal as information, escalate the credential, and leave the artifact alone.

The same trap wears a second face: when the refusal names a *file*, deleting that file looks
like a fix. It is not — it trades a missing permission for permanent damage (rewritten SHAs,
a deleted CI config). **Whenever the workaround mutates the artifact rather than the
credential, stop.** The credential is the thing that is wrong.

## Before you escalate, record the rollback

Write the pre-change state to a file first, as a runnable script. A tag cleanup is reversible
only if you captured what each tag pointed at *before* touching it.

Related: `credential-handoff-blocked` (the credential is right but gets rewritten in transit),
`measure-the-right-binary` (the command you measured is not the command that runs).
