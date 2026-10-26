---
name: newsletter-publish
description: End-to-end newsletter and social pipeline for System Design Laws / Pretense - write a news or system-design issue, score it with the 11 auditors, generate Gemini images (dialogue comic + infographic), and schedule it on Substack, Brevo and LinkedIn at a twice-a-week cadence. Trigger on "newsletter", "schedule substack", "brevo campaign", "linkedin post", "system design issue", "cybersecurity news issue", "twice a week", "Gemini images", "publish the drafts".
---

# Newsletter publish: draft -> audit -> images -> Substack + Brevo + LinkedIn

One issue = one draft, two images, three scheduled sends. Every step below has a check;
a step whose check was skipped counts as undone.

## 0. Rules that never bend

- **Founder go before anything reaches people.** Show the draft path + send times, wait for an
  explicit "go" (CLAUDE.md: outreach is never 100% automated dispatch). Scheduling counts as sending.
- **Sign-ins stay with the founder.** Substack, Gemini, LinkedIn, Brevo run in the founder's Chrome.
  If signed out, open the sign-in page and ask; never type passwords or open magic links.
- **Positive wording everywhere** (founder rule): headlines, bubbles, labels, body. Say what to do:
  "Log metadata only", never "not bodies" / "don't" / "never" / "cannot".
  Check: `grep -noiE "\b(not|no|don't|never|cannot|can't|won't|doesn't|isn't)\b" DRAFT.md` -> 0 outside code.
- **Product claims match mutation.md.** Secrets are swapped one-way and stay as stand-ins in replies;
  identifiers come back byte-exact; email/phone are flagged by default. Never "redact", "guarantee",
  "SOC 2 certified", "zero data exposure". News facts get a primary source in a Sources section.
- **No duplicates.** Check the Substack archive (`/publish/posts` published, scheduled, drafts) and the
  Brevo campaign list before creating anything.

## 1. Cadence: twice a week

Tuesday and Friday, 09:00 America/Los_Angeles. Convert every time explicitly; the three tools use
three different zones:

| Tool | Zone it shows | 09:00 PDT (until Nov 1) | 09:00 PST (after Nov 1) |
|---|---|---|---|
| Substack scheduler | browser local, IST (GMT+5:30) | 21:30 IST | 22:30 IST |
| Brevo scheduler | account zone, Asia/Karachi (GMT+5) | 21:00 | 22:00 |
| LinkedIn scheduler | browser local, IST | post 30 min later: 22:00 IST | 23:00 IST |

Verify Substack with JS: `new Date(document.querySelector('input[type=datetime-local]').value).toISOString()`
must equal the intended UTC time. LinkedIn goes 30 min after the Substack send so the article link is live.

## 2. Draft + audit

- Drafts live in `newsletter/drafts/*.md` (sent UI-only issues: `newsletter/sent/`): H1, `**TL;DR**`, `>> 30-second version`,
  `{{PAYWALL}}`, H2 sections, `## Interview Q&A`, `## Sources` (news), Pretense disclosure with
  `utm_source=substack&utm_medium=newsletter&utm_campaign=sdl-<slug>`, `{{SUBSCRIBE}}`, `{{BUTTON:...}}`.
- Score: `python3 Product1/local-gate/audit-score.py --kind newsletter DRAFT.md` (needs `ollama serve`).
  PASS 11/11 to ship; `--no-model` gives REVIEW at best and is only a quick gate check.
- Social copy: `--kind social`, 40-260 words, links UTM-tagged `utm_source=linkedin&utm_medium=social`.

## 3. Images (Gemini, founder's Chrome)

Two per issue, both checked word by word before use:

1. **Dialogue comic** (founder reference: LinkedIn activity 7519774761619673088). Square 1:1, warm
   editorial comic, yellow banner headline, 4-5 people around a table, 4-5 speech bubbles with the
   issue's key lines, wooden name plate ("INCIDENT REVIEW", "DESIGN REVIEW"...).
2. **Infographic, Alex Xu / ByteByteGo style** (reference: activity 7518699080609521664). Portrait 4:5,
   white background, title with green accent bar, "SystemDesignLaws" top right (never ByteByteGo),
   central teal node, 4 mint boxes left, 4 peach boxes right, dashed connectors.

Prompt rules that worked: "spelled exactly", "no other text, no logos, no watermark", quote each
bubble, **no numbering** (Gemini prints "1)" into bubbles), keep bubbles short (long ones garble:
"replica beh-ind"). Fix one bad bubble with "Edit this image: change only the bubble X to read exactly: Y".

Limits seen: a chat stalls after ~4 images (open a new chat at gemini.google.com/app), and the account
hits a daily image cap ("I can create more images as soon as your limit resets"). When capped, an
infographic can be built as HTML (white div, flex boxes, SVG dashed paths) and captured the same way;
comics wait for the reset - edit the scheduled post before its send date.

**Capture (founder: "take a screenshot by re-sizing over downloading"):**
- In the Gemini tab, overlay the newest image full-viewport, then zoom-capture its rect with
  `save_to_disk: true` and **no `scale`** (scale shrinks the saved file to ~300 px).
  ```js
  window.__show=(i)=>{document.getElementById('__ov')?.remove();const ims=[...document.querySelectorAll('img')].filter(x=>x.naturalWidth>500);const s=ims.at(i);const ov=document.createElement('div');ov.id='__ov';ov.style.cssText='position:fixed;inset:0;z-index:2147483647;background:#fff;display:flex;align-items:center;justify-content:center';const im=new Image();im.src=s.src;im.style.cssText='max-width:100vw;max-height:100vh';ov.appendChild(im);document.body.appendChild(ov);return new Promise(r=>im.onload=()=>{const b=im.getBoundingClientRect();r({n:ims.length,rect:[b.x,b.y,b.right,b.bottom].map(Math.round)})})};await window.__show(-1)
  ```
- Copy the saved file into the session scratchpad `img/`. Avoid: Gemini download (native Save dialog,
  lands on ~/Desktop), copy button (founder's clipboard use overwrites it), macOS `screencapture`
  (pulls the founder's other Chrome windows forward).

## 4. Substack (newsletter.systemdesignlaws.xyz)

1. Render paste HTML from the draft (drop H1 - it goes in the title field; strip PAYWALL/SUBSCRIBE;
   BUTTON -> link). Clipboard as rich HTML: `osascript -l JavaScript html2clip.js FILE.html`.
2. `/publish/post?type=newsletter`. Title and subtitle by element ref (a long title wraps and moves
   the subtitle box; coordinate clicks then type into the title). Body: the editor is tiptap -
   place the cursor with the API, not the mouse:
   `const e=document.querySelector('.ProseMirror').editor; e.chain().setTextSelection(1).focus().run()` then cmd+v.
3. Images: insert an empty paragraph where the image goes (`insertContentAt(pos,{type:'paragraph'})`),
   set selection inside it, put the PNG on the clipboard (`osascript -l JavaScript img2clip.js FILE.png`)
   **right before** cmd+v, then delete the leftover empty paragraph. Comic at the top, infographic
   before the main design section. Text edits on a saved post: `e.view.dispatch(e.state.tr.insertText(new, from, to))`.
4. Verify: section headings, link hostnames, UTM present, no `{{` markers, images on substackcdn.
5. Continue -> **Audience: Everyone** (default is "Paid subscribers only" = reaches nobody),
   comments "Free and paid subscribers", tick "Schedule time to email and publish", set datetime,
   verify UTC, click "Send to everyone in N days". The "Add subscribe buttons" prompt returns to the
   editor without scheduling - press Continue again and confirm the button text still says "in N days".
6. Check `/publish/posts/scheduled` lists it. Grab the public image URLs for Brevo:
   `decodeURIComponent(img.src).match(/https:\/\/substack-post-media\.s3\.amazonaws\.com\/public\/images\/[^?&]+/)`.

## 5. Brevo (newsletter list, Pretense sender)

1. Render email HTML: `python3 newsletter/scripts/render_email.py DRAFT.md OUT.html CAMPAIGN COMIC_URL|- INFOGRAPHIC_URL "<H2 to place infographic before>"`
   (tested in `tests/test_render_email.py`, PR #18; needs `pip install markdown`; `-` skips the comic)
   (rewrites UTMs to `utm_source=newsletter&utm_medium=email`, adds `{{ unsubscribe }}`, ASCII check).
2. Campaigns -> Create campaign -> Email -> name -> Create. Recipients: picker, type "newsletter",
   click the list, click outside, Save. Subject + preview: the two contenteditables, Save.
3. Start designing -> Create from scratch -> "HTML custom code" (menuitem needs JS `.click()`),
   click the textarea, `pbcopy < OUT.html` then cmd+v (retry once if the textarea reads 0 bytes),
   check length and `<img` count, Save & Quit.
4. Schedule -> Schedule for later -> date picker -> hour list (scroll inside it) -> Schedule.
   Confirm the list shows "Scheduled for <date> <time>".

## 6. LinkedIn (founder profile)

1. Feed -> Start a post. Paste text as HTML paragraphs (`<p>..</p><p><br></p>`), plain paste collapses
   blank lines. Remove the auto link-preview card (X) so the Media button comes back.
2. Image: never click Media normally (native file picker). Patch the picker, then click Media:
   ```js
   const oc=HTMLInputElement.prototype.click;HTMLInputElement.prototype.click=function(){if(this.type==='file'){if(!this.isConnected){this.style.display='none';document.body.appendChild(this)}return}return oc.call(this)}
   ```
   `find` the new file input ref. Build a branded 740x888 frame in a helper tab (image page with the
   comic 740x740 + a dark footer "SystemDesignLaws / newsletter.systemdesignlaws.xyz"), take a
   **full-scale** screenshot, then `upload_image` with that exact screenshot ID (wait for the ID - do
   not guess it) into the input ref. Editor -> Next.
3. Clock icon -> date `MM/DD/YYYY` + Enter, time `10:00 PM` -> check "Posting at ..." -> Confirm -> Schedule.
   The clock badge count goes up by one.

## 6b. Gotchas learned 2026-10-26

- Substack publish modal: a JS `.click()` on the "Schedule time" checkbox flips the DOM but not the
  app state, and the button keeps saying "Send to everyone now". Use a real click, then confirm the
  button reads "Send to everyone in N days" before pressing it. JS clicks on the audience/comment
  radios do register, but check the modal visually anyway.
- Brevo date picker opens on the current month: click the right arrow for next month. Minutes
  default to 30 after the first edit, so set them to 00. Renaming a campaign in the narrow window
  does not stick (the name field is half off-screen). It is an internal label, so skip it.
- LinkedIn: after "View scheduled posts", clicking a row opens that post in edit mode. Back and X
  both raise "Discard changes" - press Cancel and leave it; never risk the founder's scheduled post.
- Gemini: a chat stalls after ~4 images (open a new chat), and there is a daily image cap. When capped,
  the infographic can be HTML (white div, flex boxes, SVG dashed paths) captured by zoom.
- `upload_image` sends the screenshot at the scale it was taken: take it at scale 1, wait for the
  ID, and never guess an ID in a parallel call.
- Repo rule: drafts committed to `systemdesignlaws.xyz/newsletter/drafts/` must have 20+ Excalidraw
  diagrams (`test_all_drafts_minimum_20_diagrams`). UI-sent issues with 2 lead images go in `newsletter/sent/`
  until they meet it; say so to the founder before scheduling.
- Shell: `cd` into the scratchpad before writing relative paths; a stray relative write lands in ~/dev.

## 7. Close out

- Update `Product1/docs/CHECKLIST.md` (Phase K) with post IDs, campaign numbers and send times.
- Tell the founder: what is scheduled where (tool, date, local + PT), what is blocked and why
  (signed out, Gemini cap, Strapi `NEXT_PUBLIC_STRAPI_URL` unset), and how to cancel.
- New gotchas go into this skill, not just into memory.
