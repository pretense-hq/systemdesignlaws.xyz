#!/usr/bin/env bash
# Weekly newsletter orchestration for GitHub Actions (cloud, unattended).
# Mirrors the local run-weekly.sh but with no macOS bits: no osascript, repo-relative
# paths, outcome reported via exit code + $GITHUB_STEP_SUMMARY.
#
# Env:
#   MODE                 publish (default) | draft   (draft = write+validate, never publish)
#   ANTHROPIC_API_KEY    required for the claude CLI to authenticate
#   GITHUB_WORKSPACE     repo root (provided by Actions; falls back to PWD)
set -uo pipefail

REPO="${GITHUB_WORKSPACE:-$(pwd)}"
AUTO="$REPO/.github/automation"
VENV="$REPO/newsletter/scripts/.venv/bin/python"
MODE="${MODE:-publish}"
LOGDIR="$REPO/.github/automation-logs"
mkdir -p "$LOGDIR"
LOG="$LOGDIR/run.log"
: > "$LOG"

summary() { [ -n "${GITHUB_STEP_SUMMARY:-}" ] && echo "$1" >> "$GITHUB_STEP_SUMMARY"; echo "$1"; }

cd "$REPO" || { summary "FAILED: repo not found"; exit 1; }

# Refuse to start the LLM with no credentials.
if [ ! -f "$REPO/newsletter/scripts/.env" ] && [ ! -f "$REPO/newsletter/scripts/.substack-cookies.json" ]; then
  echo "AUTH_FAILURE: no .env / cookies present (set SUBSTACK_COOKIES secret)" | tee -a "$LOG"
  summary "### Weekly publish: BLOCKED — no Substack credentials (SUBSTACK_COOKIES secret missing)"
  exit 2
fi
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "AUTH_FAILURE: ANTHROPIC_API_KEY not set" | tee -a "$LOG"
  summary "### Weekly publish: BLOCKED — ANTHROPIC_API_KEY secret missing"
  exit 2
fi

# Allowlist: venv python + diagram tooling only; deny ALL git and network shells.
# (The workflow — not the agent — performs git commit/push.)
ALLOW="Bash($VENV:*),Bash(node:*),Bash(npx:*),Bash(bash $REPO/newsletter/scripts/export_excalidraw.sh:*),Bash($REPO/newsletter/scripts/export_excalidraw.sh:*),Read,Write,Edit,Glob,Grep,LS,TodoWrite"
DENY="Bash(git:*),Bash(curl:*),Bash(wget:*),Bash(ssh:*),Bash(scp:*)"

if ! command -v claude >/dev/null 2>&1; then
  echo "ERROR: claude CLI not found on PATH" | tee -a "$LOG"
  summary "### Weekly publish: FAILED — Claude Code CLI not installed (npm i -g @anthropic-ai/claude-code)"
  exit 7
fi

echo "=== weekly CI run (mode=$MODE) ===" | tee -a "$LOG"

PROMPT="$(cat "$AUTO/orchestrate-weekly.md")"
if [ "$MODE" = "draft" ]; then
  echo "MODE: DRAFT TEST RUN (write + validate only; no publish, no email)" | tee -a "$LOG"
  PROMPT="## RUNTIME OVERRIDE (HIGHEST PRIORITY - supersedes any conflicting rule below)
This is a DRAFT TEST RUN. Do steps 1-5 ONLY: select the first queued topic, run the
anti-duplicate guard, write the article to newsletter/drafts/<slug>.md, ensure its diagrams
exist, and validate with the unittest. Then STOP. Do NOT run create_draft.py, do NOT run
publish_draft.py, do NOT publish, do NOT send any email, and do NOT change any status in
newsletter/backlog.json. As your final line emit exactly one of:
  DRAFT_READY: <slug>
  NOTHING_QUEUED
  ALREADY_PUBLISHED: <slug>
Never emit PUBLISH_OK in this mode.

$PROMPT"
fi

claude -p "$PROMPT" \
  --permission-mode acceptEdits \
  --allowedTools "$ALLOW" \
  --disallowedTools "$DENY" \
  --add-dir "$REPO" \
  2>&1 | tee -a "$LOG"
RC=${PIPESTATUS[0]}

# ── Outcome detection (fail-closed) ────────────────────────────────────────
# Order matters. SUCCESS markers are checked FIRST so an article whose text
# happens to contain trigger words ("rate limit", "credit balance", "billing")
# can never be misclassified as an API error, and so a transient error that
# the CLI internally retried-and-recovered from does not mask a real success.
# Infra-error signatures use Anthropic/CLI-specific strings (not generic words)
# and are only reached when NO status marker was emitted (i.e. claude truly failed).
fail_tail() { echo ""; echo "---- last 20 log lines ----"; tail -n 20 "$LOG"; }

if grep -q "PUBLISH_OK:" "$LOG"; then
  summary "### Weekly publish: PUBLISHED ✅  $(grep 'PUBLISH_OK:' "$LOG" | tail -1)"
  exit 0
elif [ "$MODE" = "draft" ] && grep -q "DRAFT_READY:" "$LOG"; then
  summary "### Weekly publish (draft test): DRAFT READY ✅  $(grep 'DRAFT_READY:' "$LOG" | tail -1) — nothing published"
  exit 0
elif grep -q "NOTHING_QUEUED" "$LOG"; then
  summary "### Weekly publish: no-op — nothing is queued in backlog.json"
  exit 0
elif grep -q "ALREADY_PUBLISHED:" "$LOG"; then
  summary "### Weekly publish: no-op — $(grep 'ALREADY_PUBLISHED:' "$LOG" | tail -1) (already live, backlog reconciled)"
  exit 0
# ── Explicit credential / billing failures (clear, distinct exit codes) ──────
elif grep -qi "credit balance is too low" "$LOG" || grep -qi "insufficient credit" "$LOG"; then
  summary "### Weekly publish: BLOCKED — Anthropic credit balance too low. Add credits: https://console.anthropic.com/settings/billing"
  fail_tail
  exit 5
# Auth signatures cover both the raw API error types and the claude CLI's own
# phrasing, seen verbatim in real runs (e.g. run 30205356675):
#   "Failed to authenticate. API Error: 401 API key is invalid."
#   "Invalid API key . Please run /login"
# Bare "401" is deliberately NOT matched — only anchored phrases — so unrelated
# log content (line counts, IDs) can never trip the credential branch.
elif grep -qiE "authentication_error|invalid x-api-key|x-api-key header is required|could not resolve authentication|oauth token (has )?expired|invalid bearer token|failed to authenticate|api error: 401|api key is invalid|invalid api key|please run /login" "$LOG"; then
  summary "### Weekly publish: BLOCKED — ANTHROPIC_API_KEY invalid/expired. Rotate it: gh secret set ANTHROPIC_API_KEY"
  fail_tail
  exit 5
elif grep -qiE "rate_limit_error|overloaded_error|error: 429|error: 529|too many requests" "$LOG"; then
  summary "### Weekly publish: TRANSIENT — Anthropic rate-limited/overloaded. Re-run the workflow later."
  fail_tail
  exit 6
elif grep -qE "AUTH_FAILURE:" "$LOG" || grep -qiE "session expired|missing substack_cookies|no session found" "$LOG"; then
  summary "### Weekly publish: AUTH FAILURE — Substack session expired. Refresh the SUBSTACK_COOKIES secret."
  fail_tail
  exit 3
elif grep -q "PUBLISH_FAILED:" "$LOG"; then
  summary "### Weekly publish: FAILED — $(grep 'PUBLISH_FAILED:' "$LOG" | tail -1)"
  fail_tail
  exit 4
else
  summary "### Weekly publish: FAILED (claude rc=$RC, no status marker emitted) — see log artifact"
  fail_tail
  exit 4
fi
