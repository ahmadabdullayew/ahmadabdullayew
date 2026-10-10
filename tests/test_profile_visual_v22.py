"""Visual design contracts: meaningful artwork, source-owned images and responsive variants."""
from __future__ import annotations
from pathlib import Path
import json
import re
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
S='{http://www.w3.org/2000/svg}'
SPEC=json.loads((ROOT/'profile-spec.json').read_text())
README=(ROOT/'README.md').read_text()

class VisualV22Tests(unittest.TestCase):
    def test_eight_registered_maintained_assets_and_four_generated(self):
        entries=SPEC['assets']
        self.assertEqual(len(entries),12)
        maintained=[e for e in entries if e['kind']=='maintained']
        generated=[e for e in entries if e['kind']=='generated']
        self.assertEqual(len(maintained),8)
        self.assertEqual(len(generated),4)
        for entry in maintained:
            self.assertEqual(entry['owner'],'PROFILE_VISUAL_DESIGN.md')
            self.assertTrue((ROOT/entry['path']).is_file())
            self.assertIn('./'+entry['path'],README)

    def test_theme_and_mobile_routing_for_both_new_families(self):
        for family in ('identity','method'):
            main=f'./assets/{family}-light.svg'
            i=README.index(main)
            block=README[README.rfind('<picture>',0,i):README.find('</picture>',i)+len('</picture>')]
            self.assertIn(f'./assets/{family}-dark.svg',block)
            self.assertIn(f'./assets/{family}-mobile-light.svg',block)
            self.assertIn(f'./assets/{family}-mobile-dark.svg',block)
            self.assertEqual(block.count('<source '),3)
            self.assertIn('prefers-color-scheme: dark',block)
            self.assertIn('max-width: 640px',block)
            self.assertRegex(block,r'<img .*alt="[^"]{40,}" width="100%"')

    def test_svg_meta_no_motion_no_external_references(self):
        for asset in (ROOT/'assets').glob('*.svg'):
            with self.subTest(asset=asset.name):
                xml=ET.parse(asset).getroot()
                self.assertEqual(xml.get('role'),'img')
                self.assertEqual(xml.get('aria-labelledby'),'title desc')
                self.assertTrue(''.join(xml.find(S+'title').itertext()).strip())
                self.assertTrue(''.join(xml.find(S+'desc').itertext()).strip())
                text=asset.read_text()
                self.assertNotRegex(text,r'(?i)<script|<animate|@keyframes|<foreignObject|https?://(?!www.w3.org/2000/svg)')

    def test_project_evidence_and_scope_intact(self):
        for name in ('ASANAppeal AI','Bahar Operations','EO Drought Intelligence','Neural Branch-and-Bound Accelerator'):
            self.assertIn('### '+name,README)
        self.assertIn('136 passed, 5 skipped', README)
        self.assertIn('not independently reproduced here', README)
        self.assertIn('not a verified executable optimizer', README)
        self.assertIn('./profile/contributions-summary.md', README)

    def test_method_is_not_claimed_as_completed_research(self):
        self.assertIn('working principles, not a claim that every public project has completed every stage',README)
        self.assertIn('## Technical Foundation',README)
        self.assertLess(README.index('assets/method-light.svg'),README.index('## GitHub Activity'))

    def test_no_remote_widgets_or_script_and_review_doc(self):
        self.assertNotIn('img.shields.io',README)
        self.assertNotIn('readme-typing-svg',README)
        self.assertTrue((ROOT/'PROFILE_VISUAL_DESIGN.md').is_file())
        self.assertLess(len(README.split()),1000)

if __name__=='__main__':unittest.main()
