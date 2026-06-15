#!/usr/bin/env python3
"""
List all published and draft posts on Substack.
Used to check for existing articles before creating duplicates.

Usage:
  python list_posts.py              # List all posts (drafts + published)
  python list_posts.py --published  # Only published posts
  python list_posts.py --drafts     # Only drafts
  python list_posts.py --search "scaling reads"  # Search by title
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


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


def get_publication_url():
    """Read SUBSTACK_PUBLICATION from .env."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return None
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if "SUBSTACK_PUBLICATION" in line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                if k.strip() == "SUBSTACK_PUBLICATION" and v.strip():
                    return v.strip().strip('"').strip("'")
    return None


def _normalize_for_match(text):
    """Normalize title for matching: lower, replace hyphens with spaces, split into words."""
    if not text:
        return set()
    t = (text or "").lower().strip().replace("-", " ")
    return set(t.split())


def _as_post_list(resp):
    """Normalize a Substack list response into a list of post/draft dicts.

    The API returns either a bare list (older shape) or a dict like
    {"posts": [...], "hasMore": bool, "nextCursor": str}. Iterating the dict
    directly yields its string KEYS, which is what caused the silent
    'str object has no attribute get' failure in the anti-duplicate guard.
    Always pull the embedded list and drop any non-dict entries.
    """
    if resp is None:
        return []
    if isinstance(resp, list):
        return [x for x in resp if isinstance(x, dict)]
    if isinstance(resp, dict):
        items = resp.get("posts") or resp.get("drafts") or []
        return [x for x in items if isinstance(x, dict)]
    return []


def _fetch_all_drafts(api):
    """Return every draft (dicts), following cursor pagination.

    The library's get_drafts(offset, limit) returns HTTP 400 on this account,
    so we page via the publication 'drafts' endpoint using nextCursor and fall
    back to the library's single-page call if the raw request is unavailable.
    """
    out, seen, cursor = [], set(), None
    for _ in range(50):  # hard cap; never loop forever
        data = None
        try:
            params = {"cursor": cursor} if cursor else {}
            r = api._session.get(f"{api.publication_url}/drafts", params=params)
            if r.status_code == 200:
                data = r.json()
        except Exception:
            data = None
        if data is None:
            data = api.get_drafts()  # single-page fallback
        for d in _as_post_list(data):
            if d.get("id") not in seen:
                seen.add(d.get("id"))
                out.append(d)
        if not (isinstance(data, dict) and data.get("hasMore") and data.get("nextCursor")):
            break
        cursor = data.get("nextCursor")
    return out


class DuplicateCheckError(Exception):
    """Raised when the anti-duplicate lookup could not complete and a
    'no duplicate' answer would be a false negative. Callers MUST treat this
    as inconclusive and refuse to create a new post (fail-closed)."""


def find_existing_post(api, title_query, check_drafts=True, check_published=True):
    """
    Search for an existing post by title similarity.
    If article exists (draft or published): return (id, type, title) so caller can UPDATE instead of create.
    Normalizes hyphens so "Real-time Updates" matches "real time updates" from slug.
    Returns (post_id, post_type, post_title) or (None, None, None).
    Raises DuplicateCheckError if a requested listing failed AND no match was
    found, so a transient API error never gets reported as "no duplicate".
    """
    query_words = _normalize_for_match(title_query)
    query_lower = (title_query or "").lower().strip().replace("-", " ")

    matches = []
    drafts_failed = False
    posts_failed = False

    if check_drafts:
        try:
            drafts = _fetch_all_drafts(api)
            for d in drafts:
                d_title = d.get("draft_title") or d.get("title") or ""
                d_words = _normalize_for_match(d_title)
                overlap = len(query_words & d_words)
                # Match if: good word overlap, or query is substring of normalized title
                if overlap >= max(1, min(len(query_words), len(d_words)) // 2) or query_lower in (d_title or "").lower().replace("-", " "):
                    matches.append((d.get("id"), "draft", d_title or "Untitled", overlap))
        except Exception as e:
            drafts_failed = True
            print(f"Warning: Could not fetch drafts: {e}")

    if check_published:
        try:
            posts = _as_post_list(api.get_posts())
            for p in posts:
                p_title = p.get("title") or ""
                p_words = _normalize_for_match(p_title)
                overlap = len(query_words & p_words)
                if overlap >= max(1, min(len(query_words), len(p_words)) // 2) or query_lower in (p_title or "").lower().replace("-", " "):
                    matches.append((p.get("id"), "published", p_title or "Untitled", overlap))
        except Exception as e:
            posts_failed = True
            print(f"Warning: Could not fetch posts: {e}")

    if matches:
        matches.sort(key=lambda x: x[3], reverse=True)
        best = matches[0]
        return best[0], best[1], best[2]

    # No match found. If a requested source failed to load, we cannot be sure
    # there is no duplicate -> signal inconclusive instead of returning None.
    if (check_drafts and drafts_failed) or (check_published and posts_failed):
        raise DuplicateCheckError(
            "could not load existing posts (drafts_failed=%s, posts_failed=%s)"
            % (drafts_failed, posts_failed)
        )

    return None, None, None


def main():
    parser = argparse.ArgumentParser(description="List Substack posts")
    parser.add_argument("--published", action="store_true", help="Only published posts")
    parser.add_argument("--drafts", action="store_true", help="Only drafts")
    parser.add_argument("--search", type=str, help="Search by title")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    try:
        from substack import Api
    except ImportError:
        print("Install: pip install python-substack")
        sys.exit(1)

    session = load_session()
    publication = get_publication_url()
    api = Api(**session) if publication is None else Api(publication_url=publication, **session)

    try:
        api.get_user_id()
    except Exception:
        print("Session expired. Paste fresh cookies into newsletter/scripts/.env")
        sys.exit(1)

    if args.search:
        try:
            post_id, post_type, post_title = find_existing_post(
                api, args.search,
                check_drafts=not args.published,
                check_published=not args.drafts
            )
        except DuplicateCheckError as e:
            print(f"INCONCLUSIVE: could not determine if '{args.search}' exists ({e})")
            sys.exit(2)
        if post_id:
            print(f"Found {post_type}: [{post_id}] {post_title}")
        else:
            print(f"No match for: {args.search}")
        return

    results = []

    if not args.published:
        try:
            drafts = _fetch_all_drafts(api)
            for d in drafts:
                item = {
                    "id": d.get("id"),
                    "type": "draft",
                    "title": d.get("draft_title") or d.get("title", "Untitled"),
                    "slug": d.get("slug", ""),
                }
                results.append(item)
        except Exception as e:
            print(f"Warning: Could not fetch drafts: {e}")

    if not args.drafts:
        try:
            posts = _as_post_list(api.get_posts())
            for p in posts:
                item = {
                    "id": p.get("id"),
                    "type": "published",
                    "title": p.get("title", "Untitled"),
                    "slug": p.get("slug", ""),
                }
                results.append(item)
        except Exception as e:
            print(f"Warning: Could not fetch posts: {e}")

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            tag = "DRAFT" if r["type"] == "draft" else "PUB"
            print(f"  [{tag}] {r['id']} - {r['title']}")
        print(f"\nTotal: {len(results)} posts")


if __name__ == "__main__":
    main()
