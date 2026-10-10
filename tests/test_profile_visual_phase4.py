"""Phase 4 content, visual, responsive and accessibility regression checks."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_contributions import monthly_activity, render_svg, render_mobile_svg, render_summary
from validate_profile import validate_svg

SVG = "{http://www.w3.org/2000/svg}"


class VisualPhase4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.spec = json.loads((ROOT / "profile-spec.json").read_text(encoding="utf-8"))
        cls.summary = (ROOT / "profile/contributions-summary.md").read_text(encoding="utf-8")

    def test_first_screen_contains_identity_and_project_links(self):
        top = self.readme.split("## About", 1)[0]
        self.assertIn("# Ahmad Abdullayev", top)
        self.assertIn("Asan-Appeal", top)
        self.assertIn("Bahar", top)
        self.assertIn("./CV.md", top)
        self.assertNotIn("<img", top)

    def test_projects_are_discoverable_headings(self):
        featured = self.readme.split("## Featured Projects", 1)[1].split("## ML Experience", 1)[0]
        titles = re.findall(r"^### ([^\n]+)", featured, flags=re.M)
        self.assertEqual([t.split(" — ")[0] for t in titles], [p["name"] for p in self.spec["featured_projects"]])
        self.assertNotIn("<details", self.readme)

    def test_all_images_are_owned_and_local(self):
        assets = {x["path"] for x in self.spec["assets"]}
        self.assertEqual(len(assets), 4)
        for item in assets:
            self.assertIn(f'./{item}', self.readme)
            self.assertTrue((ROOT / item).is_file())
        self.assertNotIn('src="https://', self.readme)
        self.assertNotIn('readme-typing-svg', self.readme)
        self.assertFalse((ROOT / 'assets').exists())

    def test_responsive_source_order_matches_dark_and_light(self):
        sources = re.findall(r'<source media="([^"]+)" srcset="([^"]+)"', self.readme)
        self.assertEqual(sources, [
            ('(max-width: 640px) and (prefers-color-scheme: dark)', './profile/contributions-mobile-dark.svg'),
            ('(max-width: 640px)', './profile/contributions-mobile-light.svg'),
            ('(prefers-color-scheme: dark)', './profile/contributions-dark.svg'),
        ])
        self.assertIn('src="./profile/contributions-light.svg"', self.readme)

    def test_static_animations_disallowed(self):
        for asset in self.spec["assets"]:
            raw = (ROOT / asset["path"]).read_text()
            with self.subTest(asset=asset["path"]):
                self.assertNotRegex(raw, r"(?i)<\s*animate|@keyframes|animation\s*:")
                self.assertEqual(validate_svg(ROOT / asset['path'], asset['path']), [])

    def test_motion_regression_fails_validation(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            file = Path(tmp) / 'motion.svg'
            body = (ROOT / 'profile/contributions-light.svg').read_text()
            file.write_text(body.replace('</svg>', '<animate attributeName="opacity" dur="2s" repeatCount="indefinite"/></svg>'))
            self.assertTrue(any('motion' in e for e in validate_svg(file, 'motion.svg')))

    def test_text_summary_is_numerically_consistent(self):
        match = re.search(r'\*\*Reported contribution total:\*\* ([\d,]+)', self.summary)
        self.assertIsNotNone(match)
        reported = int(match.group(1).replace(',', ''))
        monthly = re.findall(r'^\| (\d{4}-\d{2}) \| (\d+) \| ', self.summary, re.M)
        daily = re.findall(r'^\| (\d{4}-\d{2}-\d{2}) \| (\d+) \|$', self.summary, re.M)
        self.assertGreater(len(daily), 350)
        self.assertEqual(reported, sum(int(x) for _, x in monthly))
        self.assertEqual(reported, sum(int(x) for _, x in daily))
        grouped = Counter()
        for date, num in daily:
            grouped[date[:7]] += int(num)
        self.assertEqual(grouped, dict((month, int(count)) for month, count in monthly))

    def test_svg_totals_match_text_summary(self):
        count = re.search(r'Reported contribution total:\*\* (\d+)', self.summary).group(1)
        for asset in self.spec["assets"]:
            xml = ET.parse(ROOT / asset['path']).getroot()
            desc = xml.find(SVG+'desc')
            self.assertIn(count, ''.join(desc.itertext()))
            self.assertEqual(xml.get('role'), 'img')
            self.assertEqual(xml.get('aria-labelledby'), 'title desc')

    def test_mobile_uses_legible_text_not_dense_cells(self):
        for theme in ('dark','light'):
            xml = ET.parse(ROOT / f'profile/contributions-mobile-{theme}.svg').getroot()
            self.assertEqual(xml.get('width'), '362')
            self.assertFalse(any(elem.find(SVG+'title') is not None for elem in xml.findall(SVG+'rect')))
            labels = ["".join(t.itertext()) for t in xml.findall('.//'+SVG+'text')]
            self.assertIn('contributions', ' '.join(labels))
            self.assertEqual(len([l for l in labels if re.search(r'^[A-Z][a-z]{2} 20\d{2}$', l)]), 6)

    def test_renderer_is_static_for_synthetic_input(self):
        calendar = {"totalContributions":2,"weeks":[{"firstDay":"2026-10-04","contributionDays":[{"date":"2026-10-04","weekday":0,"contributionCount":2,"contributionLevel":"FOURTH_QUARTILE"}]}]}
        for theme in ('dark','light'):
            for fn in (render_svg, render_mobile_svg):
                raw = fn(calendar, 'example', theme)
                self.assertNotIn('<animate', raw)
                self.assertIn('2 contributions', raw)
                ET.fromstring(raw)
        self.assertIn('| 2026-10-04 | 2 |',render_summary(calendar,'example'))

    def test_visual_review_and_link_review_documents_exist(self):
        for name in ('VISUAL_REVIEW.md','LINK_REVIEW.md','CONTENT_REVIEW.md'):
            self.assertTrue((ROOT / name).is_file(),name)


if __name__=='__main__': unittest.main()
