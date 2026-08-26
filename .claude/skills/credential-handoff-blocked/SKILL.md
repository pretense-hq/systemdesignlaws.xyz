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

## First, diagnose which layer is blocking

| Symptom | Layer | Verify with |
|---|---|---|
| `SignatureDoesNotMatch`, or credentials look like repeating blocks | **Our own proxy tokenized them** | `echo "$Policy" \| base64 -d \| head -c 40` — real decodes to `{"expiration":...` |
| `executeScript waited 45000ms for document_idle` | **Tool waits for an event an SPA never fires** | `javascript_tool` still works — check `document.readyState` |
| `Runtime.evaluate timed out` | **Your own `await` hung**, renderer is fine | Re-run a *synchronous* expression |
| Fetch pending forever, but the server logs `200` | **Chrome blocked response delivery** (mixed content / PNA) | `lsof -nP -iTCP:$PORT` shows ESTABLISHED + server log shows 200 + promise still pending |

## What a file picker costs you

`file_upload` needs an element `ref` from `read_page`/`find`. On an SPA that never reaches
`document_idle`, **both of those block while `javascript_tool` still works**. So you can click,
navigate and read via JS — everything except selecting a file. Knowing that boundary early stops
you retrying the wrong tool.

## Tested against a real compliance platform (2026-08-26)

Each route below was RUN, not reasoned about. Record negative results — a route ruled out with
evidence is worth as much as one that works, because the next session otherwise retries it.

| Route | Result |
|---|---|
| Local HTTP server the page fetches from | **FAILS** — the socket opens and the server logs `200`, but the response never reaches the HTTPS page and the promise hangs rather than rejecting. The server log is the wrong side of the boundary: assert on the page-side promise |
| Chunked base64 into page memory | **WORKS, expensive** — no network boundary, but a 13 KB file is ~18 K characters through context. One small file only |
| Restart the browser with a debugging port, attach over CDP | **BEST** — the existing profile keeps the session, and `setInputFiles()` reaches the OS file picker no other path can. Costs the user their open tabs, so it is their call to make |
| Copied browser profile | last resort — copies session cookies; privacy-sensitive and fragile while the browser holds the lock |
| Hand the file to a human | **always available, and not a failure state** |

**A launcher flag is silently dropped when the app is already running.** `open -a "App" --args --flag`
focuses the existing instance instead. Check for the listener before assuming the flag took effect.

