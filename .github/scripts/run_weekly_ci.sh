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

# Outcome detection (fail-closed: anything unexpected = failure).
if grep -q "AUTH_FAILURE" "$LOG"; then
  summary "### Weekly publish: AUTH FAILURE — refresh the SUBSTACK_COOKIES secret"
  exit 3
elif grep -q "PUBLISH_OK:" "$LOG"; then
  summary "### Weekly publish: PUBLISHED ✅  $(grep 'PUBLISH_OK:' "$LOG" | tail -1)"
  exit 0
elif [ "$MODE" = "draft" ] && grep -q "DRAFT_READY:" "$LOG"; then
  summary "### Weekly publish (draft test): DRAFT READY ✅  $(grep 'DRAFT_READY:' "$LOG" | tail -1) — review, nothing published"
  exit 0
elif grep -qE "NOTHING_QUEUED|ALREADY_PUBLISHED:" "$LOG"; then
  summary "### Weekly publish: no-op — $(grep -E 'NOTHING_QUEUED|ALREADY_PUBLISHED:' "$LOG" | tail -1)"
  exit 0
else
  summary "### Weekly publish: FAILED (rc=$RC) — see run log / artifact"
  exit 4
fi
