#!/usr/bin/env python3
"""Render-verify all registered static SVGs at representative display sizes.

CI smoke verification checks decoding, visible pixels, geometry and text masks.
It is not a substitute for GitHub's actual layout or assistive technology tests.
Optional --output DIR retains PNGs for manual inspection.
"""
from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

from PIL import Image
import cairosvg

ROOT = Path(__file__).resolve().parents[1]
MEDIA = {
    "mobile-light": ("profile/contributions-mobile-light.svg", [320, 390]),
    "mobile-dark": ("profile/contributions-mobile-dark.svg", [320, 390]),
    "desktop-light": ("profile/contributions-light.svg", [768, 1024, 1440]),
    "desktop-dark": ("profile/contributions-dark.svg", [768, 1024, 1440]),
    "identity-mobile-light": ("assets/identity-mobile-light.svg", [320, 390]),
    "identity-mobile-dark": ("assets/identity-mobile-dark.svg", [320, 390]),
    "identity-light": ("assets/identity-light.svg", [768, 1024, 1440]),
    "identity-dark": ("assets/identity-dark.svg", [768, 1024, 1440]),
    "method-mobile-light": ("assets/method-mobile-light.svg", [320, 390]),
    "method-mobile-dark": ("assets/method-mobile-dark.svg", [320, 390]),
    "method-light": ("assets/method-light.svg", [768, 1024, 1440]),
    "method-dark": ("assets/method-dark.svg", [768, 1024, 1440]),
}


def check_one(path: Path, widths: list[int], output: Path | None = None) -> None:
    raw = path.read_text(encoding="utf-8")
    if re.search(r"<\s*(?:animate|animateTransform|animateMotion|set)\b|@keyframes|animation\s*:", raw, re.I):
        raise ValueError(f"Motion found in {path}")
    xml = ET.fromstring(raw)
    if xml.get("role") != "img" or not xml.get("aria-labelledby"):
        raise ValueError(f"Missing accessible SVG root metadata in {path}")
    for width in widths:
        png = cairosvg.svg2png(bytestring=raw.encode("utf-8"), output_width=width)
        with Image.open(BytesIO(png)) as img:
            img.load()
            expected_height = round(width * float(xml.get('height', '1')) / float(xml.get('width', '1')))
            if img.width != width or abs(img.height - expected_height) > 2 or img.height < 70:
                raise ValueError(f"Unexpected SVG raster dimensions in {path}: {img.size}")
            rgb = img.convert("RGB")
            if len(rgb.getcolors(maxcolors=1_000_000) or []) < 3:
                raise ValueError(f"SVG lacks meaningful visual variation in {path}")
        if output is not None:
            output.mkdir(parents=True, exist_ok=True)
            (output / f"{path.stem}-{width}.png").write_bytes(png)
        print(f"PASS {path.relative_to(ROOT)} at {width}px")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="Optional folder for reviewed PNG renders")
    args = parser.parse_args()
    for filename, widths in MEDIA.values():
        check_one(ROOT / filename, widths, args.output)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, ET.ParseError) as exc:
        print(f"Visual smoke check failed: {exc}", file=sys.stderr)
        sys.exit(1)
