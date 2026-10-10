# Visual and accessibility review — Phase 4

**Last local static/raster review:** 2026-10-10. **Deployment review:** pending push to GitHub.
The profile is a GitHub-hosted Markdown document, not a separately deployed website. This review does **not** claim a live GitHub browser or screen-reader audit.

## Design contract

1. Plain semantic H1 and H2/H3 headings communicate identity and all four featured projects; no project is gated behind `<details>` or pointer-only behavior.
2. There are **no externally embedded images, animated images, GIFs, SVG SMIL animation, CSS animation or motion dependencies**. Reduced-motion needs no special fallback for these static assets.
3. Desktop (over 640px) uses a full GitHub contribution grid. Mobile (up to 640px) shows the most recent six calendar-month **numeric totals**, not illegible daily cells. Partial months are marked as potentially partial.
4. `<picture>` prioritizes mobile-dark, mobile-light, then desktop-dark, and has an unconditional desktop-light `<img>` fallback. Dark/light assets retain separate foreground/background palettes.
5. Both visualizations have descriptive SVG title/description, informative HTML alt text, and an adjacent **accessible numerical Markdown equivalent** (`profile/contributions-summary.md`) with each reporting date and count. The image is supplemental, and a GitHub link provides current data.
6. Do not infer skill from the contribution chart; stale snapshots are labeled as such.
7. No decorative asset may precede the first substantive professional evidence. The former banner and operating-model diagram were removed because their text was duplicated and illegible when shrunk.

## Automated checks

Install requirements and run:

```bash
python3 -m pip install -r requirements-validation.txt -r requirements-visual.txt
python3 scripts/validate_profile.py
python3 -m unittest discover -s tests -v
python3 scripts/check_visuals.py --output /tmp/profile-renders
```

`check_visuals.py` renders all four SVGs using CairoSVG and Pillow at **320, 390, 768, 1024 and 1440 CSS pixel-equivalent widths** as appropriate to the chosen asset. It tests decoding, positive dimensions, variation, and disallowed motion. Generated PNGs are **review artifacts, not checked-in assets**. Structural tests check the responsive `<picture>` policy, file registration, actual project headings, accessibility metadata and summary/SVG count consistency.

## Manual post-push GitHub verification — REQUIRED

After publication, review the **real** GitHub-rendered profile on these combinations:

| View | Width | Theme | Expected |
| --- | ---: | --- | --- |
| Narrow mobile | 320 px | Light & dark | Six-month numeric graphic with readable text; H1 and project links readable; no horizontal overflow |
| Mobile | 390 px | Light & dark | Same mobile picture variant with no clipped labels |
| Tablet | 768 px | Light & dark | Full contribution chart; all project headings expanded |
| Desktop | 1024 px | Light & dark | Full chart and normal evidence links |
| Wide desktop | 1440 px | Light & dark | Good reading measure and no unexpected image scaling |

Additionally, verify keyboard focus on all links, linear reading order with a screen reader (NVDA/VoiceOver/Orca as available), image alternatives, contrast, table navigation, lack of motion, responsive `currentSrc` selection, and actual destination URLs. Test browser zoom at 200% and 400% when practical. Browser/GitHub sanitation can differ from local Markdown parsing. **Do not mark these checks complete based only on local raster tests.**

If a theme, responsive image, or link fails in live GitHub, use the text summary and live GitHub link as functional fallbacks, then correct the source and rerun the entire contract.

## Review triggers

Review after changing a heading, image, theme palette, generator, viewBox, project order, or HTML structure, and after major GitHub rendering updates. Keep the inspection date and unresolved problems explicit.
