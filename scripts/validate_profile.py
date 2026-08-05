#!/usr/bin/env python3
"""Validate the profile README and local visual assets using the standard library."""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

FORBIDDEN_PATTERNS = {
    "profile-view counter": r"komarev\.com/ghpvc",
    "typing animation": r"readme-typing-svg",
    "trophy wall": r"github-profile-trophy",
    "contribution snake": r"snake",
}

LOCAL_IMAGE_PATTERN = re.compile(
    r'<img\s+[^>]*src="(?P<src>\./[^"]+)"[^>]*alt="(?P<alt>[^"]*)"',
    re.IGNORECASE,
)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not README.is_file():
        fail("README.md is missing")

    text = README.read_text(encoding="utf-8")

    for label, pattern in FORBIDDEN_PATTERNS.items():
        if re.search(pattern, text, flags=re.IGNORECASE):
            fail(f"forbidden decorative component detected: {label}")

    local_images = list(LOCAL_IMAGE_PATTERN.finditer(text))
    if not local_images:
        fail("no local profile visuals were found")

    for match in local_images:
        source = match.group("src")
        alt = match.group("alt").strip()
        if not alt:
            fail(f"missing alt text for {source}")

        file_path = ROOT / source.removeprefix("./")
        if not file_path.is_file():
            fail(f"referenced asset does not exist: {source}")

        if file_path.suffix.lower() == ".svg":
            try:
                tree = ET.parse(file_path)
            except ET.ParseError as exc:
                fail(f"invalid SVG XML in {source}: {exc}")

            svg_root = tree.getroot()
            if svg_root.attrib.get("role") != "img":
                fail(f'{source} must declare role="img"')

            ns = {"svg": "http://www.w3.org/2000/svg"}
            title = svg_root.find("svg:title", ns)
            desc = svg_root.find("svg:desc", ns)
            if title is None or not (title.text or "").strip():
                fail(f"{source} is missing an accessible title")
            if desc is None or not (desc.text or "").strip():
                fail(f"{source} is missing an accessible description")

    required_sections = [
        "## Engineering profile",
        "## Selected systems",
        "## Operating model",
        "## Technical foundation",
        "## Evidence standard",
    ]
    for section in required_sections:
        if section not in text:
            fail(f"required section is missing: {section}")

    print(
        f"Profile validation passed: {len(local_images)} local visuals, "
        f"{len(required_sections)} required sections."
    )


if __name__ == "__main__":
    main()
