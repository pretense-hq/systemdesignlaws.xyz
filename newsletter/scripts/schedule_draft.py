#!/usr/bin/env python3
"""
Schedule a Substack draft to publish at a future time, instead of immediately.

Usage:
  python schedule_draft.py --draft my-article.md --at 2026-08-25T09:00:00-07:00
  python schedule_draft.py --draft-id 190979284 --at "2026-08-25 09:00" --assume-utc
  python schedule_draft.py --draft-id 190979284 --unschedule

Why this exists
---------------
The pipeline could only create-then-publish-now. That forces every article out
the moment it is finished, so a 50-topic backlog either goes out in a burst or
waits on someone being at a keyboard at the right hour. Scheduling turns the
backlog into a cadence.

Backed by `Api.schedule_draft(draft, draft_datetime)` in python-substack, which
POSTs `trigger_at` to /drafts/{id}/scheduled_release.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


class ScheduleTimeError(ValueError):
    """Raised when the requested publish time cannot be used."""


def parse_when(raw: str, now: datetime, assume_utc: bool = False) -> datetime:
    """
    Parse a requested publish time into an aware datetime.

    Pure and side-effect free so it can be unit tested without a Substack
    session. `now` is passed in rather than read from the clock for the same
    reason.

    A naive timestamp is rejected unless `assume_utc` is set. Guessing a
    timezone is how a newsletter goes out at 2am to the wrong continent, and
    the failure is silent: the call succeeds and the mistake only shows up in
    the send.

    A time in the past is rejected outright. Substack treats an elapsed
    trigger as "publish now", so a typo in the year would send immediately to
    the whole list with no undo.
    """
    text = raw.strip()
    # Accept "2026-08-25 09:00" as well as full ISO 8601.
    try:
        when = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ScheduleTimeError(
            f"Could not parse {raw!r}. Use ISO 8601, e.g. 2026-08-25T09:00:00-07:00"
        ) from exc

    if when.tzinfo is None:
        if not assume_utc:
            raise ScheduleTimeError(
                f"{raw!r} has no timezone. Add an offset (e.g. -07:00) or pass "
                f"--assume-utc. Guessing sends the newsletter at the wrong hour."
            )
        when = when.replace(tzinfo=timezone.utc)

    if when <= now:
        raise ScheduleTimeError(
            f"{when.isoformat()} is not in the future (now {now.isoformat()}). "
            f"Substack publishes an elapsed schedule immediately."
        )

    return when


def load_session():
    """Load session from .env or persisted cookies."""
    env_path = Path(__file__).parent / ".env"
    cookies_path = Path(__file__).parent / ".substack-cookies.json"
    if cookies_path.exists():
        return {"cookies_path": str(cookies_path)}
    if not env_path.exists():
        print("No session. Create newsletter/scripts/.env with SUBSTACK_COOKIES")
        sys.exit(1)
    env = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    cookies_str = env.get("SUBSTACK_COOKIES")
    if not cookies_str and env.get("SUBSTACK_SID") and env.get("CONNECT_SID"):
        cookies_str = f"substack.sid={env['SUBSTACK_SID']}; connect.sid={env['CONNECT_SID']}"
    if not cookies_str:
        print("Missing SUBSTACK_COOKIES or SUBSTACK_SID+CONNECT_SID in .env")
        sys.exit(1)
    return {"cookies_string": cookies_str}


def resolve_draft_id(args) -> int:
    """Draft id from --draft-id, or from published/<slug>.json written by create_draft.py."""
    if args.draft_id:
        return int(args.draft_id)
    slug = Path(args.draft).stem
    pub_file = Path(__file__).resolve().parent.parent / "published" / f"{slug}.json"
    if not pub_file.exists():
        print(f"No published/{slug}.json. Run create_draft.py first or pass --draft-id")
        sys.exit(1)
    return int(json.loads(pub_file.read_text())["draft_id"])


def main():
    parser = argparse.ArgumentParser(
        description="Schedule a Substack draft for future publication"
    )
    parser.add_argument("--draft", help="Draft markdown filename")
    parser.add_argument("--draft-id", help="Substack draft id")
    parser.add_argument("--at", help="Publish time, ISO 8601")
    parser.add_argument(
        "--assume-utc",
        action="store_true",
        help="Treat a timestamp with no offset as UTC instead of refusing it",
    )
    parser.add_argument(
        "--unschedule",
        action="store_true",
        help="Cancel an existing schedule and return the post to draft",
    )
    args = parser.parse_args()

    if not args.draft and not args.draft_id:
        print("Provide --draft or --draft-id")
        sys.exit(1)
    if not args.unschedule and not args.at:
        print("Provide --at, or --unschedule to cancel")
        sys.exit(1)

    # Validate the time BEFORE opening a session, so a typo costs nothing.
    when = None
    if not args.unschedule:
        try:
            when = parse_when(args.at, datetime.now(timezone.utc), args.assume_utc)
        except ScheduleTimeError as exc:
            print(f"Error: {exc}")
            sys.exit(1)

    from substack import Api  # imported late: keeps --help working without the dep

    session = load_session()
    api = Api(**session)
    draft_id = resolve_draft_id(args)

    base = str(
        getattr(api, "publication_url", "https://jimmymalhan.substack.com")
    ).replace("https://", "").replace("http://", "").split("/")[0]
    edit_url = f"https://{base}/publish/post/{draft_id}"

    if args.unschedule:
        try:
            api.unschedule_draft(draft_id)
            print(f"Unscheduled draft {draft_id}. It is a draft again.")
        except Exception as e:
            print(f"Unschedule failed: {e}")
            sys.exit(1)
        print(f"Edit URL: {edit_url}")
        return

    try:
        api.schedule_draft(draft_id, when)
    except Exception as e:
        print(f"Schedule failed: {e}")
        sys.exit(1)

    print(f"Scheduled draft {draft_id} for {when.isoformat()}")
    print(f"  ({when.astimezone(timezone.utc).isoformat()} UTC)")
    print(f"Edit URL: {edit_url}")
    print("\nNot published yet. Substack sends it at the time above.")
    print("Cancel with: --draft-id %s --unschedule" % draft_id)


if __name__ == "__main__":
    main()
