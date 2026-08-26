---
name: release-integrity
description: Verify a release is trustworthy before or after it ships — npm vs CDN vs git tags vs signatures. Trigger on "release", "publish", "ship it", "is 0.6.x out", "cut a version", "why is the CDN behind".
---

# Integrity is not authenticity

`SHA256SUMS` proves the download was not corrupted. The **signature** proves it came from you. Without it the checksum and the artefact **share one trust origin** — whoever can write to the CDN rewrites both, and every installer verifies happily.

## The four questions, in order

1. **Version agreement.** Ask `registry.npmjs.org/-/package/<pkg>/dist-tags` over HTTP — **never `npm view`**, which answers from a local packument cache and has already produced a false result here. Compare against the CDN's own `latest`.
2. **Signature present.** `GET /releases/<v>/SHA256SUMS.cosign.bundle`. Control it: a version known to be signed must return 200, or your probe is broken.
3. **Tag exists** and points at the built commit. Two published versions here have no tag and are unreproducible.
4. **Channel separation.** If every dist-tag names the same version there is **no canary** — every release reaches 100% of users at once.

## The structural trap

cosign keyless binds identity to the CI workflow (`release.yml:8`: *"SIGNING CANNOT MOVE"*). Hand-publishing does not skip signing — it makes signing **impossible**. If CI is unavailable, signing needs a different mechanism (local key pair, or a non-GitHub OIDC issuer), not a promise to do it later.

## Never

Hand-publish. Publish without a tag. Publish npm and CDN from separate jobs. Let a workflow describe a signature no release carries.
