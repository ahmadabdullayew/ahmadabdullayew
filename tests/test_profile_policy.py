"""Phase 1 contract regression tests (standard library only)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_profile import validate  # noqa: E402


class ProfileContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copy2(ROOT / "README.md", self.root / "README.md")
        shutil.copy2(ROOT / "profile-spec.json", self.root / "profile-spec.json")
        for supporting_document in ("CV.md", "PROJECT_EVIDENCE.md", "profile/contributions-summary.md"):
            (self.root / supporting_document).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / supporting_document, self.root / supporting_document)
        for directory in ("profile", "scripts", ".github/workflows"):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        for spec in json.loads((ROOT / "profile-spec.json").read_text())["assets"]:
            source = ROOT / spec["path"]
            target = self.root / spec["path"]
            shutil.copy2(source, target)
            if spec["kind"] == "generated":
                shutil.copy2(ROOT / spec["owner"], self.root / spec["owner"])
                shutil.copy2(ROOT / spec["publishing_workflow"], self.root / spec["publishing_workflow"])

    def mutate_readme(self, before, after):
        path = self.root / "README.md"
        value = path.read_text()
        self.assertIn(before, value)
        path.write_text(value.replace(before, after, 1))

    def test_actual_contract_is_valid(self):
        self.assertEqual(validate(self.root), [])

    def test_missing_heading_rejected(self):
        self.mutate_readme("## About", "## Wrong heading")
        self.assertTrue(validate(self.root))

    def test_remote_image_rejected(self):
        self.mutate_readme('./profile/contributions-light.svg', 'https://example.com/image.svg')
        self.assertTrue(any('external' in x for x in validate(self.root)))

    def test_unregistered_image_rejected(self):
        self.mutate_readme('./profile/contributions-light.svg', './profile/missing.svg')
        self.assertTrue(any('unregistered' in x for x in validate(self.root)))

    def test_legacy_workflow_rejected(self):
        (self.root / '.github/workflows/update-profile-stats.yml').write_text('name: Obsolete')
        self.assertTrue(any('obsolete' in x for x in validate(self.root)))

    def test_project_order_rejected(self):
        self.mutate_readme('### ASANAppeal AI —', '### Another project —')
        self.assertTrue(any('project order' in x for x in validate(self.root)))

    def test_unregistered_disk_svg_rejected(self):
        shutil.copy2(ROOT / 'profile/contributions-light.svg', self.root / 'profile/orphan.svg')
        self.assertTrue(any('asset registry differs' in x for x in validate(self.root)))

    def test_manifest_controls_headings(self):
        path = self.root / 'profile-spec.json'
        data = json.loads(path.read_text())
        data['section_headings'] = ['About']
        path.write_text(json.dumps(data))
        self.assertTrue(any('section order' in x for x in validate(self.root)))


if __name__ == '__main__':
    unittest.main()
