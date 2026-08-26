---
name: compliance-architecture
description: Structure a compliance evidence system so it cannot lie — one authoritative source, policy vs evidence separation, and the layer each rule belongs in. Use when designing or repairing an evidence pipeline, deciding where a control lives, or when the same fact is claimed in more than one place. Trigger on "compliance architecture", "evidence system", "source of truth", "design vs operating effectiveness", "where should this control live", "which document is authoritative".
---

# An evidence system that can disagree with itself will

A compliance programme is a claim-making machine pointed at an auditor. Its failure mode is not
"a control is missing" — that is a finding you can close. Its failure mode is **the system stating
something untrue with a straight face**, which is a misstatement you cannot.

Five principles. Each earned by an incident, not a framework.

---

## (a) One authoritative source; everything else derives

`01-ISMS` was the authoritative scope statement. Three divergent copies existed:

| Copy | Divergence |
|---|---|
| `01-ISMS.docx` | the corrected text |
| `01-ISMS.md` | an earlier draft |
| `upload/01-ISMS.docx` | the copy actually served to the assessor |

Nothing asserted they agreed. Nothing could tell you which one an auditor would read.

**Rule** (`decisions.md` §4): pick the source that **cannot be wrong** — the artifact the customer
or the assessor actually receives — make it authoritative, derive the rest. If you cannot collapse
them in this change, add a test that **asserts they agree**. Two sources with nothing comparing
them is the most common root cause in this codebase.

Cheapest possible version, ~4 lines:

```bash
for f in 01-ISMS.docx 01-ISMS.md upload/01-ISMS.docx; do
  unzip -p "$f" word/document.xml 2>/dev/null | sed 's/<[^>]*>//g' || cat "$f"
done | md5 -q | sort -u | wc -l    # must be 1
```

## (b) A policy states intent; evidence shows performance

Filing a policy against a request for operating evidence is the **design-vs-operating-effectiveness**
failure — the first thing a SOC 2 auditor tests, and the fastest way to convert a closable gap into
a credibility problem.

| Request wants | Policy gives | Evidence gives |
|---|---|---|
| "a completed access review" | *"access is reviewed quarterly"* | the Q3 review, dated, with the reviewer's name and the accounts touched |
| "screenshots of monitoring" | *"physical access is monitored"* | the actual monitoring output, or an N/A with a reason |

**Never satisfy an "evidence of" request with a "policy for" document.** If no performance exists,
the honest artifact is a dated N/A with a written reason — see [[evidence-request-mismatch]].

## (c) Entitlement and pricing are different questions — one field, one job

- **Entitlement** = "may this account use the feature". Coarse (tier). Belongs in the signed claim.
- **Pricing** = "what do they pay". Fine-grained (seats, discounts). Belongs at checkout.

TASK-688: a 25-seat commercial minimum encoded in the signed licence would have refused **every
solo Enterprise account**, because the mint path defaults `seats = 1`. The same rule at checkout
achieves the identical revenue goal and strands nobody. One field doing two jobs is how a pricing
decision becomes an outage.

## (d) Enforce at the most reversible layer that achieves the goal

```
sales / checkout / config   ← MOST reversible. A mistake is an email and a coupon.
application logic           ← a deploy fixes it.
signed claim / fail-closed  ← LEAST reversible. A mistake is an OUTAGE, and it
security verification         reads as a breach, not a bug.
```

Put the rule in the **highest** layer that actually achieves the goal. Push it lower only when a
customer could **bypass** the higher layer to their own gain. Corollary from `decisions.md` §5:
if a change breaks a large coherent block of existing tests, it is in the wrong layer — a
fail-closed check added to the CLI broke 71 tests; the fail-open was in the proxy.

## (e) Absence is never entitlement; silence is never success

A missing value must never resolve to a passing one. Three separate P0s here:

| Missing thing | Wrong reading | Correct reading |
|---|---|---|
| No files scanned | "clean" (exit 0) | "examined nothing" (exit 3) |
| No local runner found | route to cloud | refuse — `app_no_local_runner` |
| No `seats` claim | allow | refuse |
| No captcha token | submit silently | explicit error |
| Upload `SKIPPED "a version already exists"` | done | **not landed** — the template stayed approved |

Applies to documents too: an empty-but-visible section is a positive assertion, not a blank. See
[[public-claim-vs-internal-truth]].

---

## Design review checklist

1. For each claimed fact, name the **one** artifact that carries it. Anything else is a derivation
   or a test that they agree.
2. For each control, label it **intent** or **performance**. Never file one against the other.
3. For each gate, name the layer. Justify anything below `config` with a bypass threat.
4. For each lookup, write the missing-value branch **first**. If it resolves to "pass", it is wrong.
5. Run the query that counts who fails a new gate. If you cannot run it, that is the blocker — not
   the gate (`decisions.md` §2).

## Self-test
Seed the exact defect this skill describes into a fixture, confirm the check reports it,
then remove the check and confirm the fixture now passes. A check never seen to fail is
not evidence.
