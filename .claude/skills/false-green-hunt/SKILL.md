---
name: false-green-hunt
description: Find checks that pass while proving nothing. Use before trusting any green suite, when a test has never been seen to fail, or when adding a guard. Trigger on "is this tested", "false green", "vacuous", "why did CI pass", "prove the test works".
---

# A check you have never seen fail is not a check

`testing.md`: a test that passes with the feature deleted is a fake test.

## The five shapes, all found in this repo

1. **Absence read as success.** `grep -qF "$secret" missing_file` exits non-zero, and the else-branch reports "no longer present". Seven assertions in `mutation-gate.sh` passed against a CLI that wrote nothing. *Absence of the FILE is not absence of the SECRET.*
2. **Line-counting JSON.** `gh --json | grep -c '"number"'` counts LINES (always 1). Reported "1 open PR" when there were 78.
3. **Skipping the defect's own shape.** A guard that skipped artefact names containing `$` passed vacuously — `$` is exactly what the live defect looked like.
4. **`X="$(… || true)"; RC=$?`** — RC is always 0. The gate's H3 check hunts these.
5. **A green that never ran.** `deploy-backend.yml:68`: *"every run of this workflow to date has been a no-op."*

## The procedure — three arms, never two

```
arm 1  the check passes on the real thing
arm 2  DELETE the feature -> the check must go RED, naming the thing
arm 3  CONTROL: the check must still pass on a valid case
```

**Arm 3 is not optional.** A guard that reddens everything is as useless as one that never fires. "Throw on everything" satisfies arms 1 and 2 while breaking every deployment.

## Non-vacuity assertions to embed

Before asserting absence, assert the artefact **exists and is non-empty**. Before asserting a parse result, assert the parser found **more than zero** items. Both are one line and both have caught real defects here.

## The approved-but-empty document

A compliance platform reports a policy **approved**. That is a status field, not a reading of the
body. Observed 2026-08-26: an ISO 27001 Clause 4.3 scope statement sat `approved v1.0` and green
while its text read `The Scope of <Company>'s ISMS is: {scope of ISMS}`. Every framework page was
green; the document was a blank template.

Green on a dashboard is arm 1 at best. Fetch the body through the API and grep it. See
[[compliance-doc-integrity]].

## Skip reported as success

```
SKIPPED   01-isms-scope-of-the-isms   "a version already exists"
```
Exit code 0. The uploader treated *a version already exists* as a reason to stop, so the corrected
document never landed and the template it was meant to replace was approved instead. **Read the
upload log, not the exit code.** Any tool that can say "already done" can say it wrongly — and
"absence is never entitlement" (`.claude/rules/decisions.md` §3) applies to skips.

## Two ways a content check passes on nothing

Both caught in one session, in the checker itself:

1. **Prose satisfies a substring check.** `grep -q '\bDatadog\b'` passed on the phrase
   *"AWS/Datadog/GitHub keys"* — a key type, not an in-scope system. The document's inventory did
   not list Datadog at all.
2. **The wrong table satisfies a scoped check.** After narrowing to markdown table rows, deleting
   the database provider from the system inventory *still passed*, because its name also appeared
   in a Complementary Subservice Organization Controls table. Arm 2 caught it; the first fix had not.

Lesson: when arm 2 fails to redden, the bug is in the check, not the seed. Re-scope and re-seed
until deletion actually reddens the specific assertion you intended.

## Two guards that pass on the defect they exist to catch

**A one-directional consistency check silently passes EXTRAS.** A guard that walks the
canonical set and asserts each item exists in every copy catches drift and deletion — and is
structurally blind to a file one copy carries that the canonical set does not, because that
file is compared to nothing. Proven by planting a rogue file in one copy and watching the guard
print PASS.

```
for item in canonical: present in copy?       catches drift + missing
for item in copy:      present in canonical?  catches EXTRAS  <- the half usually absent
```
Walk the union and assert set equality **both ways**. A drift guard that cannot fail on an
addition is a drift guard for half the ways things drift.

**A guard with zero production callers proves nothing about production.** A catalog check
compared a hand-maintained fixture with a published list. Nothing in the running system read
that fixture, so drift in the provider it existed to guard could never reach it — and the
fixture became a second source of truth needing its own sync. Before trusting any guard, ask
**what feeds it its data**. If that is not the same source production reads, the guard is
measuring its own copy and the green is about the copy.

## Self-test
Take any guard you rely on and delete the thing it guards: it must go red and name it. Restore
it and feed the guard a valid case: it must go green. Then add something the guard was never
told about — an extra file, a new provider value: if it stays green, you have measured only what
you already listed.
