"""Newsletter draft markdown -> Substack ProseMirror doc JSON (+ title/subtitle).

Usage: render_prosemirror.py DRAFT.md OUT.json COMIC_URL INFO_URL "H2 before which the infographic goes" SUBTITLE
Comic goes first; {{PAYWALL}} and {{SUBSCRIBE}} become subscribe widgets; {{BUTTON:l|u}} a link paragraph.
"""
import json, os, re, sys
from html.parser import HTMLParser

import markdown

SUB = {"type": "subscribeWidget", "attrs": {"url": "%%checkout_url%%", "text": "Subscribe", "language": "en"},
       "content": [{"type": "ctaCaption", "content": [{"type": "text", "text": "SystemDesignLaws is a reader-supported publication. To receive new posts and support my work, consider becoming a free or paid subscriber."}]}]}
BLOCK = {"p": "paragraph", "h2": "heading", "h3": "heading", "h4": "heading", "ul": "bullet_list", "ol": "ordered_list",
         "li": "list_item", "blockquote": "blockquote"}
MARK = {"strong": "strong", "b": "strong", "em": "em", "i": "em", "code": "code"}


def image(src):
    m = re.search(r"_(\d+)x(\d+)\.", src)
    w, h = (int(m.group(1)), int(m.group(2))) if m else (None, None)
    return {"type": "captionedImage", "content": [{"type": "image2", "attrs": {
        "src": src, "srcNoWatermark": None, "fullscreen": None, "imageSize": None, "height": h, "width": w,
        "resizeWidth": None, "bytes": None, "alt": None, "title": None, "type": "image/png", "href": None,
        "belowTheFold": False, "topImage": False, "internalRedirect": None, "isProcessing": False, "align": None, "offset": False}}]}


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = {"type": "doc", "content": []}
        self.stack = [self.root]
        self.marks = []
        self.pre = False

    def top(self):
        return self.stack[-1]

    def ensure_para(self):
        # list items / blockquotes need text inside a paragraph
        if self.top()["type"] in ("list_item", "blockquote"):
            node = {"type": "paragraph", "attrs": {"textAlign": None}, "content": [], "_auto": True}
            self.top()["content"].append(node)
            self.stack.append(node)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "pre":
            self.pre = True
            node = {"type": "code_block", "attrs": {"language": None}, "content": []}
            self.top()["content"].append(node); self.stack.append(node); return
        if tag == "hr":
            self.top()["content"].append({"type": "horizontal_rule"}); return
        if tag in BLOCK:
            if self.top().get("_auto"):
                self.stack.pop()
            node = {"type": BLOCK[tag], "content": []}
            if tag == "p" or tag[0] == "h":
                node["attrs"] = {"textAlign": None}
            if tag[0] == "h" and tag[1:].isdigit():
                node["attrs"]["level"] = int(tag[1:])
            if tag == "ol":
                node["attrs"] = {"start": 1, "order": 1}
            self.top()["content"].append(node); self.stack.append(node); return
        if tag == "a":
            self.marks.append({"type": "link", "attrs": {"href": a["href"], "target": "_blank", "rel": "noopener noreferrer nofollow", "class": None}}); return
        if tag in MARK and not self.pre:
            self.marks.append({"type": MARK[tag]})

    def handle_endtag(self, tag):
        if tag == "pre":
            self.pre = False; self.stack.pop(); return
        if tag in BLOCK:
            while self.stack[-1].get("_auto"):
                self.stack.pop()
            self.stack.pop(); return
        if tag == "a" or (tag in MARK and not self.pre):
            for i in range(len(self.marks) - 1, -1, -1):
                if self.marks[i]["type"] == ("link" if tag == "a" else MARK[tag]):
                    del self.marks[i]; break

    def handle_data(self, data):
        if self.pre:
            self.top()["content"].append({"type": "text", "text": data.rstrip("\n")}); return
        if not data.strip() and self.top()["type"] in ("doc", "bullet_list", "ordered_list", "list_item", "blockquote"):
            return
        self.ensure_para()
        node = {"type": "text", "text": data}
        if self.marks:
            node["marks"] = [dict(m) for m in self.marks]
        self.top()["content"].append(node)


def clean(n):
    n.pop("_auto", None)
    if "content" in n:
        for c in n["content"]:
            clean(c)
        # trim leading/trailing newlines inside blocks
        txt = [c for c in n["content"] if c["type"] == "text"]
        if txt and n["type"] != "code_block":
            n["content"][0]["text"] = n["content"][0]["text"].lstrip("\n") if n["content"][0]["type"] == "text" else n["content"][0].get("text")
            if n["content"][-1]["type"] == "text":
                n["content"][-1]["text"] = n["content"][-1]["text"].rstrip("\n")
            n["content"] = [c for c in n["content"] if c["type"] != "text" or c["text"]]
        for c in n["content"]:
            if c["type"] == "text":
                c["text"] = c["text"].replace("\n", " ")
        if not n["content"] and n["type"] in ("paragraph",):
            del n["content"]
    return n


def convert(md, comic, info, before):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    title = re.search(r"^# (.+)$", md, re.M).group(1).strip()
    md = re.sub(r"^# .+\n", "", md, count=1, flags=re.M)
    md = re.sub(r"^>> ", "> ", md, flags=re.M)
    md = re.sub(r"(?m)^(?!\s*[-*] |\s*\d+\. )(.+)\n(\s*[-*] |\s*\d+\. )", r"\1\n\n\2", md)
    md = md.replace("{{PAYWALL}}", "\n\nXXSUBXX\n\n").replace("{{SUBSCRIBE}}", "\n\nXXSUBXX\n\n")
    md = re.sub(r"\{\{BUTTON:([^|]+)\|([^}]+)\}\}", r"[\1](\2)", md)
    html = markdown.markdown(md, extensions=["extra"])
    p = P(); p.feed(html)
    doc = clean(p.root)
    out = []
    for n in doc["content"]:
        if n["type"] == "paragraph" and n.get("content") and n["content"][0].get("text") == "XXSUBXX":
            out.append(SUB); continue
        if n["type"] == "heading" and before and n["content"] and "".join(c.get("text", "") for c in n["content"]).strip() == before:
            out.append(image(info))
        out.append(n)
    if comic:
        out.insert(0, image(comic))
    doc["content"] = out
    assert sum(1 for n in out if n["type"] == "captionedImage") == (2 if comic else 1), "infographic anchor H2 missing"
    return title, doc


if __name__ == "__main__":
    src, dst, comic, info, before, subtitle = sys.argv[1:7]
    title, doc = convert(open(src, encoding="utf-8").read(), None if comic == "-" else comic, info, before)
    s = json.dumps(doc, ensure_ascii=False)
    assert "{{" not in s and "XXSUBXX" not in s
    json.dump({"draft_title": title, "draft_subtitle": subtitle, "draft_body": s}, open(dst, "w"), ensure_ascii=False)
    types = {}
    def walk(n):
        types[n["type"]] = types.get(n["type"], 0) + 1
        for c in n.get("content", []): walk(c)
    walk(doc)
    print(dst, title, len(s), types)
