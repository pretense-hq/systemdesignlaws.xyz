---
name: negation-scope
description: Clip a negation's reach to the clause so an unrelated "no" cannot license a real assertion. Use when writing or fixing any proximity-window guard, negation detector, or "unless X appears nearby" rule. Trigger on "negation window", "unless negated", "characters before", "proximity match", "the guard passed on a sentence it should have caught", "word boundary", "\\bnot\\b".
---

# A negation reaches one clause — not one sentence, and never N characters

Three successive fixes to the same P0 guard, each closing a real leak and exposing the next.

## Leak 1 — the flat character window crossed a paragraph

The guard flagged `\bredacts\b` unless a negation appeared within **60 characters before it**.
Intent correct; implementation leaky. A character window has no idea what a paragraph is:

```
There are no employees and no contractors.

The proxy redacts secrets at egress.        <- asserted; licensed by "no" 58 chars upstream
```
Paragraph breaks, table rows, list items and headings are all **semantically far** and
**numerically near**. Any check with a proximity window has this bug until proven otherwise.

## Leak 2 — sentence scope still licenses an unrelated clause

Clipping to the sentence boundary fixed the paragraph case and left this green:

> `Because no attestation report exists, the proxy redacts secrets at egress.`

The `no` is real, in the same sentence, and about something else entirely. A subordinate clause
carrying a negation does not negate the main clause — it is the *reason* the main clause is being
stated. This is the shape that reaches production, because it reads like careful writing.

## Leak 3 — an unbound marker matches inside ordinary words

`not` without word boundaries matches inside:

```
a<not>her          -> "another"
can<not>           -> "cannot"      (in a sentence asserting the opposite)
<not>able / <not>ice / an<not>ate
```
`another` appears in almost every document, so the guard was silenced on **ordinary prose** — a
near-universal exemption that looked like a working check. Same class: `no` inside `north`,
`known`, `nonce`, `no-op`.

## The fix — clause scope, word-bound markers

```python
CLAUSE_SPLIT = re.compile(r'[,;:]|--|\s+(?:so|then|and|but|therefore)\s+', re.I)
NEGATIONS    = [r'\bnever\b', r'\bnot\b', r'\bno\b', r'\bnone\b', r'\bcannot\b',
                r'\bwithout\b', r"\bdoes\s+n[o']t\b"]

def negated(sentence: str, span: tuple[int, int]) -> bool:
    """True iff a negation shares the CLAUSE containing span."""
    bounds = [0] + [m.end() for m in CLAUSE_SPLIT.finditer(sentence)] + [len(sentence)]
    start  = max(b for b in bounds if b <= span[0])
    end    = min(b for b in bounds if b >= span[1])
    clause = sentence[start:end]
    return any(re.search(n, clause, re.I) for n in NEGATIONS)
```
| Boundary kind | Tokens |
|---|---|
| Punctuation | `,` `;` `:` `--` (and `—`) |
| Coordinators / connectives | `so` `then` `and` `but` `therefore` |
| Structural (clip first) | sentence end, newline, `\n\n`, table cell, list item, heading |

**Order matters:** clip to the sentence first, then to the clause. Clause splitting inside a run-on
paragraph without a sentence clip re-opens leak 1 whenever a paragraph lacks punctuation.

## Seeds — every one of these must be in the test

| Seed | Must be |
|---|---|
| `The proxy redacts secrets at egress.` | RED |
| `Acme never one-way redacts.` | GREEN |
| `There are no employees.\n\nThe proxy redacts secrets at egress.` | **RED** (leak 1) |
| `Because no attestation report exists, the proxy redacts secrets at egress.` | **RED** (leak 2) |
| `In another section, the proxy redacts secrets at egress.` | **RED** (leak 3) |
| `The proxy cannot redact; it mutates reversibly.` | GREEN |

The three bold rows are the regression tests. Without them the next refactor reintroduces the
window, because the window is the obvious implementation.

## Delete the superseded helper

After the P0 test moved to the clause-scoped helper, the old flat-window `_unnegated` was
unreachable — and a comment still claimed it was load-bearing. **Two negation helpers side by side
is an invitation to call the leaky one.** Delete it in the same commit; a dead helper is how the
leak comes back.

## Related

- [[denylist-guards-leak]] — every negation marker is an exemption; over-broad markers
  (`replaces`) punch holes even with correct scoping.
- [[false-green-hunt]] — seed both directions: the assertion must redden, the legitimate negation
  must not.

## Self-test
Seed the exact defect this skill describes into a fixture, confirm the check reports it,
then remove the check and confirm the fixture now passes. A check never seen to fail is
not evidence.
