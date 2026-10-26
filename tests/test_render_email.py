"""Tests for newsletter/scripts/render_email.py (draft markdown -> ESP custom-HTML email)."""
import importlib.util
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("render_email", REPO / "newsletter" / "scripts" / "render_email.py")
render_email = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(render_email)

DRAFT = """# Design a Rate Limiter

**TL;DR** - Keep counters in sharded Redis.

>> 30-second version: "One atomic check per request."

{{PAYWALL}}

## Requirements
Functional:
- Per-client limits
- Clear 429 responses

<!-- DIAGRAM: internal note -->

## High-Level Design

Read the [docs](https://pretense.ai/?utm_source=substack&utm_medium=newsletter&utm_campaign=x) and https://example.com/spec

{{SUBSCRIBE}}

{{BUTTON:Read More Articles|https://newsletter.systemdesignlaws.xyz}}
"""

COMIC = "https://cdn.example/comic.png"
INFO = "https://cdn.example/info.png"


class RenderEmailTest(unittest.TestCase):
    def setUp(self):
        self.html = render_email.render(DRAFT, "sdl-test", COMIC, INFO, "High-Level Design")

    def test_title_moves_to_h1_once(self):
        self.assertIn('<h1 style="font-size:28px;line-height:1.2">Design a Rate Limiter</h1>', self.html)
        self.assertEqual(self.html.count("Design a Rate Limiter</h1>"), 1)

    def test_comic_under_title_and_infographic_before_named_heading(self):
        self.assertEqual(self.html.count("<img "), 2)
        self.assertLess(self.html.index(COMIC), self.html.index("<h2>Requirements</h2>"))
        info_at = self.html.index(INFO)
        self.assertLess(self.html.index("<h2>Requirements</h2>"), info_at)
        self.assertLess(info_at, self.html.index("<h2>High-Level Design</h2>"))

    def test_comic_can_be_skipped(self):
        html = render_email.render(DRAFT, "sdl-test", "-", INFO, "High-Level Design")
        self.assertNotIn(COMIC, html)
        self.assertEqual(html.count("<img "), 1)

    def test_missing_heading_is_an_error(self):
        with self.assertRaises(ValueError):
            render_email.render(DRAFT, "sdl-test", COMIC, INFO, "No Such Section")

    def test_markers_and_comments_resolved(self):
        for marker in ("{{PAYWALL}}", "{{SUBSCRIBE}}", "{{BUTTON", "DIAGRAM"):
            self.assertNotIn(marker, self.html)
        self.assertIn('href="https://newsletter.systemdesignlaws.xyz?utm_source=newsletter', self.html)
        self.assertIn(">Read More Articles</a>", self.html)

    def test_own_links_retagged_for_email_and_others_untouched(self):
        self.assertIn("pretense.ai/?utm_source=newsletter&amp;utm_medium=email&amp;utm_campaign=x", self.html)
        self.assertNotIn("utm_source=substack", self.html)
        self.assertIn('href="https://example.com/spec"', self.html)

    def test_list_after_paragraph_renders_as_list(self):
        self.assertIn("<li>Per-client limits</li>", self.html)

    def test_unsubscribe_link_and_ascii_only(self):
        self.assertIn('<a href="{{ unsubscribe }}">Unsubscribe</a>', self.html)
        self.assertEqual(sorted({c for c in self.html if ord(c) > 126}), [])


if __name__ == "__main__":
    unittest.main()
