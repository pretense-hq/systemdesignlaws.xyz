"""Tests for newsletter/scripts/render_prosemirror.py (draft markdown -> Substack draft_body)."""
import importlib.util
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("render_prosemirror", REPO / "newsletter" / "scripts" / "render_prosemirror.py")
rp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rp)

DRAFT = """# Design a Rate Limiter

**TL;DR** - Keep counters in sharded Redis.

>> 30-second version: "One atomic check per request."

{{PAYWALL}}

## Requirements
Functional:
- Per-client limits with `INCR`
- Clear 429 responses

## The Design
Use a [token bucket](https://example.com/a?b=1).

```
local n = redis.call('INCR', KEYS[1])
```

{{SUBSCRIBE}}

{{BUTTON:Read More Articles|https://newsletter.systemdesignlaws.xyz}}
"""
COMIC = "https://cdn.example/c_1092x1092.png"
INFO = "https://cdn.example/i_980x1216.png"


def walk(node):
    yield node
    for child in node.get("content", []):
        yield from walk(child)


class RenderProsemirrorTest(unittest.TestCase):
    def setUp(self):
        self.title, self.doc = rp.convert(DRAFT, COMIC, INFO, "The Design")
        self.top = [n["type"] for n in self.doc["content"]]

    def test_title_is_taken_out_of_the_body(self):
        self.assertEqual(self.title, "Design a Rate Limiter")
        self.assertNotIn("Design a Rate Limiter", json.dumps(self.doc))

    def test_comic_first_and_infographic_right_before_anchor(self):
        self.assertEqual(self.doc["content"][0]["content"][0]["attrs"]["src"], COMIC)
        i = next(k for k, n in enumerate(self.doc["content"])
                 if n["type"] == "heading" and n["content"][0]["text"] == "The Design")
        self.assertEqual(self.doc["content"][i - 1]["content"][0]["attrs"]["src"], INFO)
        self.assertEqual(self.doc["content"][i - 1]["content"][0]["attrs"]["width"], 980)

    def test_markers_become_widgets_and_links(self):
        self.assertEqual(self.top.count("subscribeWidget"), 2)
        s = json.dumps(self.doc)
        self.assertNotIn("{{", s)
        self.assertNotIn("XXSUBXX", s)
        links = [m["attrs"]["href"] for n in walk(self.doc) for m in n.get("marks", []) if m["type"] == "link"]
        self.assertIn("https://newsletter.systemdesignlaws.xyz", links)
        self.assertIn("https://example.com/a?b=1", links)

    def test_lists_code_and_quote_use_substack_node_types(self):
        types = {n["type"] for n in walk(self.doc)}
        self.assertTrue({"bullet_list", "list_item", "code_block", "blockquote", "heading"} <= types)
        code_marks = [n["text"] for n in walk(self.doc) for m in n.get("marks", []) if m["type"] == "code"]
        self.assertEqual(code_marks, ["INCR"])
        # list items hold their text inside a paragraph, as the editor expects
        item = next(n for n in walk(self.doc) if n["type"] == "list_item")
        self.assertEqual(item["content"][0]["type"], "paragraph")

    def test_missing_anchor_is_an_error(self):
        with self.assertRaises(AssertionError):
            rp.convert(DRAFT, COMIC, INFO, "No Such Heading")


if __name__ == "__main__":
    unittest.main()
