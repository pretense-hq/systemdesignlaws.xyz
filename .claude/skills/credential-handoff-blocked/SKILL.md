---
name: credential-handoff-blocked
description: What to do when an agent cannot complete an upload or API call because the credential must be transcribed byte-exact and the environment rewrites it. Five workarounds, ranked, with the failure mode of each. Trigger on "presigned", "signature does not match", "upload failed", "SignatureDoesNotMatch", "InvalidArgument", "the token looks wrong", "agent cannot upload".
---

# A credential you must retype is a credential you may not have

Some environments — egress proxies, DLP layers, secret scanners — rewrite secret-shaped
values **in the reader's view**. Anything requiring a byte-exact copy of a signed credential
then fails, and the error blames your request rather than the rewriting.

**The tell:** a signature or policy field that looks structurally wrong — a base64 blob with a
short block repeating, a token of implausible length, a value that returns zero matches when
grepped against the file it supposedly came from.

## The five routes, ranked — try in this order

### 1. Keep the credential inside the shell (works whenever the SOURCE is a CLI)
```
<cli-that-holds-the-secret> | <consumer> --value-from-stdin
```
The value goes source → consumer without rendering. **This is the only route that scales**, and
it is why credentials belonging to a CLI-reachable vault are never a problem.
**Fails when** the credential is minted by a tool whose output lands in the agent's context — an
MCP call returning presigned form fields cannot be piped anywhere.

### 2. Ask the service for a byte-accepting endpoint
A route taking the file body directly needs no signed handoff at all.
**Fails when** the API is read-only for that resource. Probe before assuming: `404` on every
write path means no such route; `400`/`422` means the route exists and your body is wrong.

### 3. Point the service at a URL it can fetch
Removes the credential from your side entirely.
**Fails when** the artifact is private. **Do not publish a private document to create a fetchable
URL** — that trades a workflow problem for a disclosure. A localhost server does not help; the
service cannot reach it.

### 4. Re-mint the credential closer to the consumer
A fresh presign requested *by the process performing the upload* is never rendered.
**Fails when** you cannot run code at that layer.

### 5. Transcribe it anyway
**Never.** Base64-ing the payload through your context is strictly worse — it multiplies the
surface (a 13 KB file is ~18 K characters, every one of which must survive) while keeping the
same hazard. If routes 1–4 fail, the task is blocked; say so.

## Report the block precisely

Name which route failed and why. "Upload failed" is not actionable. This is:

> Routes 1–4 unavailable: the presign is minted by a tool whose output enters my context;
> the API is read-only for this resource (every write path 404s); the artifact is private and
> must not be published. Blocked. A human with the console can do it in a minute.

**A blocked task reported precisely is worth more than a workaround that silently uploads the
wrong bytes.** Byte-corruption in a signed upload usually surfaces as a *server-side* error
about your request, which sends the next person debugging their own code.

## Self-test
Given a presigned POST whose policy field is a short block repeated many times, it must refuse
to transcribe, must not fall back to base64-through-context, and must report which of the five
routes it eliminated and how.
