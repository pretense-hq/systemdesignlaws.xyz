"""robots.txt, sitemap.xml and the Search Console file agree with the Pages custom domain (CNAME)."""
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


class SeoFilesTest(unittest.TestCase):
    def setUp(self):
        self.domain = (REPO / "CNAME").read_text().strip()
        self.origin = f"https://{self.domain}/"

    def test_robots_allows_crawl_and_points_at_sitemap_on_custom_domain(self):
        robots = (REPO / "robots.txt").read_text()
        self.assertRegex(robots, r"(?mi)^User-agent:\s*\*\s*$")
        self.assertNotRegex(robots, r"(?mi)^Disallow:\s*/\s*$")
        self.assertEqual(re.findall(r"(?mi)^Sitemap:\s*(\S+)\s*$", robots), [self.origin + "sitemap.xml"])

    def test_sitemap_is_valid_and_every_loc_is_on_custom_domain(self):
        root = ET.parse(REPO / "sitemap.xml").getroot()
        locs = [e.text.strip() for e in root.findall("sm:url/sm:loc", NS)]
        self.assertIn(self.origin, locs)
        for loc in locs:
            self.assertTrue(loc.startswith(self.origin), loc)

    def test_search_console_file_names_itself(self):
        files = list(REPO.glob("google*.html"))
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].read_text().strip(), f"google-site-verification: {files[0].name}")


if __name__ == "__main__":
    unittest.main()
