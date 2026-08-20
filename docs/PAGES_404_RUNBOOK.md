# Runbook: systemdesignlaws.xyz returns a GitHub 404

Symptom: `https://systemdesignlaws.xyz/` serves GitHub's
"There isn't a GitHub Pages site here." page instead of the landing page.

## Diagnosis recorded 2026-08-20

DNS is correct and is **not** the cause. Both hostnames resolve to all four
GitHub Pages anycast IPs:

- `systemdesignlaws.xyz` -> 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
- `www.systemdesignlaws.xyz` -> same four IPs
- `newsletter.systemdesignlaws.xyz` -> 104.18.36.24, 172.64.151.232 (Cloudflare / Substack, correct)

Two separate faults were found.

### 1. Pages is switched off on the repository (primary cause - needs a human)

The GitHub REST API reports `has_pages: false` and `visibility: private` for
`pretense-hq/systemdesignlaws.xyz`. There is no Pages site bound to the domain,
so GitHub answers every request for the apex with its own 404 page.

Timeline supports this: the `Update Recent Posts` workflow succeeded daily
through 2026-08-08 and has failed every run from 2026-08-09 onward, with no
configuration commit in between.

Publishing Pages from a **private** repository requires GitHub Team or
Enterprise Cloud. On the Free plan the option is unavailable, which is the
most likely reason Pages became disabled.

**Fix (repository admin, in the GitHub UI):**

1. Settings -> Pages. If the source selector is unavailable, either
   upgrade the `pretense-hq` org to Team, or make this repository public.
2. Set **Source: Deploy from a branch**, **Branch: `main`**, **Folder: `/ (root)`**.
3. Under **Custom domain**, enter `systemdesignlaws.xyz` and save. It must
   match the checked-in `CNAME` exactly.
4. Wait for the certificate to be issued, then tick **Enforce HTTPS**.

Verify:

```bash
curl -sSI https://systemdesignlaws.xyz/ | head -1        # expect 200
curl -sSI https://www.systemdesignlaws.xyz/ | head -1    # expect 301 -> apex
```

### 2. The CNAME file listed three domains (fixed in this repo)

`CNAME` contained:

```
systemdesignlaws.xyz
www.systemdesignlaws.xyz
www.newsletter.systemdesignlaws.xyz
```

GitHub Pages binds **exactly one** custom domain per site and re-reads `CNAME`
on every build. Extra hostnames leave the domain unbound, which reproduces the
same 404 - so this would have re-broken the site the moment Pages was switched
back on.

`www.newsletter.systemdesignlaws.xyz` never belonged here at all:
`newsletter.*` is served by Substack, not Pages.

`CNAME` is now a single line, `systemdesignlaws.xyz`. Pages serves the apex and
redirects the `www.` variant to it automatically, so no second entry is needed.

`tests/test_pages_custom_domain.py` locks this in and runs as part of the
required `test` check.

### 3. GitHub Actions cannot start runs either (same account-level fault)

Every workflow run from 2026-08-19 onward ends as `startup_failure` with
`path: BuildFailed`, zero jobs, and no workflow name - the run is never
created, so this is not a fault in any workflow file. The CI on PR #14
failed to start the same way; only the third-party Socket Security checks
reported.

Combined with `has_pages: false` on a private repo, the leading hypothesis is
an account-level billing or plan problem on the `pretense-hq` organization:
Pages from a private repo needs Team or Enterprise Cloud, and Actions on a
private repo stops dispatching once the included minutes or the payment method
lapse. Both symptoms clear together if that is the cause.

Note the two symptoms began on different dates, so they may not be one event:
`Update Recent Posts` failed *normally* (workflow ran, feed fetch failed) from
2026-08-09, and only degraded to `startup_failure` on 2026-08-19.

**Check first:** Organization settings -> Billing and plans, for a failed
payment, an exhausted spending limit, or a downgrade to Free. Then
Settings -> Actions -> General, to confirm Actions is still enabled.

Until runs dispatch again, the required `test` and `e2e-website` checks cannot
report, so no PR can auto-merge.

## Related, not yet fixed

The daily `Update Recent Posts` workflow fetches
`https://newsletter.systemdesignlaws.xyz/feed` and has failed since 2026-08-09.
Its logs have aged out. Once the apex is serving again, re-run the workflow and
check whether the Substack custom domain also needs re-attaching.
