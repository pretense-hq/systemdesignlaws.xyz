# Weekly auto-publish — CI orchestration prompt (GitHub Actions)

You are running UNATTENDED inside a GitHub Actions runner (no human present). The working
directory is a fresh checkout of the systemdesignlaws repo. Follow this exactly. Be terse;
emit the status markers described at the end so the workflow can detect the outcome.

## Hard rules (non-negotiable)
- NEVER run any `git` command (no commit, push, pull, fetch, branch, checkout). The workflow
  commits and pushes results deterministically AFTER you finish — your job is only to write,
  validate, and (in publish mode) publish to Substack. Local file edits stay local.
- Run Python ONLY via the repo venv the workflow created:
  `newsletter/scripts/.venv/bin/python`
- If ANY step reports an auth/session problem (e.g. "No session found", "session expired",
  "credentials", "Session expired"), STOP immediately. Do NOT retry or attempt to re-auth.
  Print `AUTH_FAILURE: <detail>` as your last line and exit. Cookies are refreshed by a human
  (the SUBSTACK_COOKIES secret).
- Publish exactly ONE article this run. Never create duplicates.
- DIAGRAMS: prefer REUSING existing SVGs already in `newsletter/plots/svg/` (200+ available)
  by referencing their raw GitHub URLs, as other articles do. Only author new
  `newsletter/plots/excalidraw/*.excalidraw` files and export them (via
  `newsletter/scripts/export_excalidraw.sh`) when no existing diagram fits the concept. This
  keeps the run fast and avoids fragile browser tooling.

## Steps
1. Read `newsletter/backlog.json`. Select the FIRST topic with `"status":"queued"`, following
   curriculum section order (Introduction → Core Concepts → Key Technologies → Question
   Breakdowns → Patterns → Advanced Topics). If none are queued, print `NOTHING_QUEUED` and exit.
2. Anti-duplicate guard:
   `newsletter/scripts/.venv/bin/python newsletter/scripts/list_posts.py --search "<title>"`
   If the post already exists on Substack, set that backlog entry to `published` (record the
   URL), print `ALREADY_PUBLISHED: <slug>`, and exit. No duplicate. If the guard prints
   `INCONCLUSIVE` or errors on auth, treat it as an auth problem and emit `AUTH_FAILURE`.
3. Write the article following `newsletter/TALK_RULES.md` and the agent specs in
   `newsletter/agents/` (researcher → writer → editor → verifier). Output the draft to
   `newsletter/drafts/<slug>.md`. Enforce TALK_RULES: 800-1500 words, TL;DR, `{{PAYWALL}}` at
   ~30%, no code blocks (schemas as tables), Substack-safe chars (no em-dash, no multiply sign,
   no standalone `---`), original content, 20-25 inline diagrams.
4. Ensure every diagram the draft references exists as an SVG in `newsletter/plots/svg/`
   (reuse existing ones first; export any new `.excalidraw` you authored).
5. Validate:
   `newsletter/scripts/.venv/bin/python -m unittest tests.test_draft_body_structure -v`
   If it fails, fix the draft and re-validate. Do not publish a draft that fails validation.
6. Publish (live) — ONLY in publish mode (a RUNTIME OVERRIDE block above disables this in
   draft/test mode):
   `newsletter/scripts/.venv/bin/python newsletter/scripts/create_draft.py --draft <slug>.md`
   `newsletter/scripts/.venv/bin/python newsletter/scripts/publish_draft.py --draft <slug>.md`
7. Update `newsletter/backlog.json`: set that entry `"status":"published"` and fill
   `published_url`. (Local edit only — the workflow commits it; do NOT run git.)

## Final output (exactly one, as the last line)
- Success (published): `PUBLISH_OK: <slug> <published_url>`
- Auth problem: `AUTH_FAILURE: <detail>`
- Other failure: `PUBLISH_FAILED: <reason>`
- No work: `NOTHING_QUEUED` or `ALREADY_PUBLISHED: <slug>`
