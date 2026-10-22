#!/usr/bin/env bash
#
# Run the full CI pipeline locally, without GitHub Actions.
#
# Mirrors both jobs in .github/workflows/test.yml:
#   test          - unit tests, recent-posts.json schema, index.html structure
#   e2e-website   - Playwright browser tests
#
# The e2e job in CI points at the live https://systemdesignlaws.xyz. Locally we
# serve the repo over http.server and point E2E_BASE_URL at that instead, so the
# suite validates the site content even while the public host is down.
#
# Usage:
#   ./scripts/ci_local.sh              # test job + e2e job
#   ./scripts/ci_local.sh --no-e2e     # test job only (no browser needed)
#
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

PORT="${E2E_PORT:-8888}"
RUN_E2E=1
[ "${1:-}" = "--no-e2e" ] && RUN_E2E=0

FAILED=()
SERVER_PID=""

cleanup() { [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null; }
trap cleanup EXIT

step() { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }
pass() { printf '  \033[32mPASS\033[0m %s\n' "$1"; }
fail() { printf '  \033[31mFAIL\033[0m %s\n' "$1"; FAILED+=("$1"); }

# ----------------------------------------------------------------- test job

step "Unit tests"
if python3 -m unittest discover -s tests 2>&1 | tail -3; then
  pass "unittest discover -s tests"
else
  fail "unittest discover -s tests"
fi

step "recent-posts.json schema"
if [ -f recent-posts.json ]; then
  if python3 -c "
import json
d = json.load(open('recent-posts.json'))
assert 'posts' in d and all('title' in p and 'url' in p and 'description' in p for p in d['posts'])
print(f\"  {len(d['posts'])} posts\")
"; then pass "recent-posts.json schema"; else fail "recent-posts.json schema"; fi
else
  echo "  skipped (no recent-posts.json)"
fi

step "index.html structure"
# Each assertion gates the step individually so one miss does not mask others.
check() {
  if grep -q "$1" index.html; then pass "$2"; else fail "$2 (pattern not found: $1)"; fi
}
check '<div class="recent-list" id="recent-list">' "Recent Issues container"
check 'id="recent-posts-data"'                     "Inline posts data"
check 'recent-posts.json'                          "Dynamic fetch"
check 'id="recent-updated"'                        "Last updated container"
check 'id="subscribe-section"'                     "Substack email signup section"
check 'newsletter.systemdesignlaws.xyz'            "Subscribe links point to newsletter subdomain"
check 'guardrail-issue'                            "Frontend guardrail fallback"

# ---------------------------------------------------------- e2e-website job

if [ "$RUN_E2E" = "1" ]; then
  step "E2E (local server on :$PORT)"

  if ! python3 -c "import playwright" 2>/dev/null; then
    fail "playwright not installed - pip install playwright"
  else
    # The pip package pins an exact browser build. If the preinstalled browsers
    # under PLAYWRIGHT_BROWSERS_PATH are a different build, launch() fails with
    # "Executable doesn't exist" - install the playwright release matching them
    # rather than downloading a second copy.
    want=$(python3 -c "
import json, pathlib, playwright
p = pathlib.Path(playwright.__file__).parent / 'driver' / 'package' / 'browsers.json'
print([b['revision'] for b in json.load(p.open())['browsers'] if b['name'] == 'chromium'][0])
" 2>/dev/null)
    have=""
    if [ -n "${PLAYWRIGHT_BROWSERS_PATH:-}" ] && [ -d "${PLAYWRIGHT_BROWSERS_PATH}" ]; then
      have=$(ls -d "${PLAYWRIGHT_BROWSERS_PATH}"/chromium-* 2>/dev/null | sed 's/.*chromium-//' | head -1)
    fi
    if [ -n "$want" ] && [ -n "$have" ] && [ "$want" != "$have" ]; then
      echo "  note: playwright wants chromium $want, image has $have"
      echo "        pip install 'playwright==<version shipping $have>' to match"
    fi

    python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 &
    SERVER_PID=$!
    for _ in $(seq 1 40); do
      curl -sf -o /dev/null "http://127.0.0.1:$PORT/index.html" && break
      sleep 0.25
    done

    if curl -sf -o /dev/null "http://127.0.0.1:$PORT/index.html"; then
      # 127.0.0.1 must bypass any HTTPS_PROXY, or the browser cannot reach it.
      if NO_PROXY="127.0.0.1,localhost" no_proxy="127.0.0.1,localhost" \
         E2E_BASE_URL="http://127.0.0.1:$PORT" \
         python3 -m unittest tests.e2e_website_test 2>&1 | tail -4; then
        pass "e2e_website_test against http://127.0.0.1:$PORT"
      else
        fail "e2e_website_test against http://127.0.0.1:$PORT"
      fi
    else
      fail "local server did not come up on :$PORT"
    fi
  fi
fi

# ------------------------------------------------------------------ summary

printf '\n\033[1m== Summary ==\033[0m\n'
if [ ${#FAILED[@]} -eq 0 ]; then
  printf '\033[32mAll local CI checks passed.\033[0m\n'
  exit 0
fi
printf '\033[31m%d check(s) failed:\033[0m\n' "${#FAILED[@]}"
printf '  - %s\n' "${FAILED[@]}"
exit 1
