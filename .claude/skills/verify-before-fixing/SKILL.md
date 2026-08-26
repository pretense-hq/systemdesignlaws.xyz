---
name: verify-before-fixing
description: Check whether a reported defect is already fixed AND already deployed before planning the fix. Use at the start of any bug report, incident, backlog item or "this is broken" claim. Trigger on "fix this bug", "is this broken", "why doesn't X work", "reproduce", "regression", "still failing", "known issue", "should I fix".
---

# The first question is never "how do I fix this" — it is "is it already fixed"

A defect report is a claim about the past. By the time it reaches you the fix may already
exist, may already be merged, and may already be serving traffic. Rebuilding it costs a day
and lands a second implementation of one behaviour beside the first.

**Evidence:** commit `f27c1ea`, shipped 2026-08-22, corrected a checkout success guard that
fell through to the very handler it guarded. The defect was re-reported afterwards from the
original symptom. A day was nearly spent rebuilding a fix that was **already fixed** and
already live. One `git log -S` on the symptom string would have ended it in ten seconds.

## Four states, and only the last one means "working"

| State | What you see in source | What a customer sees | Your move |
|---|---|---|---|
| **not fixed** | nothing | broken | fix it |
| **fixed, unmerged** | a branch | broken | merge it |
| **merged, undeployed** | on the default branch | **broken** | deploy it |
| **deployed** | on the default branch | working | close the report |

`merged` presents to a customer **identically to never fixed**. The middle two rows are where
duplicated work is born, because source looks correct and the symptom is real at the same time.

## The check, in order — source, then history, then the running artifact

```bash
# 1. does the fix exist at all? search by SYMPTOM, not by filename
git log -S'<a distinctive string from the broken behaviour>' --oneline -- <path>
git log --diff-filter=M --oneline -20 -- <path>

# 2. is it on the branch that ships?
git branch -r --contains <sha> | grep -E 'origin/(main|master)$'

# 3. is that commit actually SERVING? ask the artifact, never the deploy record
curl -fsS https://<host>/health | grep -o '<sha-or-version>'
```
Step 3 is the one people skip, and it is the only one that answers the customer's question.

## A build that reports success is not a build that is serving

Observed here: a build marked **Ready**, with an **empty alias list** — the previous build was
still answering the domain nine hours after the fix merged. Git said fixed, the pull request
said fixed, the build said fixed, and the site was broken. Also observed: a backend host that
does not auto-deploy at all, so merging changes nothing until someone runs the deploy by hand.

**Ask the running thing what version it is.** Ask it over the network, on the real hostname,
the way a customer reaches it — not on a preview URL, and not by reading a dashboard.

## Rule out the boring explanation before opening an incident

Name the dullest thing that produces this exact output and disprove it with one command.
Caught in one session: an exit code that was correct by design, cancelled in-flight requests
reported as failures, and a small model that simply did not echo a value back verbatim. The
same discipline that catches a missed defect is what stops an invented one.

## When it IS already fixed, the work is not zero

Do not just close it. The report was real to whoever filed it, so something is still wrong:

- the fix shipped but was **never exercised** — no traffic has taken that path since;
- the deploy is stale, or the domain still points at the old build;
- the symptom has **two causes** and only one is fixed;
- there is no regression test, so it will return.

Say which, in one line, with the command that shows it. "Already fixed" without a version
number is a guess wearing a conclusion's clothes.

## Refuses to do silently
Start writing a fix before running step 1 · claim a fix is live from a merge commit · trust a
deployment record over the artifact itself · close a report without naming which of the four
states it is in.

## Self-test
Point it at a defect whose fix is merged but undeployed. It must report **merged, undeployed**
and refuse to write code. Then point it at one where the fix is unmerged: it must not say
"already fixed". A check that returns the same answer in both cases is measuring nothing.
