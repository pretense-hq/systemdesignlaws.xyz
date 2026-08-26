---
name: infra-audit
description: Audit live cloud state — AWS, Vercel, Supabase, Stripe, Vanta, GitHub. Read-only. Trigger on "infra audit", "what's deployed", "is prod healthy", "cloud state", "who is on what tier".
---

# Report reachability honestly

Mark every service **REACHABLE** or **NOT REACHABLE**. A service you could not reach is not a service that is fine. Never authenticate on the user's behalf; say what is needed and move on.

## Per service, what actually matters here

- **Supabase** — org plan first (a free tier on production means **no backups, no PITR**). Then `get_advisors` for security AND performance; RLS enabled with **zero policies** is not protection, it is everything riding on `service_role`. Check which project the local CLI is *linked* to — a `db push` aimed at the wrong database is one command away.
- **Vercel** — which project serves the apex domain, duplicate projects per repo, and any project failing every deploy (still burning build minutes).
- **AWS** — an expired MCP token is not "no resources". Try the local CLI. An `AccessDenied` from a least-privilege role is a **good** finding; report it as a permissions boundary, not an absence.
- **GitHub** — open PR count, branch count, tags vs published versions, and whether CI actually executes.
- **Vanta** — failing tests split by *fixable in code* vs *blocked on billing* vs *blocked on process*. Most "compliance gaps" here are a plan upgrade, not engineering.

## Cross-check the topology claim

Resolve the DNS and read the response headers. `api.pretense.ai` resolving straight to an EC2 public IP with `Server: nginx` means **no load balancer, no WAF, no CDN** — regardless of what the diagram says.

## Vanta — read the document, not the status

Vanta's framework percentages and green controls report **approval state**, not content. A policy
can be `approved`, `v1.0`, mapped to a control that shows complete, and still be an unedited
template. Confirmed 2026-08-26: the ISO 27001 Clause 4.3 scope statement contained the literal
string `{scope of ISMS}` while every ISO page showed green.

Before reporting any compliance artefact as ready:

```
getPolicyContents(policyId, versionId)            # policies — needs a real versionId
getUploadedEvidenceContents(uploadedDocumentId)   # evidence documents
listPolicyVersions(policyId)                      # to get that versionId
```
then grep the returned text for `\{[a-z ]+\}`, `\{\{TODO`, `<SAMPLES PROVIDED`, `Company Name`, and
for vendors the company does not use. Template vendor lists (Salesforce, Zoom, ZeroTier, Sophos)
are the fastest tell.

Also check **who approved**. An approval executed by an automated session rather than by management
is a nonconformity, not a green — and one may already be logged against it. See
[[compliance-doc-integrity]].

## Framework artefacts are not interchangeable

SOC 2 mandates a System Description (Section III). ISO 27001's analogue is the Clause 4.3 scope
statement; CMMC's is SSP §1–2 per NIST 800-171 §3.12.4. Searching for "system description" across
a workspace returns only the SOC 2 one and makes the other two look absent when they exist under
different names — or makes a real gap look like a naming artefact. Check each framework's own
artefact by name.
