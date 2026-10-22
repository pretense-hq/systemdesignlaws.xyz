#!/usr/bin/env python3
"""
Safeguard tests for the GitHub Pages custom domain (CNAME).

GitHub Pages binds exactly ONE custom domain per site and re-reads the CNAME
file on every build. A CNAME carrying more than one hostname leaves the domain
unbound, so the apex resolves to the Pages IPs but Pages serves
"There isn't a GitHub Pages site here" - a 404 for the whole site.

Pure file assertions - no browser or network needed, so this runs under plain
`python3 -m unittest discover -s tests`.

Run: python3 -m unittest tests.test_pages_custom_domain -v
"""
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

APEX = "systemdesignlaws.xyz"
# newsletter.* is served by Substack (Cloudflare), never by GitHub Pages.
SUBSTACK_HOST = "newsletter.systemdesignlaws.xyz"


def read_domains(path):
    """Non-empty, stripped lines of a CNAME file."""
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


class TestPagesCustomDomain(unittest.TestCase):
    """Root CNAME binds a single apex domain to GitHub Pages."""

    def setUp(self):
        self.cname = REPO / "CNAME"
        self.assertTrue(self.cname.exists(), "root CNAME file must exist")

    def test_cname_has_exactly_one_domain(self):
        """GitHub Pages supports one custom domain; extra lines unbind the site."""
        domains = read_domains(self.cname)
        self.assertEqual(
            len(domains), 1,
            f"CNAME must list exactly one domain, found {len(domains)}: {domains}",
        )

    def test_cname_is_the_apex_domain(self):
        """Apex is canonical; Pages redirects the www variant to it automatically."""
        self.assertEqual(read_domains(self.cname)[0], APEX)

    def test_cname_does_not_claim_substack_hosts(self):
        """newsletter.* points at Substack - Pages must never claim it."""
        for domain in read_domains(self.cname):
            self.assertNotIn(
                SUBSTACK_HOST, domain,
                f"CNAME must not claim Substack host {SUBSTACK_HOST!r} (found {domain!r})",
            )

    def test_cname_ends_with_newline(self):
        """A trailing newline keeps the file POSIX-clean and diff-friendly."""
        self.assertTrue(
            self.cname.read_text().endswith("\n"),
            "CNAME must end with a newline",
        )

    def test_redirect_site_cname_has_exactly_one_domain(self):
        """The separate newsletter-redirect site has the same one-domain rule."""
        redirect_cname = REPO / "newsletter-redirect" / "CNAME"
        if not redirect_cname.exists():
            self.skipTest("newsletter-redirect/CNAME not present")
        domains = read_domains(redirect_cname)
        self.assertEqual(
            len(domains), 1,
            f"newsletter-redirect/CNAME must list exactly one domain, found {domains}",
        )


if __name__ == "__main__":
    unittest.main()
