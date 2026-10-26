# Your AI Gateway Logs Are a Credential Store

**TL;DR** - On October 21, 2026, attackers published a poisoned LiteLLM 1.107.0 using GitHub tokens that LiteLLM believes leaked through its own AI gateway logs. The lesson is architectural: any box that records prompts and responses records whatever secrets ride inside them. Swap secrets before they leave the laptop, log metadata by default, and keep agent tokens short-lived.

>> 30-second version: "An AI gateway sees every prompt and every answer. If it logs bodies, its log store holds every credential an engineer or agent ever pasted, and it needs the same protection as a vault. Better: keep real secrets on the laptop so the gateway sees stand-ins every time."

---

## What Happened

LiteLLM is a popular open-source gateway that sits between applications and model providers. According to the Cloud Security Alliance research note published October 23:

- **The release:** malicious `litellm==1.107.0` builds reached PyPI, Docker Hub and GHCR on October 21. The PyPI window was roughly 11:39 to 13:23 UTC. Wiz counted about 49,000 downloads.
- **The access:** the attacker used stolen GitHub CLI OAuth tokens belonging to three LiteLLM engineers. One token was used to override branch protection, one to approve the release, and one to delete workflow records afterward.
- **The suspected leak path:** an internet-exposed internal LiteLLM deployment had been logging request and response bodies from coding-agent sessions. LiteLLM reports cases where GitHub CLI tokens ended up inside those bodies, and so inside the logs. This is LiteLLM's working explanation; the root-cause review is still open.
- **The payload:** files that run on every Python start and collect cloud, Kubernetes, SSH, registry and AI-provider credentials, then send them to a lookalike domain.

{{PAYWALL}}

---

## The Design Flaw: Logging Bodies at a Chokepoint

**What is an AI gateway?** A proxy in front of model providers that handles routing, keys, quotas, cost tracking and, often, logging. It is the AI version of an API gateway, and it inherits the same habit: log everything for debugging.

That habit is where the exposure starts. A coding agent's traffic is richer than ordinary API traffic. It carries:

- File contents, including `.env` files and config the agent opened.
- Shell output, including tokens a command printed.
- Tool results, including credentials a tool fetched.

Log those bodies and the log store becomes the richest credential collection in the company: searchable, replicated to backups, and it deserves the same guard as the secret manager.

The CSA note's own recommendation states it plainly: treat gateway logs like a secret store and make content logging a reviewed exception.

---

## Four Fixes, Cheapest First

### 1. Log metadata by default

Record model, token counts, latency, user and cost. Turn body logging off by default. When someone needs bodies to debug, turn it on for one user for one hour, and then turn it off again.

### 2. Rotate what may already be there

If any gateway, proxy or observability tool stored agent request or response bodies, search those stores and their backups for token prefixes (`ghp_`, `gho_`, `sk-`, `AKIA`) and revoke every hit. A 2026 GitGuardian study found 64% of secrets that were valid in 2022 were still valid in 2026, so plan to revoke each one yourself.

### 3. Shrink token lifetime

An OAuth token that lives for months turns one log line into months of access. Give agent sessions short-lived, narrowly scoped tokens, and move releases to trusted publishing so the CI pipeline is the one path that ships a package.

### 4. Swap secrets before they leave the machine

The strongest control moves the fix upstream of every log: the gateway stores exactly what it receives, so send it stand-ins. Run a local proxy on the developer laptop that replaces detected secrets with stand-in tokens before the request leaves. The gateway, the provider and every log downstream then hold the stand-in.

Two details keep everything working:

- **Reversible where it is safe.** Code identifiers can be swapped back byte-exact in the answer, so the developer reads their own code.
- **One-way for secrets.** Secret stand-ins stay as stand-ins in model output. If a prompt injection gets the model to echo a stand-in into a link, reversing it would hand the real credential to the attacker.

---

## Where This Shows Up in a System Design Interview

Any design with an LLM in it now has an egress question. Draw the gateway, then say three things:

- Logs hold metadata by default.
- Secrets are tokenized client-side, before the gateway.
- Agent credentials are short-lived and scoped per session.

That is one sentence each and it signals you have read the 2026 incident reports.

---

## Interview Q&A

- **Why swap on the client, ahead of the gateway?** - Scrubbing inside the gateway happens after it has received the secrets, which can still surface in memory dumps, crash reports or a stray log path. Swapping on the client means stand-ins are all that arrive.
- **Is logging prompts ever justified?** - Yes, for evaluation and abuse review. Store them encrypted, with short retention and access logging, and scan for credentials before persisting.
- **What is the blast radius of one leaked GitHub OAuth token?** - Everything that token's user can do, which in this incident included approving a production release.
- **How would you detect this kind of compromise?** - Alert on releases outside the normal pipeline, on branch-protection overrides, and on deleted workflow runs.

---

## Sources

- Cloud Security Alliance, research note on the LiteLLM 1.107.0 compromise (October 23, 2026): https://labs.cloudsecurityalliance.org/research/csa-research-note-litellm-1107-gateway-log-token-compromise/
- GitGuardian, State of Secrets Sprawl 2026: https://www.gitguardian.com/state-of-secrets-sprawl-report-2026

---

*Disclosure: I build [Pretense](https://pretense.ai/?utm_source=substack&utm_medium=newsletter&utm_campaign=sdl-ai-gateway-logs), a local proxy that does fix 4: it swaps API keys, tokens (including GitHub `gho_`/`ghp_` tokens) and code identifiers for stand-ins before a request leaves the laptop. Identifiers come back byte-exact; secrets stay as stand-ins in the reply. It does its job when it runs in front of the gateway, and it works alongside fixes 1 to 3.*

{{SUBSCRIBE}}

{{BUTTON:Read More Articles|https://newsletter.systemdesignlaws.xyz}}
