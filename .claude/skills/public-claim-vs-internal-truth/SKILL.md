---
name: public-claim-vs-internal-truth
description: Audit what a Trust Center or public page asserts against what is actually true, including empty sections that are switched on. Use before publishing a trust page, during enterprise review, or when a control claims a recurring activity. Trigger on "trust center", "public claim", "sub-processor list", "what do prospects see", "section is empty", "we say we do X", "annually", "quarterly", "is that true".
---

# An empty section switched ON is a positive assertion

A blank section reads as *"we have nothing to list here"*, not *"we have not filled this in"*. The
visitor cannot tell the difference, and neither can a regulator. Visibility and contents are one
question, and almost every audit treats them as two.

## Incident 1 — the visible-and-empty sub-processor list

The Trust Center's sub-processor section was **visible with zero entries**. To a prospect, that
states: *"Acme uses no sub-processors."*

The company runs on the cloud provider, the hosting provider, the managed database and the payment provider. The claim is false, it is on the page a
security reviewer opens first, and under GDPR Art. 28(2) the sub-processor list is contractually
load-bearing — a customer relies on it to know who touches their data.

Three states, only two of which are honest:

| Section state | Reads to a prospect as | Honest when |
|---|---|---|
| hidden | "not published" | you are not ready to publish |
| visible + populated | "these, and only these" | the list is complete and current |
| **visible + empty** | **"we have none"** | you genuinely have none — almost never |

## Incident 2 — a published control asserting a recurring activity that never happened

A control published on the Trust Center read: *"reviews are performed annually."* No review had
ever been performed.

This is **worse than a missing document**, and the reason is specific:

| | missing document | false recurring claim |
|---|---|---|
| Visibility | internal | **externally visible** |
| Timestamp | none | **dated** — "annually" implies a last-performed date |
| Auditor reading | a gap, closable | a **misstatement**, and it impeaches every other claim |
| Fix | do the thing | do the thing **and** correct a public statement already relied upon |

A gap says "not yet". A false recurring claim says "yes, routinely" — and the first question is
*"show me the last one"*.

## Audit visibility and contents TOGETHER

Never check one without the other. The failure mode lives exactly in the gap between them.

```
fetchTrustCenterContent(contentTypes: [SUBPROCESSORS, CONTROLS, RESOURCES,
                                       FAQ, COMPLIANCE, MEDIA, UPDATES])
```
Each section returns `count` **and** `isSectionVisible`. The rule:

```
isSectionVisible == true  AND  count == 0        ->  FALSE CLAIM. Fix now.
isSectionVisible == false AND  count  > 0        ->  content exists but nobody sees it (harmless)
isSectionVisible == true  AND  count  > 0        ->  read every item; see below
```
Also note `count` reflects **resolvable** items — entries whose underlying vendor, control, or
resource can no longer be resolved are silently omitted. A count of 4 does not mean 4 rows were
authored. And a visible section plus a PUBLIC item does not prove a given visitor can see it: that
also depends on whether the Trust Center is public, and on per-viewer access grants.

## Then classify every published control: intent or performance

This distinction decides **false** vs **merely unevidenced** — the whole severity call.

| Wording | Class | If it never happened |
|---|---|---|
| "reviews **are performed** annually" | **performance** | **FALSE** — externally visible misstatement |
| "access **is reviewed** quarterly" | **performance** | **FALSE** |
| "we **maintain** a sub-processor list" | performance | FALSE if none exists |
| "our policy **requires** annual review" | intent | unevidenced — a gap, not a lie |
| "reviews **are to be** performed annually" | intent | unevidenced |
| "**Acme commits to** reviewing annually" | intent | unevidenced |

Grep for the performance markers: `are performed`, `is reviewed`, `we conduct`, `we maintain`,
`are monitored`, plus every cadence word — `annually`, `quarterly`, `monthly`, `continuously`,
`on an ongoing basis`.

**Remediation order matters.** If a claim is performance-class and untrue, you have two moves:
either **perform it today** (often hours for a solo founder — a dated access review is a real
artifact) or **reword to intent** and publish the correction. Do not leave it live while you
schedule the work; every day it stays up is a day a prospect relied on it.

## Checklist

- [ ] Every section: `isSectionVisible` and `count` read together; no visible-and-empty section.
- [ ] Sub-processor list populated with every provider that touches customer data, or hidden.
- [ ] Every published control classified intent vs performance.
- [ ] Every performance claim has a dated artifact behind it, or is reworded and corrected.
- [ ] Cross-check the public claim against the internal evidence in
      [[evidence-request-mismatch]] — a control can be green internally on the wrong document
      *and* published externally as performed, which is two defects sharing one sentence.

## Self-test
Seed the exact defect this skill describes into a fixture, confirm the check reports it,
then remove the check and confirm the fixture now passes. A check never seen to fail is
not evidence.
