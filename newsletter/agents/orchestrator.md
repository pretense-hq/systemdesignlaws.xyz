# Newsletter Orchestrator Agent

Coordinates the newsletter production pipeline. Picks topics, assigns work, tracks status.

## Core Rules (ENFORCED AT EVERY STEP)

- **Original content:** All articles are original. No external attribution or copied content.
- **25 diagrams:** Every article must have 20-25 Excalidraw diagrams. Reject if fewer than 20.
- **Never delete published articles:** Always edit existing posts. Never create duplicates.
- **Anti-duplicate:** Always check `list_posts.py --search` before creating. Edit existing, never create duplicates.
- **Progress bars:** All batch operations must show real-time ASCII progress bars (current/total, percentage, filename).
- **Adaptive rate limiting:** Slow at 70% capacity (3x delay), 90% (5x delay), 95% (heavy pause). NEVER hit 100%. Checkpoint/resume on failure.

## Execution modes

This spec describes two ways the pipeline runs. Both follow the same content rules; they differ in how status transitions are recorded.

### Interactive mode (local)

A human drives the session and each agent role is exercised step by step. Backlog status moves through every intermediate state:

```
queued -> drafting -> review -> published
```

- Status is updated to `drafting` when the topic is handed to the Researcher.
- Status is updated to `review` after Writer + Editor + Verifier complete.
- Status is updated to `published` after the Scheduler pushes to Substack.

### Automated CI mode (GitHub Actions)

The weekly workflow runs the entire pipeline as a single automated invocation driven by `.github/automation/orchestrate-weekly.md`. The agent files in `newsletter/agents/` are read as prose guidance in one pass; the six roles are not separately dispatched. Because the run is atomic, the intermediate `drafting` and `review` states are not persisted:

```
queued -> published   (on success, single transition)
queued -> queued      (on failure, no change; error is reported)
```

The CI run must never leave a topic stuck in `drafting` or `review`. Either the topic completes and becomes `published`, or the backlog entry is left untouched at `queued`.

## Workflow

1. Read `newsletter/backlog.json`
2. **Check for existing articles** - Run `list_posts.py --search "[title]"` to see if this topic is already published/drafted on Substack
3. If existing: **UPDATE** the existing post, do not create a duplicate
4. If new: Pick the next topic with `"status": "queued"` (follow section order: Introduction -> Core Concepts -> Key Technologies -> Question Breakdowns -> Patterns -> Advanced Topics)
5. Interactive mode only: update status to `"drafting"`
6. Pass topic info to Researcher: title, curriculum_path, slug
7. Interactive mode only: after Writer + Editor + Verifier complete, update status to `"review"`
8. After Scheduler pushes to Substack, update status to `"published"` with draft_file and published_url (both modes)

## Duplicate prevention

- **Always check existing posts before creating** (via `list_posts.py` or `backlog.json`)
- If a similar article already exists on Substack (by title match), update it
- `create_draft.py` auto-detects duplicates unless `--force-new` is passed

## Topic selection rules

- Follow curriculum order within each section
- Core Concepts before Key Technologies before Question Breakdowns
- Skip topics with status `"drafting"`, `"review"`, or `"published"`
- If all topics in a section are done, move to the next section

## Status transitions

```
Interactive:  queued -> drafting -> review -> published
Automated CI: queued -> published (single run)
```

## On feedback received

When user provides feedback at any stage:
1. **Immediately** save to `newsletter/docs/FEEDBACK_LOG.md`
2. Cascade to all affected files (skills, agents, verifiers, TALK_RULES, WORKFLOW, ARTICLE_TEMPLATE)
3. Apply the correction to the current work
4. Verify the fix passes all verifiers

## On failure

- If Researcher cannot fetch the remote curriculum page, the Researcher falls back to the topic's entry in the local `newsletter/curriculum.md` (see researcher.md). Only if the topic also has no local curriculum entry: log error and skip to next topic
- If Writer draft fails verification, return to Writer with verifier feedback
- If Scheduler fails (expired session), pause and flag for human intervention

## Inputs

- `newsletter/backlog.json` - topic list with status
- `newsletter/curriculum.md` - reference for section order

## Outputs

- Updated `newsletter/backlog.json` with new status
- Coordination messages to Researcher, Writer, Editor, Verifier, Scheduler
