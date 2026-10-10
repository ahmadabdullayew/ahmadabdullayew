"""Phase 2 maintained positive/negative fixtures for the CommonMark contract."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_profile import validate  # noqa: E402

CASES = json.loads((ROOT / "tests/fixtures/profile_validation_cases.json").read_text(encoding="utf-8"))


class TestReadmeValidationCases(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        for file_name in ("README.md", "profile-spec.json", "PROFILE_ARCHITECTURE.md", "CV.md", "PROJECT_EVIDENCE.md"):
            shutil.copy2(ROOT / file_name, self.root / file_name)
        for subdir in ("assets", "profile", "scripts", ".github/workflows"):
            shutil.copytree(ROOT / subdir, self.root / subdir, dirs_exist_ok=True)

    def test_cases(self):
        for case in CASES:
            with self.subTest(case["name"]):
                destination = self.root / case["target"]
                original = destination.read_text(encoding="utf-8")
                operation = case["operation"]
                if operation == "replace":
                    self.assertIn(case["before"], original, case["name"])
                    modified = original.replace(case["before"], case["after"], 1)
                elif operation == "append":
                    modified = original + case["after"]
                elif operation == "prepend":
                    modified = case["after"] + original
                else:
                    self.fail(f"Unknown fixture operation {operation!r}")
                try:
                    destination.write_text(modified, encoding="utf-8")
                    problems = validate(self.root)
                    if case["valid"]:
                        self.assertEqual(problems, [], f'{case["name"]}: {problems}')
                    else:
                        self.assertTrue(any(case["expected"] in p for p in problems), f'{case["name"]}: {problems}')
                finally:
                    destination.write_text(original, encoding="utf-8")

    def test_canonical_readme(self):
        self.assertEqual(validate(self.root), [])


if __name__ == "__main__":
    unittest.main()
