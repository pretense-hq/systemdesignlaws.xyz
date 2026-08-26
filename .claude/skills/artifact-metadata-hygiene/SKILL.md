---
name: artifact-metadata-hygiene
description: Find defects in a document that never appear in its rendered text — library-default authorship, placeholders split across runs, fill-in blanks. Use before submitting any .docx as audit evidence or publishing a policy. Trigger on "docProps", "core.xml", "python-docx", "Un-named", "document metadata", "who authored this", "placeholder", "template text", "before uploading the policy", "Clause 7.5.2".
---

# The defects that survive proofreading

You read the document. It was fine. The defects below are **not in the text you read** — they are
in the package, or split across XML runs so that no visual inspection and no naive grep can see
them.

## Defect 1 — library-default authorship in an ISO-controlled document

Generated `.docx` files carry the generating library's name where an author belongs:

```
<dc:creator>python-docx</dc:creator>
<cp:lastModifiedBy>Un-named</cp:lastModifiedBy>     <- the `docx` npm package's default
```
`Un-named` is the docx npm package default; `python-docx` is the Python library's. Both were sitting
in documents headed for an assessor.

**ISO/IEC 27001 Clause 7.5.2** requires documented information to be identified — title, date,
**author**, reference number. An assessor opening file properties and seeing `python-docx` learns
two things at once: the stated author did not write it, and nobody checked. It costs nothing to
fix and is disproportionately damaging to find.

```bash
unzip -p FILE.docx docProps/core.xml | grep -oE '<dc:creator>[^<]*'
unzip -p FILE.docx docProps/core.xml | grep -oE '<cp:lastModifiedBy>[^<]*'
```
Sweep the whole package, not just `core.xml` — authorship and stale text hide in six other places:

| Part | Carries |
|---|---|
| `docProps/core.xml` | `dc:creator`, `cp:lastModifiedBy`, `dc:title`, `cp:revision` |
| `docProps/app.xml` | `Company`, `Manager`, `Application`, `Template` |
| `docProps/custom.xml` | arbitrary org fields, often from the source template |
| `word/header*.xml` `word/footer*.xml` | classification banners, old company names, `{placeholders}` |
| `word/comments.xml` | review comments nobody meant to ship |
| `word/footnotes.xml` `word/endnotes.xml` | same |

```bash
for p in docProps/core.xml docProps/app.xml docProps/custom.xml; do
  echo "== $p"; unzip -p FILE.docx "$p" 2>/dev/null | sed 's/></>\n</g'
done
unzip -l FILE.docx | grep -E 'header|footer|comments|footnotes|endnotes'
```
## Defect 2 — a placeholder split across runs is invisible to grep

Word splits a paragraph into `w:r` runs at every formatting change — including changes you cannot
see, like a spell-check boundary or a tracked edit. `{scope of ISMS}` becomes:

```xml
<w:p><w:r><w:t>{scope</w:t></w:r><w:r><w:t> of </w:t></w:r><w:r><w:t>ISMS}</w:t></w:r></w:p>
```
`grep -o '{[^}]*}'` over `document.xml` finds **nothing**. The placeholder is right there in the
rendered text — this is exactly how a `{scope of ISMS}` template reached `approved v1.0`.

**Concatenate per paragraph before matching.** Include `w:instrText` (field codes — MERGEFIELD
placeholders live here and render as text) and `w:delText` (tracked deletions that reappear if
changes are rejected):

```python
import re, zipfile
XML = zipfile.ZipFile(f).read("word/document.xml").decode("utf8")
for para in re.findall(r"<w:p[ >].*?</w:p>", XML, re.S):
    text = "".join(re.findall(r"<w:(?:t|instrText|delText)[^>]*>(.*?)</w:(?:t|instrText|delText)>",
                              para, re.S))
    text = re.sub(r"&amp;", "&", text)
    if PLACEHOLDER.search(text):
        print(text[:120])
```
## Defect 3 — the fill-blank that matches no bracket pattern

```
...as of ______________
```
No brace, no angle bracket, no `TODO`. Every placeholder regex misses it, and it is the single most
common leftover in a policy template. `_{6,}` catches it.

## The placeholder pattern set

```python
PLACEHOLDER = re.compile(r"""
    \{[^}\n]{1,80}\}              # {scope of ISMS}
  | <[A-Z][^>\n]{1,80}>           # <SAMPLES PROVIDED - UPDATE>, <Company Name>
  | \[\[?[^\]\n]{1,80}\]\]?       # [insert date], [[TBD]]
  | _{6,}                         # ...as of ______________
  | \b(?:TBD|TODO|FIXME|XXX|LOREM IPSUM)\b
  | \b(?:e\.g\.|for example)[^.\n]{0,60}(?:Lombard|Main HQ|Acme|Contoso)
  | \bYYYY-MM-DD\b | \bMM/DD/YYYY\b
""", re.X | re.I)
```
Keep `_{6,}` and the `<UPPER>` form; those are the two that ordinary bracket patterns miss. Both
appeared in a document that was `approved v1.0`.

## Pre-submission command

```bash
for f in *.docx; do
  echo "== $f"
  unzip -p "$f" docProps/core.xml | grep -oE '<(dc:creator|cp:lastModifiedBy)>[^<]*'
  python3 tools/placeholder_scan.py "$f"     # paragraph-concatenating scan above
done
```
Run it on the **file you are about to upload**, not the source you edited — `decisions.md` §7. And
run it again on what the platform serves back: see [[compliance-doc-integrity]] and
[[platform-evaluator-as-witness]] for extraction that mangles the served copy.

## Self-test
Seed the exact defect this skill describes into a fixture, confirm the check reports it,
then remove the check and confirm the fixture now passes. A check never seen to fail is
not evidence.
