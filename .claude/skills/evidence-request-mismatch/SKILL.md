---
name: evidence-request-mismatch
description: Find evidence attached to the wrong request by building a reverse index of file to requests. Use when auditing a compliance platform's evidence, before an audit fieldwork window, or when a control is green but you have not read what satisfies it. Trigger on "evidence review", "what's attached to this control", "audit prep", "is this the right evidence", "N/A", "not applicable", "reused document", "same file everywhere".
---

# One document satisfying several unrelated requests is the signal

Walking requests one at a time, every attachment looks plausible — a file is there, the control is
green, you move on. The pattern is **only visible from the file's side**.

## The incident

`access-request-ticket-and-history.docx` was attached to **four** unrelated evidence requests:

| # | Request | Verdict |
|---|---|---|
| 1 | a completed access review | plausible — but a *ticket* is not a *review* |
| 2 | intrusion alarms and surveillance equipment | **wrong artefact** |
| 3 | monitoring physical access | **wrong artefact** |
| 4 | physical access authorizations | **wrong artefact** |

An access-request ticket has nothing to do with intrusion alarms. Three of four were misfiled, and
each looked fine in isolation.

## Build the reverse index — filename → requests

```
requests → files      what the console shows you.  Pattern invisible.
files → requests      what you must build.         Pattern jumps out.
```
```bash
# one row per (file, request); then group
listEvidenceRequests(includeAttachedEvidence: true)
```
```python
from collections import defaultdict
idx = defaultdict(list)
for req in requests:
    for f in req["attachedEvidence"]:
        idx[f["filename"]].append(req["title"])
for fn, reqs in sorted(idx.items(), key=lambda kv: -len(kv[1])):
    if len(reqs) > 1:
        print(len(reqs), fn); [print("   -", r) for r in reqs]
```
**Sort by fan-out descending and read the top of the list first.** A file satisfying 4 requests is
either a genuine multi-control artifact (an org chart, a signed policy) or three misstatements.
There is no third case, and telling them apart takes one read.

## Classify every attachment — four buckets

| Bucket | Definition | Fix |
|---|---|---|
| **policy-as-evidence** | intent filed against a request for performance | produce the dated artifact, or mark N/A |
| **wrong-artefact** | unrelated document, right-ish topic | detach; attach the real one or N/A |
| **not-applicable-misfiled** | control does not apply; a file was attached anyway | **N/A with a written reason** |
| **OK** | the artifact answers the request | leave; note why it is genuinely multi-control |

`policy-as-evidence` is the one an auditor tests first — it is the design-vs-operating-effectiveness
split (see [[compliance-architecture]] principle b). *"Access is reviewed quarterly"* is a policy.
The **Q3 review, dated, naming the reviewer and the accounts touched**, is evidence.

## N/A with a written reason beats an unrelated document — always

For a solo founder with a home office, the correct answer to *"intrusion alarms and surveillance
equipment"* is **N/A**, with the reason recorded:

> Not applicable. Acme has no corporate premises; all personnel work from home offices and all
> production systems are hosted by the cloud provider, the hosting provider and the managed database, whose physical security controls are
> inherited and evidenced by their SOC 2 reports (see CSOC section of the system description).

That is a **defensible gap**. Attaching `access-request-ticket-and-history.docx` instead converts
it into a **misstatement** — the platform now asserts you have surveillance evidence, and the
assessor opens the file and finds a ticket. The gap costs a sentence; the misstatement costs
credibility across every other control you filed.

Rule: **an unrelated attachment is strictly worse than an empty one.** Empty is a to-do. Wrong is
a false claim, and it is dated and attributed.

## The N/A reason must name three things

1. **Why the control does not apply** — the factual condition (no premises, no contractors, no
   card data).
2. **Where the risk actually lands** — inherited from a named provider, or absent by design.
3. **What would change it** — the trigger that makes it applicable again (first office lease,
   first employee). Without this, an N/A written today silently rots into a false one.

## Checklist

- [ ] Reverse index built; fan-out sorted descending.
- [ ] Every file with fan-out > 1 opened and read, not inferred from its filename.
- [ ] Each attachment classified into one of the four buckets.
- [ ] Every N/A carries all three parts of a written reason.
- [ ] Cross-check against [[platform-evaluator-as-witness]] — if the platform has its own evidence
      evaluator, run it on the ones you classified OK; it contradicts its own green status often
      enough to be worth the call.
- [ ] Filenames are not evidence of contents. `access-request-ticket-and-history.docx` describes
      itself accurately and was still wrong three times out of four.

## Self-test
Seed the exact defect this skill describes into a fixture, confirm the check reports it,
then remove the check and confirm the fixture now passes. A check never seen to fail is
not evidence.
