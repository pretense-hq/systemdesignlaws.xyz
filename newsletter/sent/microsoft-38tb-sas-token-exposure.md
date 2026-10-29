# A Share Link Is a Credential: The Microsoft 38 TB SAS Token

**TL;DR** - On September 18, 2023, Wiz disclosed that a model-download link in Microsoft's public `robust-models-transfer` GitHub repository carried an Azure SAS token covering an entire storage account, with full-control permissions, valid until 2051. Behind it sat 38 TB of private data, including workstation backups. Treat every share link as a bearer credential: one container, read access, short-lived, revocable.

>> 30-second version: "A SAS URL is a password that fits in a README. Whoever holds the link holds the access. Scope it to one blob, grant read access, give it an hour of life, and tie it to a policy you can revoke."

---

## What Happened

Microsoft's AI research division published `robust-models-transfer`, open-source image-recognition models that readers downloaded from an Azure Storage URL. Per Wiz Research and MSRC:

- **The link:** the URL carried an Account SAS token configured to share the entire storage account, with full-control permissions where read access would have served the models.
- **The lifetime:** the token was first committed on July 20, 2020, expiring October 5, 2021. On October 6, 2021, the expiry was updated to October 6, 2051 (Wiz timeline).
- **What sat behind it:** Wiz reported 38 TB of additional private data, including a disk backup of two employees' workstations: secrets, private keys, passwords, and over 30,000 internal Teams messages from 359 Microsoft employees. MSRC describes it as backups of two former employees' workstation profiles and their internal Teams messages with colleagues.
- **The write risk:** the models were `ckpt` files serialized with Python's pickle. Wiz noted an attacker could have injected malicious code into the AI models in that account.
- **The response:** Wiz reported to MSRC on June 22, 2023; MSRC revoked the token and blocked external access on June 24, 2023. Wiz lists the GitHub link replaced on July 7 and Microsoft's impact investigation complete on August 16.
- **Microsoft's statement:** "No customer data was exposed, and no other internal services were put at risk because of this issue."
- **The detection gap:** MSRC said historical rescans had flagged this URL, but "the finding was incorrectly marked as a false positive." Microsoft expanded its GitHub secret scanning detection to "any SAS token that may have overly-permissive expirations or privileges."

{{PAYWALL}}

---

## The Design Flaw: A Bearer Link With Account-Wide Reach

**What is a SAS token?** A Shared Access Signature is a signed query string on an Azure Storage URL. Azure checks the signature, scope, permissions and expiry. Whoever presents the URL gets the access.

**What is a bearer credential?** One where possession equals authority. A link in a README is a bearer credential published to the world.

Every SAS has three dials, and the damage multiplies:

- **Scope:** one blob, one container, or the whole account.
- **Permissions:** read, or read plus write and delete.
- **Lifetime:** one hour, or until 2051.

This token sat at the far end of all three.

Account SAS adds a management gap. Wiz: "There isn't any official way to keep track of these tokens within Azure, nor to monitor their issuance." And on revocation, "the only solution is revoking the entire account key."

**What is a stored access policy?** A server-side policy on a container that a Service SAS references. Delete the policy, and every SAS tied to it is revoked.

**What is a user delegation SAS?** A SAS signed with Microsoft Entra ID credentials. Wiz notes its expiry is capped at 7 days and it records who created it.

The AI angle is scale: research teams move huge training datasets, and an account-wide link is the fastest way to share them. As Wiz puts it, "the massive amounts of data they handle require additional security checks and safeguards."

---

## Five Fixes, Cheapest First

### 1. Scope every link to one container or blob, with read access

Grant read on the exact path the reader needs. Keep public data in a dedicated storage account.

### 2. Give links an hour of life

MSRC: "Azure Storage recommends 1 hour or less for all SAS URLs." For long-lived public downloads, publish to a public container or release artifact.

### 3. Make every link revocable and attributable

Use a Service SAS bound to a stored access policy, or a user delegation SAS. Disable Shared Key authorization on accounts holding internal data, and log SAS-authenticated reads.

### 4. Scan for permissions, then review dismissals

Run secret scanning with push protection, and grade SAS findings by `sp` (permissions), `se` (expiry) and scope. Send dismissals to a second reviewer: this URL was caught, then closed as a false positive.

### 5. Swap storage secrets locally before they reach AI tools

This incident was a link committed to a public repo. The same strings (SAS URLs, connection strings, account keys) also travel a second path: engineers paste them into AI coding assistants while debugging data pipelines. A local proxy can swap detected secrets for stand-ins before the request leaves the laptop, so the provider and its logs hold the stand-in. Confirm your detector covers SAS signatures (`sig=`) as well as account keys. Secret stand-ins stay as stand-ins in the answer, so a prompt-injected reply leaks a placeholder.

---

## Where This Shows Up in a System Design Interview

Any design that shares files with outsiders (dataset hosting, model distribution, user uploads) needs a presigned-URL story. State three things:

- Links are scoped to one object, grant read access, and expire in minutes to hours.
- Links reference a revocable server-side policy, and issuance is logged with the caller's identity.
- Public data lives in its own bucket or account.

---

## Interview Q&A

- **Why is a presigned URL a credential?** - Anyone holding it can use it until expiry. Scope it, keep it short-lived, and keep it out of source control.
- **Which SAS type for external sharing?** - User delegation SAS, or a Service SAS with a stored access policy. Both support targeted revocation.
- **How do you revoke a leaked link quickly?** - Delete the stored access policy it references. For an Account SAS, rotate the signing key, which also invalidates every other token signed with it.
- **Why does write access on a model store matter?** - Pickle checkpoints execute code on load, so write access becomes a supply-chain path to every downloader.

---

## Sources

- Wiz Research, 38TB of data accidentally exposed by Microsoft AI researchers (September 18, 2023): https://www.wiz.io/blog/38-terabytes-of-private-data-accidentally-exposed-by-microsoft-ai-researchers
- Microsoft Security Response Center, Microsoft mitigated exposure of internal information in a storage account due to overly-permissive SAS token (September 18, 2023): https://www.microsoft.com/en-us/msrc/blog/2023/09/microsoft-mitigated-exposure-of-internal-information-in-a-storage-account-due-to-overly-permissive-sas-token

---

*Disclosure: I build [Pretense](https://pretense.ai/?utm_source=substack&utm_medium=newsletter&utm_campaign=sdl-sas-token-38tb), a local proxy that does fix 5: it swaps detected secrets, such as Azure Storage connection strings and account keys, plus code identifiers, for stand-ins before a request leaves the laptop. Identifiers come back byte-exact; secrets stay as stand-ins in the reply. It covers AI-tool traffic that passes through it, so pair it with fixes 1 to 4 for links in repos and storage.*

{{SUBSCRIBE}}

{{BUTTON:Read More Articles|https://newsletter.systemdesignlaws.xyz}}
