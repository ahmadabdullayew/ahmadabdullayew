"""Check evidence-first composition inspired by the curated GitHub profile examples.

These are source-level constraints, not a claim of live GitHub browser WCAG testing.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
README = ROOT.joinpath('README.md').read_text(encoding='utf-8')


class EvidenceFirstUxTests(unittest.TestCase):
    def test_first_screen_is_text_led_and_all_four_projects_are_one_click_away(self):
        intro = README.split('## About', 1)[0]
        self.assertIn('# Ahmad Abdullayev', intro)
        for slug in ('Asan-Appeal', '/Bahar)', 'EO-Drought-Intelligence', 'DBMS-Report'):
            self.assertIn(slug, intro)
        self.assertIn('[Project evidence](./PROJECT_EVIDENCE.md)', intro)
        self.assertIn('[Technical CV](./CV.md)', intro)
        self.assertIn('assets/identity-light.svg', intro)
        self.assertNotIn('<details', intro)

    def test_reading_effort_is_bounded_and_sections_are_plainly_visible(self):
        self.assertLess(len(README.split()), 950)
        area = README.split('## Featured Projects', 1)[1].split('## ML Experience', 1)[0]
        self.assertEqual(len(re.findall(r'^### ', area, flags=re.M)), 4)
        self.assertEqual(area.count('**Outcome and limit:**'), 4)
        self.assertEqual(area.count('**Reproduce / inspect:**'), 4)
        self.assertNotIn('<details', area)

    def test_no_unowned_external_ornaments_or_animated_widgets(self):
        self.assertNotRegex(README, r'<img[^>]+src=["\']https?://')
        self.assertNotIn('img.shields.io', README)
        self.assertNotIn('readme-typing-svg', README)
        self.assertNotIn('<marquee', README)
        self.assertTrue((ROOT/'UI_UX_REFERENCE_REVIEW.md').is_file())

    def test_reading_order_and_semantics(self):
        self.assertLess(README.index('## Featured Projects'), README.index('## GitHub Activity'))
        self.assertIn('Static contribution snapshot', README)
        self.assertIn('./profile/contributions-summary.md', README)
        self.assertIn('prefers-color-scheme: dark', README)


if __name__ == '__main__':
    unittest.main()
