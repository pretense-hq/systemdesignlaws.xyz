---
name: platform-evaluator-as-witness
description: Use a compliance platform's own evidence evaluator to contradict its own green status, and account for its text extraction mangling what it serves. Use when a control shows complete but you doubt the evidence, or when building an argument that a green is wrong. Trigger on "evaluateEvidence", "the compliance platform says complete", "is this evidence valid", "the dashboard is green", "prove the evidence is wrong", "section symbol", "text extraction".
---

# The platform contradicting itself is stronger than your reading

Telling a founder *"I read the document and it is the wrong evidence"* is an opinion. Showing that
**the platform's own evaluator rejects the evidence on a control the platform marks complete** is
a self-contradiction they cannot argue with — and neither can the vendor's support team.

Always run the evaluator when one exists. It is the cheapest high-credibility evidence available.

## The incident

A the compliance platform control read `isComplete: true`, green on the framework page. Its own evaluator, run
against the attached document:

```
evaluateEvidence(evidenceRequestId, documentCollectionId)
->  validations: []
    "the submitted document is an Internal Audit Report,
     which is the incorrect evidence type"
```
Two independent findings in one call:

1. **`validations: []`** — an empty array, not a pass. Nothing was validated. Per
   `decisions.md` §3, absence is never entitlement: *no validations* means **examined nothing or
   matched nothing**, and it must never read as clean. This is the same shape as
   [[no-op-filter-trap]] and the `SKIPPED` upload in [[false-green-hunt]].
2. **An explicit rejection** — the platform names the mismatch itself. That sentence is the
   deliverable. Quote it verbatim into the ticket; do not paraphrase it into your own words, or
   you convert the platform's testimony back into your opinion.

## How to run it

```
evaluateEvidence(evidenceRequestId, documentCollectionId)          # collection = intended set
evaluateEvidence(evidenceRequestId, uploadedDocumentIds: [...])    # explicit set
```
- Use the **collection** when the collection is exactly the intended evidence set (the default).
- Use **explicit document ids** when evaluating something not yet in a collection.
- It **always enqueues a fresh evaluation** — it is not a way to read a cached result. Do not
  call it to "check the status".
- Never invent ids. Get `documentCollectionId` from `getEvidenceRequestDetails(...,
  includeAttachedEvidence: true)`.

## Reading the result

| Result | Means | Do |
|---|---|---|
| `validations: []` | evaluated nothing / matched nothing | treat as **failure**, never as pass |
| explicit rejection text | the platform disagrees with itself | quote verbatim; this is the finding |
| validations present, passing | evaluator agrees | still read the document — see below |
| errors / not enqueued | evaluator unavailable | say so; do not report a green |

A passing evaluation is arm 1 only. The evaluator reads the same mangled text you are about to
read about, so it can pass a document a human would reject.

## The extraction mangles what it serves — `§` renders as `$`

The platform's text extraction corrupts characters, and it corrupts them **for both audiences at
once**:

```
intended:  §170.21(a)(2)(iii)
served:    $170.21(a)(2)(iii)
```
Every section symbol in the document became a dollar sign. That string is what the **assessor**
reads and what the **platform's own AI** reads. Consequences:

- A regulatory citation becomes unresolvable. `$170.21` is not a CFR reference, so an assessor
  checking your citation finds nothing — see [[regulatory-citation-discipline]].
- Any guard or evaluator matching `§\s*\d` finds zero hits in the served text while the source
  file is correct. A check that passes on your local `.docx` can fail on what the platform serves,
  and vice versa.

**Verify the served text, not your source file** (`decisions.md` §7 — verify the artifact the
customer receives). Fetch through the API and grep:

```bash
# what does the platform actually serve?
getUploadedEvidenceContents(uploadedDocumentId) | grep -n '\$1[0-9][0-9]\.' 
# expect §; a $ here means the extraction mangled it
```
Practical mitigation: **avoid characters the extraction eats** in text that must survive. Write
`Sec. 170.21(a)(2)(iii)` or `32 CFR 170.21(a)(2)(iii)` rather than relying on `§`. Losing the
glyph is cosmetic; losing the citation is a finding.

## Sweep the whole set, not the one you doubt

Run the evaluator across every request that shows complete, not only the suspicious one. The
contradiction above was found on a control nobody had flagged. Pair with the reverse index from
[[evidence-request-mismatch]]: evaluate the high-fan-out files first, since one wrong file there
produces several wrong greens.

## Report shape

> the compliance platform control `X` reports `isComplete: true`. the platform's own `evaluateEvidence` on the attached
> evidence returns `validations: []` and states: *"the submitted document is an Internal Audit
> Report, which is the incorrect evidence type"*. The platform's status field and the platform's
> evaluator disagree; the evaluator is the one reading the document.

## Self-test
Seed the exact defect this skill describes into a fixture, confirm the check reports it,
then remove the check and confirm the fixture now passes. A check never seen to fail is
not evidence.
