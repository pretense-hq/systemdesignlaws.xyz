# Newsletter Scheduler Agent

Pushes verified drafts to Substack and either schedules them for a future
send or publishes them now. Nothing is left sitting as a forgotten draft.

**Scheduling is the default.** Publishing the instant an article is finished
forces the whole backlog out in bursts and pins the send time to whenever
someone happened to be at a keyboard. With 50 topics queued, that is the
difference between a cadence and a flood.

## Core Rules (ENFORCED AT EVERY STEP)

- **Never delete published articles.** Always edit. If article exists, update it. Never create duplicates.
- **Never leave a forgotten draft.** Every draft pushed must end in one of 2
  states: scheduled for a specific future time, or published. A draft in
  neither state is a bug.
- **Prefer scheduled over immediate.** Publish now only when the article is
  time-sensitive or a human asks for it.
- **Never schedule in the past or without a timezone.** `schedule_draft.py`
  refuses both. Substack treats an elapsed schedule as "publish now", so a
  mistyped year sends to the entire list with no undo, and a missing offset
  silently sends at the wrong hour.
- **Original content only:** Curriculum topics. No external attribution.
- **Anti-duplicate:** Always check `list_posts.py --search` before creating. Edit existing, never create duplicates.
- **Progress bars:** All batch operations must show real-time ASCII progress bars (current/total, percentage, filename).
- **Adaptive rate limiting:** Slow at 70% capacity (3x delay), 90% (5x delay), 95% (heavy pause). NEVER hit 100%. Checkpoint/resume on failure. All API calls use `api_call_with_retry()` with `AdaptiveRateLimiter`.
- **Batch image uploads:** Use `--batch-delay` (default 2s). Resume from last checkpoint on failure.

## Process

1. Receive verified draft path from Verifier/Orchestrator
2. Validate the draft passes structure tests
3. Push to Substack using `create_draft.py`
4. Report the edit URL back to Orchestrator
5. Orchestrator updates `backlog.json` status to `published`

## Steps

### 1. Check for existing article

**First:** Open https://newsletter.systemdesignlaws.xyz/ or https://systemdesignlaws.substack.com/archive and verify whether the post already exists on the website.

**Then:** Run `list_posts.py` to confirm via API:
```bash
python3 newsletter/scripts/list_posts.py --search "[article title]"
```

If the post exists on the website: edit the existing post, then publish. Do NOT create a duplicate.

### 2. Validate draft

```bash
python3 -m unittest tests.test_draft_body_structure -v
```

If tests fail, return to Editor with error details. Do not push broken drafts.

### 3. Push to Substack, then schedule (or publish)

```bash
python3 newsletter/scripts/create_draft.py --draft [filename].md
```

Then EITHER schedule it, which is the default:

```bash
python3 newsletter/scripts/schedule_draft.py --draft [filename].md \
  --at 2026-08-25T09:00:00-07:00
```

OR publish immediately, when the piece is time-sensitive or a human asks:

```bash
python3 newsletter/scripts/publish_draft.py --draft [filename].md
```

Cancel a schedule with `schedule_draft.py --draft-id [id] --unschedule`, which
returns the post to draft.

Batch create + publish remains `batch_create_and_publish.py`. Rate limits:
slow at 70% (3x), 90% (5x), 95% (pause).

**Choosing a send time.** One article per week, same weekday, same hour. The
consistency matters more than the specific slot: a reader who knows when it
lands is a reader who opens it.

### 4. Report back

Return to Orchestrator (and display to user):
- draft_file: the filename pushed
- state: `scheduled` or `published`
- scheduled_for: the ISO 8601 send time, when scheduled
- edit_url: the Substack edit URL
- excalidraw_path: `newsletter/plots/excalidraw/[name].excalidraw` for diagram editing
- status: success or failure with error message

**Always output both the Substack edit URL and the Excalidraw diagram path.**

## On failure

- **Session expired:** Print message, flag for human to refresh cookies in `newsletter/scripts/.env`. See `newsletter/scripts/PASTE_CREDENTIALS.md`.
- **Test failure:** Return draft to Editor with specific test errors.
- **API error:** Log error, do not retry automatically. Flag for human review.

## Do not

- Delete published articles. Ever. Edit only.
- Leave a draft neither scheduled nor published
- Schedule without an explicit timezone offset
- Schedule a time that has already passed
- Push drafts that fail structure validation
- Modify draft content (read-only consumer)
- Retry on auth failures (session refresh is manual)
