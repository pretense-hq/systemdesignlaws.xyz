---
name: denylist-guards-leak
description: Stop using a forbidden-word list to enforce a rule that matters. Use when writing or reviewing any guard that blocks bad phrasing, when a P0 rule is enforced by a regex of verbs, or when a check keeps needing "one more pattern". Trigger on "add a pattern to the guard", "denylist", "blocklist", "forbidden words", "the guard missed it", "banned phrasing", "content check".
---

# A verb denylist cannot carry a P0 rule

Denylists enumerate the ways to be wrong. There is no end to that list, and every gap is a silent
pass. The evidence is a P0 guard on this product's core law that was widened twice and still leaked.

## Round 1 — one verb, five misses out of six

The guard matched `\bredacts\b`. Compliance prose is **passive**, so it saw the one form the
documents never use:

| Seeded sentence | Guard |
|---|---|
| `The proxy redacts secrets at egress.` | RED |
| `Customer secrets and PII are redacted at egress.` | **GREEN** |
| `Egress works by redacting secrets…` | **GREEN** |
| `Egress applies one-way redaction…` | **GREEN** |
| `The proxy permanently strips secrets; they are unrecoverable.` | **GREEN** |
| `Secrets are removed and cannot be recovered.` | **GREEN** |

**5 of 6 real phrasings passed.** Active third-person singular is a stylistic accident of the
example the author had in mind.

## Round 2 — thirteen patterns, twelve bypasses still

Widening to inflections (`redact|redacts|redacted|redacting|redaction`) plus `strip*`, `remove*`,
`discard*` — 13 patterns — left all of these green:

```
destroyed      scrubs        erases        sanitises
wiped          expunged      zeroes out    masked
```
plus `irreversibly` used where the guard only knew `permanently`. Twelve bypasses, each a word an
ordinary technical writer would pick without a second thought. Note `sanitises` — a spelling
variant is a bypass too, and so is `sanitizes`.

**The list will never close.** Every new synonym is a P0 that ships.

## The durable fix — pair the denylist with a POSITIVE requirement

Stop asking *"is the wrong assertion absent?"* Ask *"is the correct assertion present?"*

```
DENY  (necessary, never sufficient)   no one-way-removal claim appears
REQUIRE (the load-bearing half)       the reversible-mutation claim IS present,
                                      in the section that carries it
```
The positive half cannot be bypassed by vocabulary, because it is satisfied by exactly one thing:
the true statement being there. A document that says nothing at all now **fails**, where a pure
denylist would have passed it — and "says nothing" is the most common real-world state.

Concretely, for the ALWAYS-MUTATE law:

```bash
# half 1: no one-way claim (best-effort, will always be incomplete)
command grep -inE "$(paste -sd'|' patterns/one-way-verbs.txt)" "$DOC" && fail "one-way claim"

# half 2: the correct claim must be present in the egress section  <- the real guard
command grep -qiE 'reversibl[ey].{0,40}(mutat|swap)|mutat.{0,40}reversibl' "$DOC" \
  || fail "no reversible-mutation assertion in $DOC"
```
Half 2 is what makes the guard hold. Half 1 only catches a document that says both things.

## Over-broad negation markers punch new holes

The negation set exists so corrective prose stays legal — `never one-way redacts`, `corrects the
SSP's redaction wording`. But every marker added to that set is an **exemption**, and exemptions
leak.

Adding `replaces` as a "corrective verb" exempted this:

> `The token replaces the secret and the original value is discarded.`

The sentence asserts one-way removal (`discarded`) and the guard licensed it, because `replaces`
appeared nearby. A negation marker must be a word that **cannot** appear in a genuine assertion.
`never`, `not`, `no` qualify. `replaces`, `swaps`, `handles` do not — they are ordinary
description verbs.

Rules for the negation set:
1. **Word-bound every marker.** Bare `not` matches inside `another` and `cannot` — see
   [[negation-scope]], where that silenced a gate on ordinary prose.
2. **Clause-scope the reach**, never a flat character window.
3. **Seed each marker in both directions** before adding it: the corrective sentence must stay
   green, and a genuine assertion containing that marker must still redden.

## Review checklist for any denylist guard

- [ ] Is there a **positive** requirement paired with it? If not, the guard is advisory.
- [ ] Enumerate inflections: `X`, `Xs`, `Xed`, `Xing`, `Xion(s)`, plus `-ise/-ize` spellings.
- [ ] Enumerate **synonyms that carry the same claim** — the defect is the assertion, not the word.
- [ ] Passive voice seeded? Active-only patterns miss the majority of compliance prose.
- [ ] Every negation/exemption marker word-bound, clause-scoped, and seeded both ways.
- [ ] Arm 3 of [[false-green-hunt]]: correct prose must stay green, or you have built a guard that
      reddens on everything and will be disabled within a week.

## Self-test
Seed the exact defect this skill describes into a fixture, confirm the check reports it,
then remove the check and confirm the fixture now passes. A check never seen to fail is
not evidence.
