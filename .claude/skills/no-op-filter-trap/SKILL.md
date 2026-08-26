---
name: no-op-filter-trap
description: Prove an API filter actually filters before reading its result as coverage. Use whenever a query "confirms" something good — broad coverage, everything patched, all vendors compliant. Trigger on "the filter returned", "coverage looks good", "9 of 10", "confirming query", "does this filter work", "sanity check the query", "too good to be true".
---

# A filter that returns almost everything may not be filtering at all

The dangerous query is not the one that errors. It is the one that returns a **reassuring** result
you never questioned, because the answer matched what you hoped.

## The incident

```
listVendors(evidenceTypes: [ ...all 17 types... ])   ->  9 of 10 vendors
```
Read as: *nine of ten vendors have at least one of these evidence types on file.* Broad coverage.
Move on.

Then, per vendor:

```
getVendorAssessmentMetadata(vendorId)  ->  evidence: []   documents: []
```
**Both evidence arrays empty** — for the same vendors the filter had just "confirmed". The
`evidenceTypes` argument was doing nothing. The endpoint returned the vendor list it would have
returned with no filter at all, and the 10th vendor was excluded for an unrelated reason (state),
which is exactly what made 9-of-10 look like a real measurement rather than a pass-through.

Had the filter been ignored *and* returned 10 of 10, someone would have been suspicious. **The
near-miss is what sold it.**

## The rule — pass a value that MUST return nothing

Before trusting any filter, run the **null probe**:

```
listVendors(evidenceTypes: ["__nonexistent_evidence_type__"])
```
| Result | Verdict |
|---|---|
| `[]` / 0 rows | filter works — the earlier result means something |
| rows returned | **the filter is a no-op.** Discard every conclusion drawn from it |

One extra call. It would have caught this immediately.

Variants for other shapes:

| Filter kind | Null probe |
|---|---|
| enum / type list | a value not in the enum, or a plausible-but-fake one |
| id list | `["0"]`, `["ffffffffffffffffffffffff"]` |
| date range | a window entirely in the future |
| text search | a nonsense token — `zzqqx_no_match_zzqqx` |
| boolean | both `true` and `false`; if counts are identical, it is ignored |

**Also run the max probe** where cheap: a filter that returns *nothing for everything* is equally
broken, and equally quiet. Two probes bracket it (arms 2 and 3 of [[false-green-hunt]]).

## Generalise: any query whose result you were hoping for

The trap is not specific to `listVendors`. Apply the null probe to every **confirming** query:

| Confirming query | What it might actually be |
|---|---|
| "all N repos have branch protection" | the filter is ignored; you listed all repos |
| "0 findings above severity HIGH" | severity param unsupported; 0 is the parse failure |
| "all users have MFA" | the `mfa=false` filter silently dropped |
| "every control has evidence" | `includeAttachedEvidence` not honoured; arrays absent, not empty |
| `validations: []` from an evaluator | evaluated nothing — see [[platform-evaluator-as-witness]] |

Two silent-failure modes to name explicitly:

1. **Unrecognised parameter ignored.** Most REST APIs drop unknown query params without error.
   Misspell `evidenceTypes` as `evidenceType` and you get a full unfiltered list, HTTP 200.
   Deliberately misspell the parameter once: **if the result is unchanged, the API is ignoring it,
   and it may have been ignoring the correct spelling too.**
2. **Absent vs empty.** `evidence: []` means "none". A **missing** `evidence` key means "not
   returned by this endpoint" — and code that does `len(v.get("evidence", []))` reads the second
   as the first. `decisions.md` §3: absence is never entitlement.

## Then verify per-item, not in aggregate

The aggregate lied; the per-item call told the truth. This is the general shape — the list
endpoint is a projection, the detail endpoint reads the record. **Confirm coverage claims by
sampling detail calls**, at minimum on the items the aggregate says are covered:

```bash
# aggregate said covered; prove it item by item
for v in $COVERED_IDS; do getVendorAssessmentMetadata "$v" | jq '{id, e:(.evidence|length), d:(.documents|length)}'; done
```
Any row with `e:0, d:0` falsifies the aggregate outright.

## Checklist

- [ ] Null probe run; returned zero rows.
- [ ] Parameter name deliberately misspelled once; result changed.
- [ ] Absent vs empty distinguished in the parsing code.
- [ ] At least one per-item detail call confirms the aggregate.
- [ ] The number that looked reassuring (`9 of 10`) explained — *why* was the 10th excluded? An
      unexplained near-miss is the tell.

## Self-test
Seed the exact defect this skill describes into a fixture, confirm the check reports it,
then remove the check and confirm the fixture now passes. A check never seen to fail is
not evidence.
