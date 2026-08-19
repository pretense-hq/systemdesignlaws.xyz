#!/usr/bin/env python3
"""
Tests for schedule time parsing in newsletter/scripts/schedule_draft.py.

Pure datetime assertions - no Substack session, no network - so this runs
under plain `python3 -m unittest discover -s tests`.

The two rules worth guarding are both about sends that cannot be undone:

  1. A naive timestamp is refused. Guessing a timezone is how a newsletter
     goes out at 2am to the wrong continent, and the failure is silent - the
     call succeeds and the mistake only surfaces in the send.
  2. A past timestamp is refused. Substack publishes an elapsed schedule
     immediately, so a typo in the year would blast the whole list with no
     undo.

Run: python3 -m unittest tests.test_schedule_draft -v
"""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "newsletter" / "scripts"))

from schedule_draft import ScheduleTimeError, parse_when  # noqa: E402

NOW = datetime(2026, 8, 19, 12, 0, 0, tzinfo=timezone.utc)


class TestParseWhen(unittest.TestCase):
    def test_accepts_iso_with_offset(self):
        when = parse_when("2026-08-25T09:00:00-07:00", NOW)
        self.assertEqual(when.utcoffset(), timedelta(hours=-7))
        self.assertEqual(when.astimezone(timezone.utc).hour, 16)

    def test_accepts_iso_with_z_style_utc(self):
        when = parse_when("2026-08-25T09:00:00+00:00", NOW)
        self.assertEqual(when.astimezone(timezone.utc).hour, 9)

    def test_rejects_naive_timestamp_by_default(self):
        # The silent-wrong-hour case.
        with self.assertRaises(ScheduleTimeError) as ctx:
            parse_when("2026-08-25 09:00", NOW)
        self.assertIn("timezone", str(ctx.exception))

    def test_assume_utc_opts_in_to_naive(self):
        when = parse_when("2026-08-25 09:00", NOW, assume_utc=True)
        self.assertEqual(when.tzinfo, timezone.utc)
        self.assertEqual(when.hour, 9)

    def test_rejects_a_time_in_the_past(self):
        # Substack treats an elapsed trigger as "publish now".
        with self.assertRaises(ScheduleTimeError) as ctx:
            parse_when("2020-01-01T09:00:00+00:00", NOW)
        self.assertIn("future", str(ctx.exception))

    def test_rejects_a_mistyped_year_in_the_past(self):
        # The realistic version of the above: 2025 instead of 2026.
        with self.assertRaises(ScheduleTimeError):
            parse_when("2025-08-25T09:00:00+00:00", NOW)

    def test_rejects_exactly_now(self):
        with self.assertRaises(ScheduleTimeError):
            parse_when(NOW.isoformat(), NOW)

    def test_accepts_one_minute_from_now(self):
        soon = (NOW + timedelta(minutes=1)).isoformat()
        self.assertEqual(parse_when(soon, NOW), NOW + timedelta(minutes=1))

    def test_rejects_unparseable_input(self):
        for bad in ["next tuesday", "", "2026-13-45T00:00:00+00:00", "soon"]:
            with self.assertRaises(ScheduleTimeError, msg=f"{bad!r} should raise"):
                parse_when(bad, NOW)

    def test_surrounding_whitespace_is_tolerated(self):
        when = parse_when("  2026-08-25T09:00:00+00:00  ", NOW)
        self.assertEqual(when.astimezone(timezone.utc).hour, 9)


if __name__ == "__main__":
    unittest.main()
