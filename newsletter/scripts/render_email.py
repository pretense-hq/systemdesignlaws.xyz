#!/usr/bin/env python3
"""Render a newsletter draft (markdown) to email-ready HTML for an ESP's custom-HTML editor.

The comic goes under the title and the infographic goes right before a named H2.
Draft markers ({{PAYWALL}}, {{SUBSCRIBE}}, {{BUTTON:label|url}}, <!-- comments -->) are
resolved for email, and links to our own sites are re-tagged utm_source=newsletter.

Usage:
  render_email.py DRAFT.md OUT.html CAMPAIGN COMIC_URL|- INFOGRAPHIC_URL "H2 to place it before"
"""
import re
import sys

import markdown

OWN_SITES = ("pretense.ai", "systemdesignlaws")
UNSUBSCRIBE = "{{ unsubscribe }}"


def image(url, alt):
    return (f'<p style="margin:20px 0"><img src="{url}" alt="{alt}" width="600" '
            f'style="display:block;width:100%;max-width:600px;height:auto;border:0"></p>')


def tag_link(url, campaign):
    if not any(site in url for site in OWN_SITES):
        return url
    if "utm_source=" in url:
        url = re.sub(r"utm_source=[^&\"]+", "utm_source=newsletter", url)
        return re.sub(r"utm_medium=[^&\"]+", "utm_medium=email", url)
    sep = "&amp;" if "?" in url else "?"
    return f"{url}{sep}utm_source=newsletter&amp;utm_medium=email&amp;utm_campaign={campaign}"


def render(md, campaign, comic, infographic, before):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    md = md.replace("{{PAYWALL}}", "").replace("{{SUBSCRIBE}}", "")
    md = re.sub(r"\{\{BUTTON:([^|]+)\|([^}]+)\}\}", r"[\1](\2)", md)
    md = re.sub(r"^>> ", "> ", md, flags=re.M)
    # markdown needs a blank line before a list that follows a paragraph line
    md = re.sub(r"(?m)^(?!\s*[-*] |\s*\d+\. )(.+)\n(\s*[-*] |\s*\d+\. )", r"\1\n\n\2", md)
    title = re.search(r"^# (.+)$", md, re.M).group(1).strip()
    md = re.sub(r"^# .+\n", "", md, count=1, flags=re.M)
    md = re.sub(r"(?<![(<\[])(https?://[^\s)]+)", r"<\1>", md)
    body = markdown.markdown(md, extensions=["extra"])
    body = re.sub(r'href="([^"]+)"', lambda m: f'href="{tag_link(m.group(1), campaign)}"', body)
    heading = f"<h2>{before}</h2>"
    if heading not in body:
        raise ValueError(f"heading not found: {before}")
    body = body.replace(heading, image(infographic, before) + heading, 1)
    body = body.replace("<blockquote>",
                        '<blockquote style="border-left:3px solid #ccc;margin:0;padding-left:12px;color:#444">')
    top = image(comic, title) if comic != "-" else ""
    return (
        '<!doctype html><html><body style="margin:0;background:#f6f6f4">'
        '<div style="max-width:640px;margin:0 auto;padding:24px 20px;background:#fff;'
        'font:16px/1.6 Georgia,serif;color:#1a1a1a">\n'
        '<p style="font:13px Arial,sans-serif;color:#666">System Design Laws</p>'
        f'<h1 style="font-size:28px;line-height:1.2">{title}</h1>\n'
        f"{top}\n{body}\n"
        '<p style="font:12px Arial,sans-serif;color:#888;margin-top:32px">You get this because you '
        f'subscribed at systemdesignlaws.xyz. <a href="{UNSUBSCRIBE}">Unsubscribe</a></p>'
        "</div></body></html>"
    )


def main(argv):
    if len(argv) != 7:
        sys.exit(__doc__)
    src, out, campaign, comic, infographic, before = argv[1:7]
    html = render(open(src, encoding="utf-8").read(), campaign, comic, infographic, before)
    non_ascii = sorted({c for c in html if ord(c) > 126})
    open(out, "w", encoding="utf-8").write(html)
    print(f"{out}: {len(html)} bytes, imgs={html.count('<img ')}, links={html.count('href=')}, "
          f"non_ascii={non_ascii}")


if __name__ == "__main__":
    main(sys.argv)
