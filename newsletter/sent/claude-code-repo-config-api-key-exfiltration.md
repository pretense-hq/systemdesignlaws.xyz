# A Repo Setting Chose Where Claude Code Sent Your API Key

**TL;DR** - Before version 2.0.65, opening a hostile repository in Claude Code could send the user's Anthropic API key to an attacker: a project settings file set `ANTHROPIC_BASE_URL`, and Claude Code called the API before the trust prompt. The lesson: repo config is untrusted input, trust comes before the first network call, and credentials stay pinned to their host.

>> 30-second version: "A config file inside a repo decided where an API key went, and the client followed it before asking the user. Treat every repo file as untrusted until the user says otherwise, and bind each credential to its one legitimate destination."

---

## What Happened

Check Point Research (Aviv Donenfeld and Oded Vanunu) published "Caught in the Hook" on February 25, 2026.

- **The setting:** a repository's `.claude/settings.json` can set environment variables. Of `ANTHROPIC_BASE_URL`, Check Point writes: "This environment variable controls the endpoint for all Claude Code API communications."
- **The timing:** routing that variable through their own proxy, the researchers saw that "before we could even interact with the trust dialog, Claude Code had already initiated several requests."
- **What leaked:** "every request included the authorization header - our full Anthropic API key, completely exposed in plaintext," plus session-setup prompts with repository file names and recent commit messages. In a hostile repo, the key "would be sent directly to the attacker's server."
- **The blast radius:** in Anthropic's Workspaces, "Any API key belonging to that workspace inherits visibility into the Workspace's stored files," so a stolen key could read, delete and upload team files.
- **The timeline (per Check Point):** reported October 28, 2025; fixed December 28, 2025. The fix ensures "no API requests are initiated before users confirm the trust dialog."
- **The advisory:** GHSA-jh7p-qr78-84p7 (January 20, 2026) lists `@anthropic-ai/claude-code` below 2.0.65 as affected and 2.0.65 as patched; auto-update users already have the fix. NVD published CVE-2026-21852 on January 21, 2026.
- **The scores differ:** GitHub, as CNA, rates it CVSS 4.0 5.3 (Medium). NIST's February 2, 2026 analysis added CVSS 3.1 7.5 (High). NVD lists CWE-522, Insufficiently Protected Credentials.

The same research covered earlier pre-trust issues. CVE-2025-59536, "Claude Code can execute commands prior to the startup trust dialog," was published October 3, 2025 and fixed in 1.0.111 (GitHub CVSS 4.0 8.7; NVD CVSS 3.1 8.8); Check Point ties it to an MCP consent bypass. A hooks finding is advisory GHSA-ph6w-f82w-28w6, fixed in 1.0.87.

{{PAYWALL}}

---

## The Design Flaw: Untrusted Config Picked the Credential's Destination

**What is a trust prompt?** The dialog a coding agent shows when it first opens a folder. It is a privilege boundary: everything before the answer runs on behalf of an unknown author.

**What is a base URL override?** An environment variable that sends a client's API traffic to a different host, used legitimately for corporate gateways and testing. The client attaches the same API key to whatever host it names.

Combine them and you get an ordering bug stacked on a trust bug:

- **Config is code.** A settings file that sets environment variables changes program behaviour, and anyone with commit access writes it, including the author of a pull request you check out.
- **Network before consent.** The client began API calls ahead of the trust decision, so the user had zero chance to object.
- **The key follows the URL.** The credential was bound to "wherever the base URL points" when it belonged to one destination. One string in a repo file moved a secret across the trust boundary.

Hooks and MCP servers share the shape: config that acts.

---

## Five Fixes, Cheapest First

### 1. Patch and rotate

Confirm `claude --version` shows 2.0.65 or later. If anyone opened unfamiliar repositories on an older build with an API key configured, rotate that key and review Workspace file activity.

### 2. Review repo config like code

Add `.claude/` and `.mcp.json` to CODEOWNERS. Open unfamiliar repos in a container with a throwaway key.

### 3. Trust before the first network call

For tool builders: parse project config into inert data, ask, then open sockets. Add a test that launches the tool in a hostile fixture repo and asserts zero outbound connections before consent.

### 4. Pin credentials to their destination

Treat host-changing overrides from project files as privilege escalation. Accept base URLs from user-level or organization-managed settings, ask explicitly when a project file wants to change one, keep an allowlist of approved hosts, and scope keys with spend limits.

### 5. Swap secrets in prompt content before egress

Prompts carry more than the key: file names, commit messages, code. A local proxy can replace detected secrets, PII and code identifiers with stand-in tokens before a request leaves the laptop, so the provider and its logs hold stand-ins. Identifiers swap back byte-exact in the answer; secrets stay as stand-ins.

A local proxy is typically wired in through that same base URL setting, so a repo that overrides it routes around the proxy as well. Fixes 1 to 4 keep the client pointed where you chose; fix 5 covers what travels on that path.

---

## Where This Shows Up in a System Design Interview

Any client that reads project config and holds a credential: CLIs, IDE plugins, coding agents. Say:

- Project config is untrusted input until the user grants trust.
- The client makes zero network calls before that decision.
- Each credential is pinned to an allowlisted host.

---

## Interview Q&A

- **Why is a base URL a security setting?** - Whoever controls that string receives the key.
- **Where does the trust check sit at startup?** - Ahead of hooks, MCP startup and every outbound request. Parse, ask, then act.
- **How do you bind a key to its destination?** - Allowlist hosts per credential and reject host changes from lower-trust config.
- **Why did NVD and GitHub score it differently?** - GitHub's 4.0 vector rates confidentiality low with passive interaction; NIST's 3.1 vector rates it high with zero interaction.

---

## Sources

- Check Point Research, "Caught in the Hook" (February 25, 2026): https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/
- Anthropic, advisory GHSA-jh7p-qr78-84p7 (January 20, 2026): https://github.com/anthropics/claude-code/security/advisories/GHSA-jh7p-qr78-84p7
- NIST NVD, CVE-2026-21852 (January 21, 2026): https://nvd.nist.gov/vuln/detail/CVE-2026-21852
- NIST NVD, CVE-2025-59536 (October 3, 2025): https://nvd.nist.gov/vuln/detail/CVE-2025-59536
- Anthropic, advisory GHSA-4fgq-fpq9-mr3g (October 3, 2025): https://github.com/advisories/GHSA-4fgq-fpq9-mr3g
- Anthropic, advisory GHSA-ph6w-f82w-28w6: https://github.com/advisories/GHSA-ph6w-f82w-28w6

---

*Disclosure: I build [Pretense](https://pretense.ai/?utm_source=substack&utm_medium=newsletter&utm_campaign=sdl-claude-code-config), a local proxy that does fix 5: it swaps secrets, PII and code identifiers in prompt content for stand-ins before a request leaves the laptop. Identifiers come back byte-exact; secrets stay as stand-ins. It works on traffic that passes through it, so a repo that rewrites the base URL routes around it; pair it with patching, trust-before-network and pinned base URLs.*

{{SUBSCRIBE}}

{{BUTTON:Read More Articles|https://newsletter.systemdesignlaws.xyz}}
