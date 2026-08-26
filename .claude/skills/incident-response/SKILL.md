---
name: incident-response
description: Run the Pretense incident-response pipeline end to end — intake, telemetry, diagnosis, runbook retrieval, a human approval gate, then approved execution, verification, stakeholder comms, and a memory record. Use when an alert fires or a Pretense prod/staging surface is reported broken (www.pretense.ai down, backend /health failing, deploy broken, billing/webhook mismatch, DB/Supabase issue, CDN/release problem). Trigger on "incident", "alert", "X is down", "prod is broken", "on-call".
portable: false
portable_reason: names THIS company's production surfaces (www.pretense.ai, backend /health) and its incident subagent pipeline. Losing option: parameterise the surfaces -- rejected, the runbook value IS the specific surfaces and their probes.
---

# Pretense incident response

Drives the 9-stage pipeline defined in `.claude/workflows/incident-response.js`, backed by five custom agents in `.claude/agents/` (incident-telemetry, incident-diagnostician, incident-runbook, incident-executor, incident-verifier). Nothing that changes state runs without explicit human approval.

## When invoked

1. Capture the alert text from the user (what fired / what's broken). If they didn't give one, ask for the one-line symptom.

2. **Run phase 1 (diagnose — read-only, no approval needed):**
   ```
   Workflow({ name: "incident-response", args: { alert: "<symptom>" } })
   ```
   This runs Intake → Context (parallel telemetry) → Diagnosis → Knowledge → Supervisor and returns `{ stage: "awaiting-approval", intake, diagnosis, runbooks, actions: [...] }`.

3. **Present the plan to the user** — the probable cause, the runbooks matched, and each proposed action (id, what it does, reversible?, risk). Do NOT execute yet. If there are no mutating actions (pure diagnosis), just report findings and stop.

4. **On explicit approval in chat**, run phase 2 with only the approved action ids:
   ```
   Workflow({ name: "incident-response", args: {
     alert: "<symptom>",
     approved: true,
     plan: <the entire phase-1 return value>,
     approvedActionIds: ["a1", ...],
     timestamp: "<current ISO-8601 time>"    // scripts can't call Date.now(); pass it in
   }})
   ```
   This runs Execution (approved actions only, sequential, halts on first failure) → Verification → Communication (drafts the update and files/comments a TASK ticket) → Memory (appends to the incident-log memory).

## Guardrails baked in
- Read-only stages physically cannot restart/deploy/write/delete (agent tool lists + prompt rules).
- Every mutation needs the approval gate; approval is per-action and per-incident.
- Platform gotchas are injected into every stage: never source `.env`, DIRECT_DATABASE_URL for transactions, CLI-only Vercel prod deploys, Actions billing-blocked, deploy keys dead (bundle transport).
- Secret values are never printed.

## After resolution
Confirm the incident-log memory entry and the Jira ticket exist; if the fix revealed a new durable fact, update the relevant memory file per the read-first protocol.
