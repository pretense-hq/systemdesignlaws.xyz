---
name: secrets-remote-by-default
description: Move every long-lived credential off disk into a secrets manager and keep it there, without the values ever passing through the model. Trigger on "secrets", "credentials", ".env", "rotate", "secrets manager", "vault", "clear local credentials", "is this key exposed".
---

# A credential on disk is one you cannot rotate, audit, or revoke

The vault is the only system of record. Disk holds a **loader**, never a value.

## Provider-agnostic — follow the convention already present

Detect what the project uses (AWS Secrets Manager, Vault, 1Password, Doppler, GCP) and reuse its
naming. **Never introduce a second vault**, and never invent a new naming scheme beside a
working one — that is an N+1 source of truth wearing a security badge.

## Not every secret belongs in a vault

| Class | Example | Where it goes |
|---|---|---|
| Long-lived service credential | DB URL, service-role key, webhook secret | **vault** |
| Short-lived / auto-minted | OIDC, STS, session tokens | **nowhere** — regenerate on demand |
| Public-by-design | anon / publishable keys | plain config |
| Empty-valued template | `API_KEY=` | leave it; it is documentation |
| Expired | a dead token | delete |

Vaulting a short-lived token is worse than leaving it: within hours it is stale, and it now
looks authoritative.

## Classify by value, and cross-check by name

A shape regex has a blind spot for anything without a known prefix — a plain password, or a
provider whose keys start `0x`. Run **both** passes:

```bash
# by value
grep -vE '^\s*#' "$f" | grep -E '^[A-Z_]+=(sk-|sk_live_|eyJ|whsec_|postgres(ql)?://[^:]+:[^@]+@)'
# by name — catches what shape misses
for k in PASSWORD SECRET TOKEN PRIVATE_KEY SIGNING_KEY WEBHOOK; do grep -n "$k" "$f"; done
```
Then **open the file**. Three separate false positives in one migration were a synthetic test
corpus, a documentation stub, and a match inside a comment.

## Transfer without disclosure

The value must never enter the model's context and never appear in `argv` (`ps` is
world-readable):

```bash
grep -m1 '^KEY=' .env | cut -d= -f2- | tr -d '"' \
  | <vault-cli> put --secret-id <id> --value-from-stdin
```
**Verify by fingerprint, never by eye** — and normalize both sides identically before hashing.
A trailing newline on one side manufactures a false "differs" and sends you storing a duplicate
of something already vaulted.

**If the environment has an egress proxy, DLP, or scanner that rewrites values in flight, what
the model reads is not what is on disk.** Transcribing writes a placeholder into the vault.
Piping is immune, so this procedure works *with* such a layer instead of depending on its
reversal being perfect.

## Through a rewriting layer, conclude from metadata — never from the characters

Measured: every credential value an agent read through such a layer produced **zero**
`grep -F` matches against the same bytes on disk. Nothing announces the substitution — the
values arrive well-formed and credential-shaped, so the wrong conclusion gets reported with
full confidence. An agent that trusts what it reads reports the wrong key, the wrong prefix,
the wrong provider.

Metadata survives, because the *answer* is a number or a boolean — not a secret, so a rewriter
has nothing to swap:

```bash
awk -F= '/^KEY=/{print length($2)}' .env    # length
grep -c '^KEY=sk-' .env                      # prefix present: 1 or 0
shasum -a 256 .env | cut -c1-12              # identity, for comparing two copies
```
Length, character class, prefix, count, digest — decide from those. **If a conclusion requires
the literal value, it is not a conclusion you may draw**: pipe the value into the tool that
needs it and compare fingerprints instead.

## Check the vault before storing anything

Frequently the value is already there. Comparing first turns a migration into a no-op and avoids
minting a second name for one secret.

## Order, and it is not reorderable

1. **Mirror** — additive; changes no running system.
2. **Loader** — inject into the process environment and `exec`; no application code changes when
   the app reads `process.env`.
3. **Prove** — move the plaintext aside and boot. Run the negative control too: without the
   loader it must **fail**. A boot that succeeds either way proves nothing.
4. **Clear** — every copy, including ones inside worktrees. A depth-limited sweep misses those,
   and one remaining copy makes "exclusively vaulted" false while looking finished.

## The loader fails closed

No credentials, unreadable secret, or a missing required key ⇒ non-zero exit and the process
**never starts**. Booting against a default connection string is the failure this prevents.
*Absence is never entitlement.* Prove it with a deliberately broken profile.

## Escalates, never decides
**Rotation.** Mirroring is not rotating — afterwards the credential exists in the vault *and*
wherever it leaked. Rotation breaks production until a redeploy, so it is the owner's call. Best
done right after the loader is proven, when it costs a secret update instead of a deploy.

## Self-test
A fixture with a short-lived token and an empty-valued key: it must vault neither. A `.env` with
no loader present: it must refuse to delete. Remove its guards and it must fail.
