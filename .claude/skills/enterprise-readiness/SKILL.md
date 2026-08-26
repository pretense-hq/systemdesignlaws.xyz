---
name: enterprise-readiness
description: Answer, honestly, what an enterprise security review will find. Use before or during enterprise onboarding, an RFP, a SOC2/ISO questionnaire, or a DPA negotiation. Trigger on "enterprise", "security questionnaire", "SOC2", "can we sell to", "onboarding a client".
---

# Answer as the buyer's auditor would

Frame every finding as the question a security review actually asks, with the answer the codebase gives **today**. Three classes of answer stop a deal outright.

## The questions, in the order they get asked

| Question | Where the real answer lives |
|---|---|
| Can we purchase this tier? | the DTO/enum on the subscription path — a published price with no working checkout is a deal-stop |
| Are production backups enabled? | the DB provider's **org plan**, not the code |
| Is tenant data isolated at the database layer? | RLS **policies**, not RLS enabled |
| SSO / SCIM? | are IdP private keys encrypted at rest; does SCIM update/delete check tenant; is `exp` optional |
| Self-host option? | does the on-prem artefact ship fail-open by default |
| SOC2 / ISO / CMMC | passing-test ratio and how many are **overdue** |
| Offboarding SLA | is anyone currently past it |
| HA / DR | does the API hostname resolve to a single instance |
| Sub-processors | are their certificates current |
| Supply chain | is the artefact **signed**, and can you reproduce the build from a tag |

## The rule

Never answer from a document. Resolve the DNS, read the advisor output, fetch the signature, run the query. A diagram is a claim; a `curl` is an answer.

## Sequencing

A buyer never reaches the feature conversation if they cannot pay you, the database has no backups, and tenant isolation is not enforced. **Enterprise-ready first, features second.**
