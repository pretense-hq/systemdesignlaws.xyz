#!/usr/bin/env python3
"""Fetch latest 15 posts from Substack RSS and write recent-posts.json."""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import xml.etree.ElementTree as ET

RSS_PATH = Path("feed.xml")
OUTPUT_PATH = Path("recent-posts.json")
LIMIT = 15
DESC_MAX_LEN = 140


def strip_html(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def get_text(element) -> str:
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def parse_rss_to_posts(rss_path: Path, limit: int = LIMIT, desc_max: int = DESC_MAX_LEN) -> list:
    """Parse RSS XML and return list of post dicts (title, url, description).

    Raises ValueError if the file is missing, is not well-formed XML, or is
    not an RSS feed (e.g. the feed URL redirected to an HTML page).
    """
    if not rss_path.exists():
        raise ValueError(f"Feed file not found: {rss_path}. Did the curl download step fail?")
    try:
        tree = ET.parse(rss_path)
    except ET.ParseError as exc:
        snippet = rss_path.read_text(errors="replace").lstrip()[:80]
        raise ValueError(
            f"{rss_path} is not well-formed XML ({exc}). "
            f"File starts with: {snippet!r}. "
            "The feed URL may have redirected to an HTML page instead of the RSS feed; "
            "verify the URL still serves application/xml."
        ) from exc
    root = tree.getroot()
    if root.tag.split("}")[-1] not in ("rss", "feed"):
        raise ValueError(
            f"{rss_path} parsed as XML but root element is <{root.tag}>, not <rss> or <feed>. "
            "This does not look like an RSS/Atom feed; the feed URL may be serving the wrong content."
        )
    items = root.findall(".//item")[:limit]
    posts = []
    for item in items:
        title = get_text(item.find("title"))
        link_el = item.find("link")
        link = link_el.text.strip() if link_el is not None and link_el.text else ""
        desc_raw = get_text(item.find("description"))
        desc = strip_html(desc_raw)
        if len(desc) > desc_max:
            desc = desc[: desc_max - 3].rsplit(" ", 1)[0] + "..."
        if title and link:
            # Use systemdesignlaws.substack.com for post URLs (newsletter.* returns 404 for /p/ paths)
            url = link.replace("newsletter.systemdesignlaws.xyz", "systemdesignlaws.substack.com")
            posts.append({"title": title, "url": url, "description": desc or "Read more."})
    return posts


def main():
    try:
        posts = parse_rss_to_posts(RSS_PATH)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    if not posts:
        print(
            f"ERROR: No posts found in {RSS_PATH}. Refusing to overwrite "
            f"{OUTPUT_PATH} with an empty list; the feed may be broken.",
            file=sys.stderr,
        )
        sys.exit(1)
    output = {
        "posts": posts,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Wrote {len(posts)} posts to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
