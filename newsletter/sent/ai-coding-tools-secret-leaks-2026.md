# AI-Assisted Commits Leak Secrets at Twice the Rate: Designing for It

**TL;DR** - GitGuardian counted about 29 million new secrets on public GitHub in 2025, up 34%, with AI-service credentials up 81% and AI-assisted commits leaking at roughly double the baseline. Answer it with design: fewer long-lived secrets, scanning at every boundary, and secrets swapped out before code reaches a model.

>> 30-second version: "AI tools raise the volume of code and the number of places secrets travel: commits, prompts, MCP configs, logs. Treat every one of those as an egress path, give each one a control, and make credentials short-lived so any slip expires on its own."

---

## The Numbers

From GitGuardian's State of Secrets Sprawl 2026 (published March 17, 2026, covering 2025):

- **About 29 million** newly leaked secrets on public GitHub, up 34% year over year, the largest single-year jump the report has recorded.
- **1,275,105 AI-service secrets** leaked, up 81%.
- **About 3.2%** of commits made with Claude Code's help leaked a secret, roughly twice the baseline. The report itself cautions that this may reflect human mistakes as much as AI behavior.
- **24,008 unique secrets** sat in the MCP configuration files it studied.
- **64%** of secrets that were valid in 2022 were still valid in 2026.
- Internal repositories were about **6x** more likely than public ones to contain hardcoded secrets.

The last two matter most for design. Leaks stay live until someone revokes them, and private repos need the same scanning as public ones.

{{PAYWALL}}

---

## How AI Tools Reshape Secret Handling

Before coding agents, a secret leaked in roughly one way: someone committed it. Now there are four or more paths.

- **Commits** - more code, written faster, with lighter review.
- **Prompts** - an agent reads `.env`, a config or shell output and sends it to a model provider.
- **Tool configs** - MCP servers configured with long-lived tokens in plain JSON files.
- **Logs** - gateways and observability tools that store request and response bodies (see the LiteLLM 1.107.0 compromise on October 21, 2026).

Each path needs its own control. One pre-commit hook covers the first path.

---

## A Layered Design

### Layer 1: Fewer secrets to leak

- **Short-lived credentials.** Use workload identity and OIDC for CI and cloud access, and session tokens for agents. A token that expires in an hour turns a leak into a short incident report.
- **References over values.** Configs point to a secret manager entry. MCP configs read from the environment or a keychain.

### Layer 2: Scan at every boundary

- **Pre-commit and pre-push** hooks on developer machines.
- **Server-side push protection** on the repository host, because hooks can be skipped.
- **Log pipelines** scanned before persistence.

### Layer 3: Keep secrets out of prompts

This is the newest boundary and the one with the most room to grow. Options, in increasing strength:

- **Ignore files** that keep the agent out of `.env` and key directories. They are easy; pair them with a scanner for secrets inside source files and command output.
- **A local egress proxy** that inspects each outbound prompt and swaps detected secrets for stand-in tokens before the request leaves the machine. The provider and every log after it see the stand-in.

The design rule for that proxy: code identifiers can be reversed back into the answer byte-exact, but secret stand-ins must stay one-way. Reversing a secret token in model output would let a prompt injection exfiltrate it through a crafted link.

### Layer 4: Plan for a slip and contain it

- Alert on first use of a credential from a new network or ASN.
- Keep a rotation runbook that works in minutes, and rehearse it.

---

## How to Use This in an Interview

When a design includes an LLM or an agent, add one box and one sentence: "Prompts pass through a local egress proxy that tokenizes secrets; the gateway logs metadata by default; agent credentials are session-scoped." It is cheap to say and shows you treat the model call as egress.

---

## Interview Q&A

- **Why is a 2x leak rate a design question more than a training question?** - Volume is rising fast enough that a steady human error rate produces more leaks every year. Controls have to scale with commits, independent of headcount.
- **Why scan private repos?** - In the same report they were about 6x more likely to contain hardcoded secrets, and anyone with read access, or a stolen token, can read them.
- **What is the weak point of pre-commit scanning?** - It is optional on the client. Pair it with server-side push protection.
- **Why one-way for secrets but reversible for identifiers?** - Identifiers are needed to read the answer. Secrets stay as stand-ins in model output, because reversing them opens an exfiltration path.

---

## Sources

- GitGuardian, State of Secrets Sprawl 2026: https://www.gitguardian.com/state-of-secrets-sprawl-report-2026
- GitGuardian press release (March 17, 2026): https://blog.gitguardian.com/the-state-of-secrets-sprawl-2026-pr/
- Cloud Security Alliance, LiteLLM 1.107.0 research note: https://labs.cloudsecurityalliance.org/research/csa-research-note-litellm-1107-gateway-log-token-compromise/

---

*Disclosure: I build [Pretense](https://pretense.ai/?utm_source=substack&utm_medium=newsletter&utm_campaign=sdl-secrets-sprawl-2026), the local egress proxy described in layer 3. It swaps API keys, tokens and code identifiers for stand-ins before a prompt leaves the laptop, restores identifiers byte-exact in the answer, and keeps secrets as stand-ins. By default it flags emails and phone numbers for review.*

{{SUBSCRIBE}}

{{BUTTON:Read More Articles|https://newsletter.systemdesignlaws.xyz}}
