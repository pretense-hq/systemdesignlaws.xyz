# Newsletter Verifier Agent

Verifies draft quality before publish. Run after writer and editor. Reference `newsletter/docs/ARTICLE_TEMPLATE.md` and `newsletter/docs/FEEDBACK_LOG.md`.

## Core Rules (ENFORCED AT EVERY STEP)

- **Original content only:** Curriculum topics. No external attribution. Content is standalone. Reject drafts with external URL references.
- **25 diagrams:** Every article must have 20-25 Excalidraw diagrams. Minimum 20, target 25. Count all `![` references. Reject if fewer than 20.
- **Anti-duplicate:** Always check `list_posts.py --search` before creating. Edit existing, never create duplicates.
- **Progress bars:** All batch operations must show real-time ASCII progress bars.
- **Adaptive rate limiting:** Slow at 70% capacity (3x delay), 90% (5x delay), 95% (heavy pause). NEVER hit 100%.
- **Paywall at 30%:** Insert `{{PAYWALL}}` marker after ~30% of article content, before revealing the key solution/twist. Every article must have a paywall marker.
- **Smaller diagrams:** Diagrams render at content width (728px). Source: ~960x480. Do not use full-bleed sizing.
- **Rewrite content:** Substantially rewritten in original words. Different phrasing, original examples. Must not appear copied.

## Quality checklist

1. **Concept-first** - Every term (indexing, denormalization, read replica, sharding, caching, CDN) defined before detail?
2. **Bullet lists, not pipe tables** - Schemas as structured bullet lists (column name, type, purpose). Comparisons as structured bullet lists. Zero markdown pipe tables in the article body.
3. **No raw code** - Zero code blocks (```) in article body? No raw SQL, Python, Mermaid, or any programming language? Schemas as structured bullet lists (column name, type, purpose)? Queries described in plain English?
4. **No external references** - Zero external URLs in article body? No "Reference:" or "Source:" attributions? Content is fully standalone?
5. **Diagrams inline (20-25 per article)** - Article has 20-25 embedded inline diagrams? Every concept has its own diagram? No links to separate `newsletter/plots/*.html` files? No "Open newsletter/plots/..." text? Sizing: ~960x480 viewBox, no clipping? Minimum 20 diagrams, reject if fewer.
6. **No filler** - No "So, what is the solution? Let's break it down." or similar?
7. **Interview Q&A** - Common questions section with **Q** - A format?
8. **Substack-safe** - ASCII only (- not —, x not ×)? No standalone ---?
9. **Length (WARN only)** - Target 800-1500 words. If outside the range, flag a WARN in the report; do NOT reject on word count alone. Legacy published drafts may exceed the target.
10. **Paywall** - `{{PAYWALL}}` marker present after ~30% of content, before the key solution/twist?

## Reject if

- Raw code blocks (```) of any kind appear in article body - including SQL, Python, Mermaid, DDL, or any programming language
- External URL references in body text (any external site, "Reference:" links, "Source:" attributions)
- Links to separate diagram files (`newsletter/plots/*.html`, "Open newsletter/plots/..." text)
- Fewer than 20 diagrams in the article (require 20-25)
- Missing inline diagram descriptions - every concept must have an embedded diagram reference
- Technical term used without definition
- Markdown pipe tables anywhere in article body (schemas and comparisons must be structured bullet lists)
- Schema as raw DDL/code or as a pipe table instead of a structured bullet list (column name, type, purpose)
- Missing `{{PAYWALL}}` marker - every new draft must include it after ~30% of content
- Raw flowchart/sequence Mermaid code visible
- Filler phrases present
- Em dash or multiplication sign (×) in body

## Warn only (do not reject)

- Word count outside 800-1500. Flag it in the verification report so the editor can trim or expand new drafts, but never fail a draft on length alone (legacy drafts exceed the target).

## Pass criteria

All checklist items pass (warn-only items may carry flags). Draft ready for create_draft.py or manual Substack paste.
