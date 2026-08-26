---
name: compliance-doc-integrity
description: Verify what a compliance platform actually serves, not what its dashboard says. Use before trusting any policy, system description, SSP or scope statement, and before citing one as audit evidence. Trigger on "is our policy ready", "system description", "scope statement", "SSP", "Vanta says green", "upload the policy", "are we audit ready", "SOC 2 / ISO 27001 / CMMC document".
---

# Approved is not filled in

A compliance platform checks that a document is **approved**. It does not check that the document
is **written**. Those are different questions, and only one of them is on the dashboard.

Observed 2026-08-26 in Vanta: the ISO/IEC 27001 Clause 4.3 scope statement was `approved`, `v1.0`,
green on the framework page — and its body read:

```
The Scope of Pretense's ISMS is: {scope of ISMS}
The following locations are in scope: {e.g. Main HQ, San Francisco, 1234 Lombard Street, 94109}
```

plus six departments the company did not have, five vendors it did not use (Salesforce, Zoom,
ZeroTier, Sophos, Microsoft VPN), an "Epic Database" it did not own, and `<SAMPLES PROVIDED -
UPDATE>` throughout. Clause 4.3 is the first page an ISO auditor opens.

**The UI could not show this. The API could.**

## The three checks, in order

### 1. Read the body through the API, never the console

```
getPolicyContents(policyId, versionId)        # policies
getUploadedEvidenceContents(uploadedDocumentId)  # evidence
```
Then grep the returned text. A green control, an `OK` evidence request, and an `approved` status
tell you nothing about what is inside.

### 2. Grep for the placeholder classes

```
\{[a-z ]+\}          {scope of ISMS}, {include services...}
\{\{TODO            \{\{EFFECTIVE_DATE\}\}
<SAMPLES PROVIDED   <angle-bracket sample text>
Company Name        Epic Database   Clubhouse   ZeroTier
```
Also check for vendors and departments that do not exist. Template vendor lists are the single
most reliable tell that a document was never edited.

### 3. Verify the artifact, not the source

A correct local file proves nothing about what the platform serves. Diff local against API on
every document you believe is done.

## "SKIPPED" is not "uploaded"

The correct scope statement had existed locally for ten days. It never landed. The uploader logged:

```
SKIPPED   01-isms-scope-of-the-isms   "a version already exists"
```

and exited zero. *A version already exists* was treated as success. The stock template stayed and
was subsequently approved. **Read every upload log for skip-as-success** — see
[[false-green-hunt]] and `.claude/rules/decisions.md` §3 (absence is never entitlement).

## Approval integrity

Check **who** approved, not just that something was approved. The same workspace carried
nonconformity `NC-2026-08-16-01`: thirteen policies approved *"by an automated session, not by
management"*, with the documents themselves stating that founder approval was still required
before citing them as evidence.

**Never click approve on an auditor-facing policy as an automated session.** Uploading a draft is
help; approving it manufactures the nonconformity. Upload, then hand approval to a human.

## Two false greens this produced in the checker itself

Writing the drift test, two checks passed while proving nothing. Both are easy to repeat:

1. **Prose mention counted as inventory.** `grep -q '\bStripe\b'` passed because Stripe appeared in
   the phrase *"AWS/Stripe/GitHub keys"* — a key type, not an in-scope system. Require the
   component in a **table row**.
2. **Controls table counted as inventory.** After scoping to table rows, deleting Supabase from the
   system inventory *still passed*, because Supabase also appeared in the Complementary Subservice
   Organization Controls table. Scope the search to rows under an **inventory heading**.

An empty file also passes every placeholder check. Pair every content assertion with a substance
floor, and seed a regression to prove the check fails.

## One boundary, derived everywhere

Nine documents asserted the system boundary with nothing comparing them. Pick the one that cannot
be wrong — for ISO that is the Clause 4.3 scope statement — make it authoritative, derive the rest,
and add a test asserting they agree (`.claude/rules/decisions.md` §4). Cross-framework drift found
this way: the CMMC SSP described the product's core control as *"redacts secrets/PII"* while the
SOC 2 description correctly said *"reversible mutation (not one-way redaction)"* — two filed
documents contradicting each other on the one control customers buy. See `.claude/rules/mutation.md`.

## The 11-auditor panel

Each opens a different page first and fails on a different thing. Run them as parallel reviews and
require an explicit verdict per framework — no blank cells, and a missing verdict is FAIL.

| # | Auditor | Opens first | Fails if |
|---|---|---|---|
| 1 | SOC 2 service auditor (AICPA DC §200) | Section III fair presentation | Boundary/carve-out/CSOC/CUEC incoherent; empty tables |
| 2 | ISO 27001 lead auditor | Clause 4.3 scope | Scope not determinate; exclusions unjustified; 7.5 broken |
| 3 | CMMC C3PAO assessor | Boundary + CUI status | Boundary undefined; CUI status unstated; §3.12.4 thin |
| 4 | ITGC auditor | Component inventory | Inventory contradicts access/change narrative |
| 5 | ISMS internal auditor | Traceability, nonconformities | Claims unevidenced; disputed approval cited |
| 6 | Third-party risk auditor | Sub-processor list | Lists disagree; carve-out method inconsistent |
| 7 | Privacy auditor (GDPR/CCPA/27701) | Data categories and flows | PII or transfers misstated; retention absent |
| 8 | **Technical security assessor** | Data flow vs live system | **Egress misdescribed — P0 BLOCK** |
| 9 | Cloud infrastructure auditor | Shared responsibility | Region/account claims wrong |
| 10 | DFARS / DIBCAC-style auditor | 7012/7019/7020, SPRS | Claims a posture the POA&M contradicts |
| 11 | Customer-side enterprise reviewer | Whatever contradicts itself | Two of your own documents disagree |

## The anti-pattern

Reporting "all frameworks green" from a dashboard. The dashboard is reporting approval state. You
were asked about content.
