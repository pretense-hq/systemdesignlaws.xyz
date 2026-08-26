---
name: shared-pattern-source
description: Stop two hand-maintained copies of the same pattern list from drifting, and catch regex-dialect differences between the engines that read them. Use when a rule is enforced in more than one place — a test suite and a shell gate, CI and a pre-commit hook, a linter and a script. Trigger on "patterns drift", "the gate and the tests disagree", "duplicate regex", "keep them in sync", "POSIX class", "works in grep but not Python".
---

# Two copies of a pattern list always drift — and always in the unsafe direction

Not "may drift". **Always.** The only question is which copy is wrong when you find out.

## The incident

The P0 redaction patterns were maintained twice: once in the Python test suite, once in the shell
gate. Same intent, two hands, no comparison.

| Seed | Test suite | Shell gate |
|---|---|---|
| 4 of 8 seeds | **RED** (correctly caught) | **GREEN** (missed) |

Every single divergence was in the **unsafe** direction — the gate, which is what actually runs at
release time, was the permissive copy. A drift that fails safe is a nuisance; this one shipped.

Compounding it: the gate was also measuring [[measure-the-right-binary|the wrong binary]], so its
green was doubly meaningless.

## The fix: one file, both readers

```
patterns/p0-redaction.txt          <- the ONLY place a pattern is written
  ├── tests/test_redaction.py      reads it
  └── local-gate/gate.sh           reads it
```
```bash
# gate.sh
while IFS= read -r pat; do [ -n "$pat" ] && grep -nE "$pat" "$DOC"; done < patterns/p0-redaction.txt
```
```python
PATTERNS = [l for l in open("patterns/p0-redaction.txt").read().splitlines() if l.strip()]
```
**Not** "keep them in sync" in a comment. Not a CI job that diffs them. One file, read twice. A
comparison job still lets a human land a change to one side and silence the job.

If you genuinely cannot collapse them in this change, the minimum is a test that **asserts the two
lists are byte-identical** — and it must fail on addition, not just on edit.

## The dialect trap — `[[:space:]]` matches nothing in Python

The pattern file is now shared, so a pattern must be valid in **every** engine that reads it. It
will not be.

| Construct | POSIX ERE (`grep -E`) | Python `re` |
|---|---|---|
| `[[:space:]]` | whitespace | **matches nothing** — a `FutureWarning`, not an error |
| `[[:alpha:]]` | letters | same silent failure |
| `\b` | GNU extension only | word boundary |
| `\d` `\w` `\s` | not portable in ERE | fine |
| `(?i)` `(?:...)` | unsupported | fine |

`[[:space:]]` is the dangerous one because **Python does not raise**. It emits a `FutureWarning`
that a test runner swallows, then quietly matches zero characters. The pattern is present, looks
correct, and enforces nothing.

## The portability test — run every pattern through BOTH engines, fail on disagreement

This is the test that makes a shared file safe. Without it, sharing just moves the drift into the
dialect.

```python
import re, subprocess, warnings, pytest

PATTERNS = [l for l in open("patterns/p0-redaction.txt").read().splitlines() if l.strip()]
PROBES   = open("patterns/probes.txt").read().splitlines()   # must-match + must-not-match corpus

@pytest.mark.parametrize("pat", PATTERNS)
def test_pattern_agrees_across_engines(pat):
    with warnings.catch_warnings():
        warnings.simplefilter("error")          # FutureWarning -> failure, not a shrug
        rx = re.compile(pat)
    for probe in PROBES:
        py = bool(rx.search(probe))
        rc = subprocess.run(["grep", "-qE", pat], input=probe, text=True).returncode
        ere = (rc == 0)
        assert py == ere, f"dialect split on {pat!r} for {probe!r}: python={py} ere={ere}"
```
Three things it must do, all load-bearing:

1. **`simplefilter("error")`** — otherwise the `[[:space:]]` case passes silently.
2. **A probe corpus with must-match AND must-not-match strings** — a pattern that matches nothing
   in both engines "agrees" perfectly. Arm 3 of [[false-green-hunt]] applies: the test must be able
   to go red in both directions.
3. **`command grep`, not `grep`** — see [[measure-the-right-binary]]. In an interactive shell
   `grep` may be a function wrapping ugrep, and you will be certifying portability against an
   engine that is in neither production path. `subprocess.run` execs the real binary, but if you
   shell out with `shell=True` you inherit the shim.

## Checklist

- [ ] One file. Both consumers read it at runtime, not at copy time.
- [ ] Portability test over both engines, with `FutureWarning` promoted to error.
- [ ] Probe corpus contains at least one string each pattern must **not** match.
- [ ] Add a pattern that is deliberately dialect-split (e.g. `[[:digit:]]`) once, confirm the test
      reddens, remove it. A portability test never seen failing is not a portability test.

## Self-test
Seed the exact defect this skill describes into a fixture, confirm the check reports it,
then remove the check and confirm the fixture now passes. A check never seen to fail is
not evidence.
