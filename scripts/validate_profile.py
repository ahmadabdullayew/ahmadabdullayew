#!/usr/bin/env python3
"""Validate the GitHub profile's authoritative Phase 1/2 contract.

The README is parsed as CommonMark rather than regex-scanned. Only rendered
Markdown and HTML elements are inspected; source code, comments and code fences
are not treated as live profile content. No remote requests are made.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
SPEC_FILE = "profile-spec.json"
SVG_NS = "http://www.w3.org/2000/svg"
IMAGE_EXTENSIONS = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"}
VOID_HTML = {"img", "source", "br", "hr", "input", "meta", "link"}
GENERIC_ALTS = {"image", "picture", "photo", "graphic", "svg", "icon", "illustration"}
MD = MarkdownIt("commonmark", {"html": True}).enable("table")


@dataclass(frozen=True)
class ImageRef:
    url: str
    alt: str
    context: str
    decorative: bool = False
    functional: bool = False


@dataclass
class ReadmeContent:
    sections: list[str]
    heading_anchors: set[str]
    images: list[ImageRef]
    links: list[str]
    summary_labels: list[str]
    project_headings: list[str]
    ids: set[str]
    errors: list[str]


def slugify(label: str) -> str:
    """GitHub-compatible slug for ordinary Markdown headings (not a GFM renderer)."""
    value = re.sub(r"<[^>]+>", "", label).strip().lower()
    value = "".join(char for char in value if char.isalnum() or char in "_- ")
    return value.replace(" ", "-")


def _text_from_inline(token) -> str:
    if not token or not token.children:
        return token.content if token else ""
    return "".join(child.content for child in token.children if child.type in {"text", "code_inline", "html_inline"}).strip()


class ProfileHTMLCollector(HTMLParser):
    """Collect real HTML elements (not commented/code-fenced examples)."""

    def __init__(self, permitted: set[str]):
        super().__init__(convert_charrefs=True)
        self.permitted = permitted
        self.stack: list[str] = []
        self.picture_fallbacks: list[bool] = []
        self.images: list[ImageRef] = []
        self.links: list[str] = []
        self.summaries: list[str] = []
        self.summary_buffer: list[str] | None = None
        self.ids: set[str] = set()
        self.errors: list[str] = []

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_HTML:
            self.handle_endtag(tag)

    def handle_starttag(self, tag, attrs):
        if tag not in self.permitted:
            self.errors.append(f"unsupported HTML component: <{tag}>")
        attributes = dict(attrs)
        attr_counts = Counter(name for name, _ in attrs)
        for name, count in attr_counts.items():
            if count > 1:
                self.errors.append(f"duplicate HTML attribute {name} on <{tag}>")
        for name, val in attrs:
            if name.startswith("on"):
                self.errors.append(f"unsafe HTML event attribute {name} on <{tag}>")
            if name == "id":
                if not val or val in self.ids:
                    self.errors.append(f"empty or duplicate HTML id: {val!r}")
                else:
                    self.ids.add(val)
        if tag == "picture":
            self.picture_fallbacks.append(False)
        if tag == "img":
            if "picture" in self.stack and self.picture_fallbacks:
                self.picture_fallbacks[-1] = True
            source = attributes.get("src")
            if not source:
                self.errors.append("HTML <img> requires src")
            role = attributes.get("role", "").lower()
            hidden = attributes.get("aria-hidden", "").lower() == "true"
            alt = attributes.get("alt")
            decorative = alt == "" and role in {"presentation", "none"} and hidden
            functional = "a" in self.stack
            if alt is None:
                self.errors.append("HTML <img> is missing alt attribute")
            if source:
                self.images.append(ImageRef(source, alt or "", "HTML <img>", decorative, functional))
            if attributes.get("srcset"):
                self._srcset(attributes["srcset"], alt or "", "HTML <img srcset>", decorative, functional)
        if tag == "source":
            if "picture" not in self.stack:
                self.errors.append("HTML <source> must appear inside <picture>")
            if not attributes.get("srcset") and not attributes.get("src"):
                self.errors.append("HTML <source> requires srcset or src")
            for name in ("src", "srcset"):
                if attributes.get(name):
                    if name == "srcset":
                        self._srcset(attributes[name], "", "HTML <source srcset>")
                    else:
                        self.images.append(ImageRef(attributes[name], "", "HTML <source>"))
        if tag == "a":
            href = attributes.get("href")
            if not href:
                self.errors.append("HTML <a> missing href")
            else:
                self.links.append(href)
        if tag == "summary":
            if "details" not in self.stack:
                self.errors.append("HTML <summary> must appear inside <details>")
            self.summary_buffer = []
        if tag not in VOID_HTML:
            self.stack.append(tag)

    def _srcset(self, srcset: str, alt: str, context: str, decorative=False, functional=False):
        # External image URLs and data URIs are prohibited by policy, so comma
        # splitting is unambiguous for *valid* local candidate URLs.
        candidates = srcset.split(",")
        if not candidates or any(not candidate.strip() for candidate in candidates):
            self.errors.append(f"invalid empty srcset candidate in {context}")
        for candidate in candidates:
            parts = candidate.split()
            if not parts:
                continue
            if len(parts) > 2 or (len(parts) == 2 and not re.fullmatch(r"(?:[1-9]\d*w|(?:\d+(?:\.\d+)?)x)", parts[1])):
                self.errors.append(f"invalid srcset descriptor: {candidate.strip()!r}")
            self.images.append(ImageRef(parts[0], alt, context, decorative, functional))

    def handle_endtag(self, tag):
        if tag in VOID_HTML:
            self.errors.append(f"void HTML element has closing tag: </{tag}>")
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"mismatched closing HTML element: </{tag}>")
            return
        if tag == "picture" and self.picture_fallbacks:
            if not self.picture_fallbacks.pop():
                self.errors.append("HTML <picture> must contain an <img> fallback")
        if tag == "summary" and self.summary_buffer is not None:
            label = " ".join(" ".join(self.summary_buffer).split())
            self.summaries.append(label.split(" — ", 1)[0])
            self.summary_buffer = None
        self.stack.pop()

    def handle_data(self, data):
        if self.summary_buffer is not None:
            self.summary_buffer.append(data)


def parse_readme(readme: str, spec: dict) -> ReadmeContent:
    tokens = MD.parse(readme)
    permitted = set(spec.get("component_policy", {}).get("allowed_html_tags", []))
    html = ProfileHTMLCollector(permitted)
    sections = []
    project_headings: list[str] = []
    in_featured_projects = False
    anchors: set[str] = set()
    anchor_counts: Counter = Counter()
    images: list[ImageRef] = []
    links: list[str] = []

    structural_nesting = 0
    for index, token in enumerate(tokens):
        if token.type in {"blockquote_open", "list_item_open"}:
            structural_nesting += 1
        if token.type == "heading_open":
            heading = tokens[index + 1] if index + 1 < len(tokens) else None
            heading_label = _text_from_inline(heading)
            base = slugify(heading_label)
            suffix = anchor_counts[base]
            anchor_counts[base] += 1
            anchors.add(base if suffix == 0 else f"{base}-{suffix}")
            if token.tag == "h2" and structural_nesting == 0:
                sections.append(heading_label)
                in_featured_projects = heading_label == "Featured Projects"
            elif token.tag == "h3" and structural_nesting == 0 and in_featured_projects:
                project_headings.append(heading_label.split(" — ", 1)[0].strip())
        if token.type in {"html_block", "html_inline"}:
            html.feed(token.content)
        if token.type in {"blockquote_close", "list_item_close"}:
            structural_nesting -= 1
        if token.type != "inline":
            continue
        for child in token.children or []:
            if child.type == "image":
                images.append(ImageRef(child.attrGet("src") or "", child.content, "Markdown image"))
            elif child.type == "link_open":
                links.append(child.attrGet("href") or "")
            elif child.type == "html_inline":
                html.feed(child.content)
    html.close()
    return ReadmeContent(sections, anchors, images + html.images, links + html.links, html.summaries, project_headings, html.ids, html.errors + ([f"unclosed HTML element: <{t}>" for t in html.stack]))


def local_path(url: str, kind: str, errors: list[str]) -> tuple[str, str] | None:
    """Return normalized local file path and fragment; reject dangerous schemes."""
    value = url.strip()
    if not value:
        errors.append(f"empty {kind} URL")
        return None
    if value.startswith("//"):
        errors.append(f"protocol-relative {kind} URL not permitted: {value[:100]}")
        return None
    try:
        parsed = urlsplit(value)
    except ValueError as exc:
        errors.append(f"malformed {kind} URL {value[:120]!r}: {exc}")
        return None
    if parsed.scheme or parsed.netloc:
        if kind == "image":
            errors.append(f"external/embedded image is prohibited: {value[:120]}")
        elif parsed.scheme.lower() in {"http", "https"} and parsed.netloc:
            return None
        elif parsed.scheme.lower() == "mailto" and parsed.path and "@" in parsed.path:
            return None
        else:
            errors.append(f"unsupported/unsafe link scheme: {value[:120]}")
        return None
    path = unquote(parsed.path)
    fragment = unquote(parsed.fragment)
    if "\\" in path or path.startswith("/") or re.search(r"[\x00-\x1f]", path) or parsed.query:
        errors.append(f"unsupported local {kind} URL: {value[:120]}")
        return None
    normalized = Path(path.removeprefix("./")).as_posix() if path else ""
    if path and (".." in Path(normalized).parts or normalized in {"", "."}):
        errors.append(f"unsafe local {kind} URL: {value[:120]}")
        return None
    if kind == "image" and (not normalized or fragment):
        errors.append(f"unsupported local image path: {value[:120]}")
        return None
    return normalized, fragment


def validate_svg(file: Path, display_path: str) -> list[str]:
    errors: list[str] = []
    try:
        raw = file.read_bytes()
        if re.search(rb"<!\s*(?:DOCTYPE|ENTITY)\b", raw, re.I):
            return [f"SVG {display_path} contains prohibited DTD or entity declaration"]
        root = ET.fromstring(raw)
    except (ET.ParseError, OSError, ValueError) as exc:
        return [f"invalid SVG XML in {display_path}: {exc}"]
    if root.tag != f"{{{SVG_NS}}}svg":
        errors.append(f"SVG {display_path} has no SVG-namespace root")
    if root.get("role") != "img":
        errors.append(f'SVG {display_path} must declare role="img"')
    numbers: dict[str, float] = {}
    for name in ("width", "height"):
        value = root.get(name, "")
        match = re.fullmatch(r"(\d+(?:\.\d+)?)(?:px)?", value)
        if not match or not math.isfinite(float(match[1])) or float(match[1]) <= 0:
            errors.append(f"SVG {display_path} has invalid positive {name}: {value!r}")
        else:
            numbers[name] = float(match[1])
    view_box = root.get("viewBox", "")
    try:
        coords = [float(x) for x in re.split(r"[,\s]+", view_box.strip())]
        if len(coords) != 4 or not all(math.isfinite(x) for x in coords) or coords[2] <= 0 or coords[3] <= 0:
            raise ValueError("four finite numbers with positive extent expected")
        if len(numbers) == 2 and not math.isclose(numbers["width"] / numbers["height"], coords[2] / coords[3], rel_tol=0.01):
            errors.append(f"SVG {display_path} width/height aspect ratio disagrees with viewBox")
    except ValueError:
        errors.append(f"SVG {display_path} has invalid viewBox: {view_box!r}")
    seen_ids: set[str] = set()
    for element in root.iter():
        id_value = element.get("id")
        if id_value:
            if id_value in seen_ids:
                errors.append(f"SVG {display_path} has duplicate id {id_value!r}")
            seen_ids.add(id_value)
        name = element.tag.rsplit("}", 1)[-1].lower()
        if name in {"animate", "animatemotion", "animatetransform", "set"}:
            errors.append(f"SVG {display_path} has prohibited motion element <{name}>")
        if name == "style" and re.search(r"(?:animation(?:-name|-duration|-iteration-count)?|@keyframes|transition)(?:\s*:|\s+)", "".join(element.itertext()), re.I):
            errors.append(f"SVG {display_path} includes prohibited CSS animation")
        if name in {"script", "foreignobject"}:
            errors.append(f"SVG {display_path} includes prohibited <{name}> element")
        for key, value in element.attrib.items():
            local_key = key.rsplit("}", 1)[-1].lower()
            if local_key.startswith("on"):
                errors.append(f"SVG {display_path} contains event attribute {local_key}")
            if local_key == "href" and (value.startswith(("https:", "http:", "//", "data:", "javascript:"))):
                errors.append(f"SVG {display_path} contains remote/unsafe href")
    for title_name in ("title", "desc"):
        node = root.find(f"{{{SVG_NS}}}{title_name}")
        if node is None or not "".join(node.itertext()).strip():
            errors.append(f"SVG {display_path} lacks meaningful <{title_name}>")
        elif not node.get("id"):
            errors.append(f"SVG {display_path} <{title_name}> requires id for aria-labelledby")
    labelled = root.get("aria-labelledby", "").split()
    title = root.find(f"{{{SVG_NS}}}title")
    desc = root.find(f"{{{SVG_NS}}}desc")
    required = {node.get("id") for node in (title, desc) if node is not None and node.get("id")}
    if len(labelled) != len(set(labelled)) or not required or set(labelled) != required:
        errors.append(f"SVG {display_path} aria-labelledby must reference its title and desc exactly")
    if any(x not in seen_ids for x in labelled):
        errors.append(f"SVG {display_path} aria-labelledby contains unresolved id")
    return errors


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        spec = json.loads((root / SPEC_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"missing or invalid specification: {exc}"]
    if not isinstance(spec, dict):
        return ["profile specification must be a JSON object"]
    if spec.get("schema_version") != 1:
        errors.append("unsupported profile specification version")
    if spec.get("readme_path") != "README.md":
        errors.append("readme_path must be README.md")
    readme_file = root / "README.md"
    try:
        readme = readme_file.read_text(encoding="utf-8")
    except OSError as exc:
        return errors + [f"cannot read README.md: {exc}"]

    content = parse_readme(readme, spec)
    errors.extend(content.errors)
    expected = spec.get("section_headings")
    if not isinstance(expected, list) or not expected or len(expected) != len(set(expected)):
        errors.append("section_headings must be a nonempty, unique list")
    elif content.sections != expected:
        errors.append(f"section order differs from profile-spec.json; expected {expected!r}, found {content.sections!r}")

    publication = spec.get("publication", {})
    if publication.get("architecture") != "repository-owned-contribution-calendar-only":
        errors.append("unrecognized publication architecture")
    if publication.get("external_images_allowed") is not False or publication.get("external_image_hosts_allowlist") != []:
        errors.append("the selected publication architecture forbids external embedded images")
    legacy = publication.get("obsolete_analytics_workflow")
    if legacy != ".github/workflows/update-profile-stats.yml" or (root / legacy).exists():
        errors.append("obsolete statistics workflow must remain removed")

    assets = spec.get("assets", [])
    if not isinstance(assets, list) or not assets:
        return errors + ["asset registry must be a nonempty list"]
    asset_paths: set[str] = set()
    for item in assets:
        if not isinstance(item, dict):
            errors.append("asset registry entries must be objects")
            continue
        path = item.get("path", "")
        if not isinstance(path, str) or not path.startswith(("assets/", "profile/")) or ".." in Path(path).parts or Path(path).suffix.lower() not in IMAGE_EXTENSIONS:
            errors.append(f"invalid asset registry path: {path!r}")
            continue
        if path in asset_paths:
            errors.append(f"duplicate asset registration: {path}")
        asset_paths.add(path)
        file = root / path
        if not file.is_file() or not file.resolve().is_relative_to(root.resolve()):
            errors.append(f"registered asset missing or outside repository: {path}")
            continue
        if file.suffix.lower() == ".svg":
            errors.extend(validate_svg(file, path))
        kind = item.get("kind")
        if kind == "generated":
            owner, workflow = item.get("owner", ""), item.get("publishing_workflow", "")
            if not (root / owner).is_file() or not (root / workflow).is_file():
                errors.append(f"missing generator/workflow for {path}")
            elif Path(path).name not in (root / workflow).read_text(encoding="utf-8"):
                errors.append(f"publishing workflow does not explicitly own {path}")
        elif kind != "maintained" or not item.get("owner"):
            errors.append(f"asset ownership unspecified for {path}")
    disk_assets = {p.relative_to(root).as_posix() for directory in ("assets", "profile") if (root / directory).exists() for p in (root / directory).rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS}
    if disk_assets != asset_paths:
        errors.append(f"asset registry differs from files on disk; unregistered={sorted(disk_assets - asset_paths)}, absent={sorted(asset_paths - disk_assets)}")

    summary_path = publication.get("accessible_summary")
    if summary_path != "profile/contributions-summary.md" or not (root / str(summary_path)).is_file():
        errors.append("accessible contribution summary is missing or incorrectly registered")
    image_paths: set[str] = set()
    for item in content.images:
        path_info = local_path(item.url, "image", errors)
        if path_info is None:
            continue
        path, _ = path_info
        image_paths.add(path)
        if not (root / path).is_file() or not (root / path).resolve().is_relative_to(root.resolve()):
            errors.append(f"broken local image path: {path}")
        if path not in asset_paths:
            errors.append(f"unregistered image: {path}")
        if item.context != "HTML <source srcset>" and item.context != "HTML <source>":
            if item.decorative:
                if item.functional:
                    errors.append(f"linked functional image cannot be decorative: {path}")
            elif not item.alt.strip() or item.alt.strip().lower() in GENERIC_ALTS:
                errors.append(f"image lacks meaningful alternative text: {path} ({item.context})")
    if not image_paths:
        errors.append("README has no registered local visuals")
    for item in assets:
        if not isinstance(item, dict):
            continue
        if item.get("readme_required") and item.get("path") not in image_paths:
            errors.append(f"required registered image is not referenced in README: {item.get('path')}")

    anchors = content.heading_anchors | content.ids
    for href in content.links:
        info = local_path(href, "link", errors)
        if info is None:
            continue
        local, fragment = info
        if not local and not fragment:
            errors.append("empty local hyperlink")
        if not local:
            if fragment not in anchors:
                errors.append(f"broken README fragment link: #{fragment}")
            continue
        target = root / local
        if not target.is_file() or not target.resolve().is_relative_to(root.resolve()):
            errors.append(f"broken local link target: {local}")
        elif fragment and target.suffix.lower() == ".md":
            try:
                target_content = parse_readme(target.read_text(encoding="utf-8"), spec)
                if fragment not in (target_content.heading_anchors | target_content.ids):
                    errors.append(f"broken Markdown fragment link: {local}#{fragment}")
            except OSError:
                errors.append(f"unreadable local Markdown link: {local}")

    selected = spec.get("featured_projects", [])
    if not isinstance(selected, list) or any(not isinstance(entry, dict) for entry in selected):
        errors.append("featured_projects must be an array of objects")
        selected = []
    names = [entry.get("name") for entry in selected]
    if content.project_headings != names:
        errors.append(f"featured project order differs from specification: {content.project_headings!r}")
    for project in selected:
        if project.get("url") not in content.links:
            errors.append(f"missing project link: {project.get('name')}")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Profile validation passed: README syntax, links, assets, accessibility metadata, publication policy and project order.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
