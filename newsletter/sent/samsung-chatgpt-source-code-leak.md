# Samsung's ChatGPT Incidents: A Ban Moves the Traffic, a Gateway Controls It

**TL;DR** - In March 2023, within 20 days of Samsung's chip division allowing ChatGPT, engineers entered equipment source code and a meeting transcript into it in three reported cases. Samsung capped prompts at 1,024 bytes, then in May restricted generative AI on company devices. A ban changes where AI traffic flows; a controlled egress path decides what it carries.

>> 30-second version: "Engineers wanted help with real work, so real work went in. Blocking the tool on company devices pushes the habit to personal phones, where the company sees less. Give people one approved path, classify what may travel on it, and swap secrets and identifiers before the prompt leaves the machine."

---

## What Happened

- **March 11, 2023:** Samsung's Device Solutions (DS) division, its semiconductor business, began allowing ChatGPT. The company had blocked it on site over leak concerns, and its DX mobile and appliance division kept the block, per Economist Korea.
- **March 30, 2023:** Economist Korea reported three incidents in under 20 days:
  - One employee copied the full source of a program that downloads semiconductor equipment measurement data and asked ChatGPT how to fix an error.
  - Another entered the full source of a program for identifying yield and defect equipment and asked for optimization.
  - A third transcribed a recorded meeting with Naver Clova and entered it to produce minutes.
- **Emergency measures:** Samsung limited uploads to 1,024 bytes per question, investigated with discipline where needed, and warned that internal-network access could be blocked. Its notice said content entered into ChatGPT is stored on external servers and retrieval by the company is impossible.
- **Provider terms then:** Engadget noted that under ChatGPT's data policy, prompts were used for training unless users opted out.
- **May 2, 2023:** Bloomberg reported a memo restricting generative AI on company-owned computers, tablets and phones and on internal networks, citing data stored externally, "making it difficult to retrieve and delete." In an internal survey, 65% of respondents saw these tools as a security risk. Staff on personal devices were asked to keep company data out of prompts.
- **Effective date:** TechCrunch reported the rule took effect May 1 and quoted Samsung: "until these measures are ready, we are temporarily restricting the use of generative AI through company devices."
- **Date note:** Bloomberg's memo account places a source-code upload "earlier in April"; Economist Korea dates the three cases to March.

{{PAYWALL}}

---

## The Design Flaw: An Egress Policy With Two Settings

**What is egress?** Data leaving your network for an outside service. Every prompt to a hosted model is egress.

**What is shadow AI?** Unapproved AI use the company can barely observe: personal accounts and phones.

**What is a controlled egress path?** One approved route to model providers, usually a gateway, that knows the user, the data class and the provider terms.

Samsung's DS setup had two positions: blocked, or open. Open meant full source files reached a consumer chatbot within three weeks. The 1,024-byte cap shrank each paste, yet treated a kilobyte of yield logic like a kilobyte of public docs.

Blocking company devices moves the demand. The engineer with a broken script still has a phone, and the May memo relied on a request to personal-device users. The useful third position is a sanctioned route where identity, data class and provider terms are settled before a byte leaves.

---

## Four Fixes, Cheapest First

### 1. Classify data on one page

Public, internal, confidential, restricted. Map each class to a destination: public to approved tools, internal to the enterprise tenant, restricted (yield logic) to an internal model.

### 2. Approve tools with business terms

Buy the enterprise tier and set the controls: prompts excluded from training, short retention, deletion on request, single sign-on.

### 3. Route every request through an enterprise gateway

One endpoint, SSO identity, metadata logs, classification rules at the door. The byte cap was a crude gateway rule; a gateway can route restricted requests to an internal model. Make it faster than a phone.

### 4. Swap secrets and identifiers locally before egress

A proxy on the laptop replaces detected secrets, PII and code identifiers with stand-in tokens before the request leaves. The provider sees a stand-in token where a class name described a measurement-database downloader.

Be precise about coverage. The code's logic and structure still reach the model; that is how it helps. For a meeting transcript, swapping names reduces what reaches the provider while the substance travels. So pair this with fixes 1 to 3: classification decides whether a request goes out, the gateway enforces it, local swapping shrinks what it reveals.

Identifiers come back byte-exact. Secrets and PII stay as stand-ins: reversing them would hand real values to a prompt-injected answer.

---

## Where This Shows Up in a System Design Interview

"Design an internal AI assistant" is the direct version. Draw the client, a local tokenizer, the gateway, a classifier, an external provider under enterprise terms and an internal model. Then say:

- Identity and data class attach before routing.
- Restricted content routes to the internal model.
- Logs hold metadata by default.
- The approved path is fastest, so usage stays visible.

---

## Interview Q&A

- **Why is a ban weaker than a gateway?** - Demand stays, so usage moves to personal devices. A gateway keeps it visible and governed.
- **Where should classification run?** - Both ends: the client swaps secrets and identifiers; the gateway routes and records metadata.
- **Is a prompt-size cap useful?** - As a short-term measure. A kilobyte of restricted code still travels.
- **What does identifier swapping leave exposed?** - Control flow, algorithms, constants and comments; classification covers those.

---

## Sources

- Economist Korea, Jung Du-yong, report on ChatGPT misuse after Samsung DS lifted its block (Korean, March 30, 2023): https://economist.co.kr/article/view/ecn202303300057
- Bloomberg, Mark Gurman, "Samsung Bans Staff's AI Use After Spotting ChatGPT Data Leak" (May 2, 2023): https://www.bloomberg.com/news/articles/2023-05-02/samsung-bans-chatgpt-and-other-generative-ai-use-by-staff-after-leak (syndicated: https://finance.yahoo.com/news/samsung-bans-generative-ai-staff-004831399.html)
- TechCrunch, Kate Park, "Samsung bans use of generative AI tools like ChatGPT after April internal data leak" (May 2, 2023): https://techcrunch.com/2023/05/02/samsung-bans-use-of-generative-ai-tools-like-chatgpt-after-april-internal-data-leak/
- Engadget, Kris Holt, "Three Samsung employees reportedly leaked sensitive data to ChatGPT" (April 7, 2023): https://www.engadget.com/three-samsung-employees-reportedly-leaked-sensitive-data-to-chatgpt-190221114.html

---

*Disclosure: I build [Pretense](https://pretense.ai/?utm_source=substack&utm_medium=newsletter&utm_campaign=sdl-samsung-chatgpt), a local proxy that does fix 4: it swaps detected secrets, PII and code identifiers for stand-in tokens before a request leaves the laptop. Identifiers come back byte-exact; secrets and PII stay as stand-ins. The code's logic still reaches the model, so pair it with classification, approved tools and a gateway.*

{{SUBSCRIBE}}

{{BUTTON:Read More Articles|https://newsletter.systemdesignlaws.xyz}}
