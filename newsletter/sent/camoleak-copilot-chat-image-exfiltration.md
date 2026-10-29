# CamoLeak: The Chat Answer Was the Exfiltration Channel

**TL;DR** - In June 2025, Legit Security researcher Omer Mayraz found that hidden text in a GitHub pull request could steer Copilot Chat into leaking private repository content through GitHub's own Camo image proxy. GitHub disabled image rendering in Copilot Chat as of August 14, 2025. The lesson: the response path is an egress path, so treat every model answer as untrusted output.

>> 30-second version: "CamoLeak carried private repo data out inside a chat answer, one invisible image per character. Every image pointed at GitHub's own trusted proxy, so the allowlist approved each request. If a model's answer can render, it can send."

---

## What Happened

Copilot Chat runs with the permissions of the person asking. According to Legit Security's write-up (dated September 30, 2025) and The Register (October 9, 2025):

- **The discovery:** Mayraz found the flaw in June 2025, rated it CVSS 9.6, and reported it through HackerOne.
- **The injection:** he hid instructions for Copilot inside a pull request description using GitHub's hidden-comment markdown, an official feature. When a different user asked Copilot Chat about the PR, Copilot followed the hidden instructions with that user's access.
- **The exfiltration path:** GitHub's Content Security Policy limits images to GitHub-owned domains, and GitHub rewrites external image links into signed Camo proxy URLs. Mayraz used GitHub's API to pre-generate a signed Camo URL for every letter and symbol, each pointing at his server, which returned a 1x1 transparent pixel. The prompt told Copilot to render the target data as a sequence of these images. The order of fetches spelled out the data.
- **The demo:** the proof of concept leaked a zero-day description from an issue in a private project, plus the result of a codebase search for `AWS_KEY`. The Register reports the PoC pulled AWS keys and security tokens.
- **The fix:** in Legit's words, "GitHub fixed it by disabling image rendering in Copilot Chat completely," effective August 14 per GitHub. The Register adds that GitHub blocked the use of Camo to leak "sensitive victim user content" while a longer-term remediation is developed.

{{PAYWALL}}

---

## The Design Flaw: The Answer Is an Outbound Request

**What is Camo?** GitHub's image proxy, built on the open-source Camo project. GitHub rewrites external image URLs to `camo.githubusercontent.com` with an HMAC signature; the proxy checks the signature, fetches the image and serves it from a GitHub domain.

**What is indirect prompt injection?** Instructions planted in content the model reads as data, such as a PR description, which the model then follows as commands.

CamoLeak lined up three ordinary facts:

- **Untrusted input reached the model.** Anyone who can open a PR can write a hidden comment.
- **The model held private access.** Copilot Chat acts with the asking user's permissions.
- **The output reached a renderer that makes network requests.** Markdown images load the moment the answer appears.

Together they form a full loop: read the secret, encode it, send it.

The allowlist part is the subtle one. CSP said "GitHub domains," and Camo is a GitHub domain. A Camo signature means "GitHub approved this fixed URL." Mayraz signed one URL per character in advance, so each request was legitimate on its own; the data lived in the sequence. When an allowed proxy forwards to any origin, the allowlist quietly includes the whole internet.

---

## Five Fixes, Cheapest First

### 1. Render model output as plain text by default

Strip images and auto-loading media from assistant answers. This is the control GitHub shipped.

### 2. Surface hidden content before the model reads it

Strip or display HTML comments, zero-width characters and collapsed sections, and label PR and issue text as third-party data in the prompt.

### 3. Scope the assistant to the task

A PR review needs the PR and its diff. Ask for consent before wider searches, and log each one.

### 4. Treat every proxy as egress

For AI-generated content, allowlist final destinations, including the proxy's upstream targets. Cap images per answer and alert on bursts of distinct URLs from one response.

### 5. Swap secrets locally before they leave the machine

Run a local proxy on the developer laptop that replaces detected secrets and PII with stand-in tokens before the request reaches a model provider. Two details matter:

- **Reversible where it is safe.** Code identifiers swap back byte-exact in the answer, so the developer reads their own code.
- **One-way for secrets.** Secret stand-ins stay as stand-ins in the answer. If an injected prompt places a stand-in inside an image URL, the URL carries a meaningless token; reversing it would splice the real credential into the attacker's request.

This covers traffic passing through the developer's machine. Copilot Chat reads repositories on GitHub's servers, so pair it with fixes 1 to 4 on the hosted side.

---

## Where This Shows Up in a System Design Interview

Any LLM that reads user-supplied content carries an egress question. Draw the chat UI and say:

- Model output renders as text; rich media goes through an allowlist of final destinations.
- Retrieved content is labeled untrusted, and hidden markup is stripped at ingestion.
- Secrets are tokenized on the client and stay tokenized on the way back.

---

## Interview Q&A

- **Why is "render Markdown in the chat" a security decision?** - Each image tag is an HTTP request from the user's browser. If the model controls the URL, it controls an outbound channel.
- **CSP limited images to GitHub domains. Why was that insufficient?** - Camo is a GitHub domain that forwards to external hosts. Pre-signed URLs made the trusted proxy a relay, and the data rode in the request order.
- **Where should prompt-injection defense live?** - At both ends: clean inputs and constrain outputs.
- **How would you detect this pattern?** - One assistant response producing many distinct proxy fetches of tiny images from one upstream host within seconds.

---

## Sources

- Legit Security, Omer Mayraz, "CamoLeak: Critical GitHub Copilot Vulnerability Leaks Private Source Code" (September 30, 2025): https://www.legitsecurity.com/blog/camoleak-critical-github-copilot-vulnerability-leaks-private-source-code
- The Register, Carly Page, "GitHub Copilot Chat turns blabbermouth with crafty prompt injection attack" (October 9, 2025): https://www.theregister.com/2025/10/09/github_copilot_chat_vulnerability/
- GitHub Docs, "About anonymized URLs" (Camo): https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-anonymized-urls

---

*Disclosure: I build [Pretense](https://pretense.ai/?utm_source=substack&utm_medium=newsletter&utm_campaign=sdl-camoleak), a local proxy that does fix 5: it swaps API keys, tokens, PII and code identifiers for stand-ins before a request leaves the laptop. Identifiers come back byte-exact; secrets stay as stand-ins in the answer. It covers traffic that passes through it, and it works alongside fixes 1 to 4 for hosted assistants like Copilot Chat.*

{{SUBSCRIBE}}

{{BUTTON:Read More Articles|https://newsletter.systemdesignlaws.xyz}}
