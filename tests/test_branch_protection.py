#!/usr/bin/env python3
"""
Safeguard tests for main branch protection.

Pure JSON assertions on the checked-in ruleset - no browser or network needed,
so this runs under plain `python3 -m unittest discover -s tests`.

Run: python3 -m unittest tests.test_branch_protection -v
"""
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


class TestMainBranchProtection(unittest.TestCase):
    """Checked-in main ruleset blocks deletion, force-pushes, and direct merges."""

    def test_main_branch_protection_never_delete(self):
        """Safeguard: checked-in main ruleset blocks deletion, force-pushes, and direct merges."""
        ruleset_path = REPO / ".github" / "rulesets" / "main.json"
        self.assertTrue(ruleset_path.exists(), "main ruleset file must exist")
        data = json.loads(ruleset_path.read_text())
        self.assertEqual(data.get("target"), "branch")
        self.assertEqual(data.get("enforcement"), "active")
        self.assertEqual(
            data.get("conditions", {}).get("ref_name", {}).get("include"),
            ["refs/heads/main"],
            "ruleset must target refs/heads/main",
        )

        rules_by_type = {rule["type"]: rule for rule in data.get("rules", [])}
        self.assertIn("deletion", rules_by_type, "main ruleset must block deletions")
        self.assertIn("non_fast_forward", rules_by_type, "main ruleset must block force pushes")
        self.assertIn("pull_request", rules_by_type, "main ruleset must require pull requests")
        self.assertIn(
            "required_status_checks",
            rules_by_type,
            "main ruleset must require passing checks",
        )

        required_checks = [
            check["context"]
            for check in rules_by_type["required_status_checks"]["parameters"]["required_status_checks"]
        ]
        self.assertEqual(required_checks, ["test", "e2e-website"])


if __name__ == "__main__":
    unittest.main()
