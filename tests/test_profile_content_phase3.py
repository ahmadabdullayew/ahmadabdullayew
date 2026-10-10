"""Phase 3 content contract and cross-document evidence checks.

These tests validate what is under repository control. They do not assert that
external GitHub links stay live or that downstream experiments have run.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_profile import local_path, parse_readme, validate  # noqa: E402


class Phase3ContentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((ROOT / "profile-spec.json").read_text(encoding="utf-8"))
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.cv = (ROOT / "CV.md").read_text(encoding="utf-8")
        cls.evidence = (ROOT / "PROJECT_EVIDENCE.md").read_text(encoding="utf-8")

    def test_full_profile_remains_valid(self):
        self.assertEqual(validate(ROOT), [])

    def test_profile_prioritizes_featured_evidence(self):
        expected = [
            "About", "Featured Projects", "ML Experience and Research",
            "Technical Foundation", "GitHub Activity", "Current Focus", "Connect",
        ]
        self.assertEqual(self.spec["section_headings"], expected)
        parsed = parse_readme(self.readme, self.spec)
        self.assertEqual(parsed.sections, expected)
        self.assertEqual(parsed.project_headings, [p["name"] for p in self.spec["featured_projects"]])
        self.assertIn('[Technical CV](./CV.md)', self.readme)
        self.assertIn('[Project evidence](./PROJECT_EVIDENCE.md)', self.readme)

    def test_all_featured_projects_have_visible_content(self):
        self.assertNotIn("<details", self.readme)
        self.assertNotIn("</details>", self.readme)
        featured = self.readme.split("## Featured Projects", 1)[1].split("## ML Experience and Research", 1)[0]
        for entry in self.spec["featured_projects"]:
            self.assertIn(f"### {entry['name']} —", featured)
        self.assertIn("**Outcome and limit:**", featured)
        self.assertIn("**Reproduce / inspect:**", featured)

    def test_project_scope_is_not_overclaimed(self):
        self.assertIn("not independently reproduced here", self.readme)
        self.assertIn("**untrained**", self.readme)
        self.assertIn("not a verified executable optimizer", self.readme)
        self.assertIn("not a deployed website", self.readme)
        self.assertIn("Individual code authorship", self.readme)
        self.assertIn("reported", self.evidence)
        self.assertIn("No downstream repository test suite", self.evidence)

    def test_no_fabricated_remote_resume_or_website(self):
        self.assertTrue((ROOT / "CV.md").is_file())
        self.assertIn("Academic Website — source repository", self.readme)
        self.assertNotIn("```yaml", self.readme)
        self.assertIn("Khazar University", self.cv)
        self.assertIn("not independently established", self.cv)

    def test_supporting_documents_local_links_resolve(self):
        for name in ("CV.md", "PROJECT_EVIDENCE.md"):
            content = (ROOT / name).read_text(encoding="utf-8")
            parsed = parse_readme(content, self.spec)
            self.assertEqual(parsed.errors, [], name)
            for url in parsed.links:
                problems: list[str] = []
                local = local_path(url, "link", problems)
                self.assertEqual(problems, [], f"{name}: {url}")
                if local is None:
                    continue
                path, fragment = local
                if path:
                    file = ROOT / path
                    self.assertTrue(file.is_file(), f"{name}: {url}")
                    self.assertTrue(file.resolve().is_relative_to(ROOT.resolve()))
                else:
                    self.assertIn(fragment, parsed.heading_anchors | parsed.ids)

    def test_evidence_matrix_covers_every_featured_project(self):
        for item in self.spec["featured_projects"]:
            self.assertIn(item["name"], self.readme)
            self.assertIn(item["url"], self.evidence)
        self.assertIn("## Skills and source traceability", self.evidence)
        self.assertIn("10 October 2026", self.evidence)

    def test_cv_does_not_assert_grades_or_jobs(self):
        for phrase in ("GPA:", "IELTS:", "Senior Engineer", "production deployed", "published paper"):
            self.assertNotIn(phrase, self.cv)


if __name__ == "__main__":
    unittest.main()
