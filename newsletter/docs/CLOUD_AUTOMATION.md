# Cloud Weekly Auto-Publish (GitHub Actions)

The newsletter is produced and published **in the cloud** by the **Weekly Publish** GitHub
Actions workflow. Nothing runs on anyone's laptop. Any org member with repo access can trigger
and monitor it.

- Workflow: `.github/workflows/weekly-publish.yml`
- Orchestration prompt: `.github/automation/orchestrate-weekly.md`
- Runner: `.github/scripts/run_weekly_ci.sh`

## What it does

Every **Sunday 18:00 IST (12:30 UTC)** it runs an unattended Claude Code agent that:
1. Picks the first `queued` topic from `newsletter/backlog.json` (curriculum order).
2. Runs the anti-duplicate guard (`list_posts.py`) — never duplicates a live post.
3. Writes the article + diagrams (reusing existing SVGs in `newsletter/plots/svg/` where possible).
4. Validates it (`tests.test_draft_body_structure`).
5. **Publishes live to Substack and emails all subscribers**, then marks the backlog entry
   `published` and commits the change back to the repo.

## Run modes

| Mode | What happens | When |
|------|--------------|------|
| `publish` | Full run: write → publish live → email subscribers | The scheduled Sunday run |
| `draft` | Write + validate only. **Never publishes, never emails.** Ends `DRAFT_READY:` | Safe manual test |

A manual run defaults to **`draft`** for safety. The scheduled run always uses `publish`.

## How any org member runs it

**From the GitHub UI:** Repo → **Actions** tab → **Weekly Publish** → **Run workflow** → choose
`draft` (safe) or `publish` → **Run workflow**. Watch the run; the summary shows the outcome and
a `weekly-run-log` artifact has the full log.

**From the CLI:**
```bash
gh workflow run weekly-publish.yml -f mode=draft        # safe test, nothing published
gh workflow run weekly-publish.yml -f mode=publish      # publishes live + emails
gh run watch                                            # follow the latest run
```

## Required secrets (repo settings → Secrets and variables → Actions)

| Secret | Purpose | Status |
|--------|---------|--------|
| `SUBSTACK_COOKIES` | Substack session (`substack.sid=...`) for anti-dup + publish | set |
| `ANTHROPIC_API_KEY` | Claude Code auth (pay-per-token) | **must be added** |

Add the API key once:
```bash
gh secret set ANTHROPIC_API_KEY   # paste the key when prompted
```

## When a run reports AUTH FAILURE (cookie expired)

The Substack session cookie expires periodically. When it does, the run ends with
`AUTH_FAILURE` and nothing is published. Refresh it:
1. Log in to https://substack.com, DevTools → Application → Cookies → copy the `substack.sid` value.
2. `printf 'substack.sid=%s' '<value>' | gh secret set SUBSTACK_COOKIES`
3. Re-run the workflow (`mode=publish`) if you want this week's post out.

## Cost

Each run is a full Claude Code agent writing an article (significant tokens, billed to
`ANTHROPIC_API_KEY`). Budget for one such run per week, plus any manual `draft` tests.

## Pause / resume the schedule

- **Pause:** Actions tab → Weekly Publish → `...` menu → **Disable workflow**.
- **Resume:** same menu → **Enable workflow**.
- The cron line in `weekly-publish.yml` controls timing (`30 12 * * 0`).

## Review-first instead of auto-publish?

Run `mode=draft` manually (or change the scheduled default) — it writes the draft and stops, so
a human can review `newsletter/drafts/<slug>.md` and publish with
`newsletter/scripts/publish_draft.py` when ready.
