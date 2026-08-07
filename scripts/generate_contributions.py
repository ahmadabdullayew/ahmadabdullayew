#!/usr/bin/env python3
"""Generate a GitHub-native contribution calendar with restrained premium animation."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request


GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query ContributionCalendar($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          firstDay
          contributionDays {
            date
            contributionCount
            contributionLevel
            weekday
          }
        }
      }
    }
  }
}
"""

PALETTES = {
    "dark": {
        "background": "#0D1117",
        "text": "#C9D1D9",
        "secondary": "#8B949E",
        "border": "#30363D",
        "NONE": "#0D1117",
        "FIRST_QUARTILE": "#0E4429",
        "SECOND_QUARTILE": "#006D32",
        "THIRD_QUARTILE": "#26A641",
        "FOURTH_QUARTILE": "#39D353",
        "accent": "#8B5CF6",
        "accent_strong": "#A78BFA",
        "accent_blue": "#58A6FF",
    },
    "light": {
        "background": "#FFFFFF",
        "text": "#24292F",
        "secondary": "#57606A",
        "border": "#D0D7DE",
        "NONE": "#FFFFFF",
        "FIRST_QUARTILE": "#9BE9A8",
        "SECOND_QUARTILE": "#40C463",
        "THIRD_QUARTILE": "#30A14E",
        "FOURTH_QUARTILE": "#216E39",
        "accent": "#7C3AED",
        "accent_strong": "#8B5CF6",
        "accent_blue": "#0969DA",
    },
}


def fetch_calendar(username: str, token: str) -> dict:
    payload = json.dumps(
        {"query": QUERY, "variables": {"login": username}}
    ).encode("utf-8")

    request = urllib.request.Request(
        GRAPHQL_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "github-profile-contribution-calendar",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"GitHub GraphQL request failed with HTTP {exc.code}: {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub GraphQL request failed: {exc}") from exc

    if body.get("errors"):
        raise RuntimeError(
            "GitHub GraphQL returned errors: " + json.dumps(body["errors"])
        )

    user = body.get("data", {}).get("user")
    if not user:
        raise RuntimeError(f"GitHub user {username!r} was not found.")

    return user["contributionsCollection"]["contributionCalendar"]


def month_labels(weeks: list[dict]) -> list[tuple[int, str]]:
    labels: list[tuple[int, str]] = []
    seen: set[tuple[int, int]] = set()

    for index, week in enumerate(weeks):
        for day in week["contributionDays"]:
            date = dt.date.fromisoformat(day["date"])
            key = (date.year, date.month)

            if date.day <= 7 and key not in seen:
                labels.append((index, date.strftime("%b")))
                seen.add(key)
                break

    return labels


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_svg(calendar: dict, username: str, theme: str) -> str:
    p = PALETTES[theme]
    weeks = calendar["weeks"]
    total = int(calendar["totalContributions"])

    width = 900
    height = 215

    grid_x = 67
    grid_y = 72
    cell = 11
    gap = 3
    step = cell + gap

    grid_width = max(1, len(weeks)) * step - gap
    grid_height = 7 * step - gap

    title = f"{total:,} contributions in the last year"

    cells: list[str] = []
    mask_cells: list[str] = []
    active_halos: list[str] = []

    week_count = max(1, len(weeks))

    for week_index, week in enumerate(weeks):
        for day in week["contributionDays"]:
            weekday = int(day["weekday"])

            x = grid_x + week_index * step
            y = grid_y + weekday * step

            level = day.get("contributionLevel", "NONE")
            count = int(day.get("contributionCount", 0))
            date = day.get("date", "")

            fill = p.get(level, p["NONE"])
            stroke = p["border"] if level == "NONE" else fill
            plural = "" if count == 1 else "s"

            cells.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1">'
                f'<title>{esc(date)}: {count} contribution{plural}</title>'
                f'</rect>'
            )

            mask_cells.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                f'fill="none" stroke="white" stroke-width="2"/>'
            )

            if count > 0:
                phase = 1.0 + (week_index / week_count) * 8.0 + weekday * 0.015
                active_halos.append(
                    f'<rect class="cell-halo" x="{x - 1}" y="{y - 1}" '
                    f'width="{cell + 2}" height="{cell + 2}" rx="3" '
                    f'fill="none" stroke="{p["accent_strong"]}" stroke-width="1.4" '
                    f'opacity="0">'
                    f'<animate attributeName="opacity" '
                    f'values="0;0;0.55;0" keyTimes="0;0.45;0.52;1" '
                    f'dur="9s" begin="{phase:.3f}s" repeatCount="indefinite"/>'
                    f'<animate attributeName="stroke-width" '
                    f'values="1;1;2.4;1" keyTimes="0;0.45;0.52;1" '
                    f'dur="9s" begin="{phase:.3f}s" repeatCount="indefinite"/>'
                    f'</rect>'
                )

    months = []
    for week_index, label in month_labels(weeks):
        x = grid_x + week_index * step
        months.append(
            f'<text x="{x}" y="56" class="secondary month">{esc(label)}</text>'
        )

    weekdays = []
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        weekdays.append(
            f'<text x="20" y="{grid_y + row * step + 9}" '
            f'class="secondary weekday">{label}</text>'
        )

    legend_x = width - 205
    legend_y = 192

    legend_levels = [
        p["NONE"],
        p["FIRST_QUARTILE"],
        p["SECOND_QUARTILE"],
        p["THIRD_QUARTILE"],
        p["FOURTH_QUARTILE"],
    ]

    legend_cells = []
    for i, color in enumerate(legend_levels):
        x = legend_x + 36 + i * 15
        stroke = p["border"] if i == 0 else color

        legend_cells.append(
            f'<rect x="{x}" y="{legend_y - 9}" width="10" height="10" rx="2" '
            f'fill="{color}" stroke="{stroke}" stroke-width="1"/>'
        )

    scan_start = grid_x - 190
    scan_end = grid_x + grid_width + 190

    # Three subtle particles travel with the scan. They are decorative and
    # intentionally kept away from the contribution-value encoding.
    particle_ys = (
        grid_y - 5,
        grid_y + grid_height // 2,
        grid_y + grid_height + 5,
    )

    particles = []
    for i, y in enumerate(particle_ys):
        begin = 1.0 + i * 0.32
        opacity = 0.65 - i * 0.12
        radius = 2.1 - i * 0.3
        particles.append(
            f'<circle class="particle" cx="{scan_start}" cy="{y}" r="{radius}" '
            f'fill="{p["accent_blue"]}" opacity="{opacity}">'
            f'<animate attributeName="cx" values="{scan_start};{scan_end}" '
            f'dur="9s" begin="{begin:.2f}s" repeatCount="indefinite" '
            f'calcMode="spline" keyTimes="0;1" keySplines="0.22 1 0.36 1"/>'
            f'<animate attributeName="opacity" values="0;{opacity};0" '
            f'dur="9s" begin="{begin:.2f}s" repeatCount="indefinite"/>'
            f'</circle>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg"
    width="{width}" height="{height}" viewBox="0 0 {width} {height}"
    role="img" aria-labelledby="title desc">

  <title id="title">GitHub contribution pulse for {esc(username)}</title>
  <desc id="desc">
    {esc(title)}. Cell colors encode real GitHub contribution levels.
    Decorative violet and blue effects animate around the grid without changing the data.
  </desc>

  <defs>
    <linearGradient id="scanGradient" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{p["accent"]}" stop-opacity="0"/>
      <stop offset="30%" stop-color="{p["accent"]}" stop-opacity="0.04"/>
      <stop offset="44%" stop-color="{p["accent"]}" stop-opacity="0.22"/>
      <stop offset="50%" stop-color="{p["accent_strong"]}" stop-opacity="1"/>
      <stop offset="56%" stop-color="{p["accent_blue"]}" stop-opacity="0.35"/>
      <stop offset="70%" stop-color="{p["accent"]}" stop-opacity="0.04"/>
      <stop offset="100%" stop-color="{p["accent"]}" stop-opacity="0"/>
    </linearGradient>

    <linearGradient id="coreGradient" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{p["accent_blue"]}" stop-opacity="0"/>
      <stop offset="48%" stop-color="{p["accent_blue"]}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{p["accent_blue"]}" stop-opacity="0.95"/>
      <stop offset="52%" stop-color="{p["accent_blue"]}" stop-opacity="0"/>
      <stop offset="100%" stop-color="{p["accent_blue"]}" stop-opacity="0"/>
    </linearGradient>

    <linearGradient id="borderGradient" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{p["border"]}"/>
      <stop offset="35%" stop-color="{p["accent"]}"/>
      <stop offset="52%" stop-color="{p["accent_blue"]}"/>
      <stop offset="70%" stop-color="{p["accent"]}"/>
      <stop offset="100%" stop-color="{p["border"]}"/>
    </linearGradient>

    <filter id="softGlow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="2.7" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <filter id="particleGlow" x="-120%" y="-120%" width="340%" height="340%">
      <feGaussianBlur stdDeviation="3.0" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <mask id="cellBorders">
      <rect width="100%" height="100%" fill="black"/>
      {"".join(mask_cells)}
    </mask>
  </defs>

  <style>
    text {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      fill: {p["text"]};
    }}

    .title {{
      font-size: 16px;
      font-weight: 600;
    }}

    .secondary {{
      fill: {p["secondary"]};
      font-size: 12px;
    }}

    .month {{
      font-weight: 500;
    }}

    .weekday {{
      font-size: 11px;
    }}

    #aurora-scan {{
      opacity: 0.82;
    }}

    #core-scan {{
      opacity: 0.60;
    }}

    .particle {{
      filter: url(#particleGlow);
    }}

    @media (prefers-reduced-motion: reduce) {{
      #aurora-scan,
      #core-scan,
      #animated-frame,
      #cell-halos,
      #particles {{
        display: none;
      }}
    }}
  </style>

  <rect
    width="{width}"
    height="{height}"
    rx="9"
    fill="{p["background"]}"
    stroke="{p["border"]}"
  />

  <rect
    id="animated-frame"
    x="1.5"
    y="1.5"
    width="{width - 3}"
    height="{height - 3}"
    rx="8"
    fill="none"
    stroke="url(#borderGradient)"
    stroke-width="1.4"
    stroke-linecap="round"
    stroke-dasharray="90 810"
    opacity="0.48"
  >
    <animate
      attributeName="stroke-dashoffset"
      values="900;0"
      dur="14s"
      repeatCount="indefinite"
    />
    <animate
      attributeName="opacity"
      values="0.28;0.58;0.28"
      dur="6s"
      repeatCount="indefinite"
    />
  </rect>

  <text x="20" y="30" class="title">{esc(title)}</text>

  <rect
    x="20"
    y="39"
    width="260"
    height="1.5"
    rx="1"
    fill="{p["accent"]}"
    opacity="0.12"
  >
    <animate
      attributeName="width"
      values="70;260;70"
      dur="8s"
      repeatCount="indefinite"
    />
    <animate
      attributeName="opacity"
      values="0.08;0.32;0.08"
      dur="8s"
      repeatCount="indefinite"
    />
  </rect>

  {"".join(months)}
  {"".join(weekdays)}
  {"".join(cells)}

  <g id="cell-halos" filter="url(#softGlow)">
    {"".join(active_halos)}
  </g>

  <g id="aurora-scan" mask="url(#cellBorders)" filter="url(#softGlow)">
    <rect
      x="{scan_start}"
      y="{grid_y - 7}"
      width="195"
      height="{grid_height + 14}"
      fill="url(#scanGradient)"
    >
      <animate
        attributeName="x"
        values="{scan_start};{scan_end}"
        dur="9s"
        begin="1s"
        repeatCount="indefinite"
        calcMode="spline"
        keyTimes="0;1"
        keySplines="0.22 1 0.36 1"
      />
    </rect>
  </g>

  <g id="core-scan" mask="url(#cellBorders)">
    <rect
      x="{scan_start - 20}"
      y="{grid_y - 5}"
      width="120"
      height="{grid_height + 10}"
      fill="url(#coreGradient)"
    >
      <animate
        attributeName="x"
        values="{scan_start - 20};{scan_end - 20}"
        dur="9s"
        begin="1.18s"
        repeatCount="indefinite"
        calcMode="spline"
        keyTimes="0;1"
        keySplines="0.22 1 0.36 1"
      />
    </rect>
  </g>

  <g id="particles">
    {"".join(particles)}
  </g>

  <text x="20" y="{legend_y}" class="secondary">Contribution pulse</text>

  <text x="{legend_x}" y="{legend_y}" class="secondary">Less</text>
  {"".join(legend_cells)}
  <text x="{legend_x + 118}" y="{legend_y}" class="secondary">More</text>
</svg>
"""


def main() -> int:
    username = (
        os.environ.get("PROFILE_USERNAME")
        or os.environ.get("GITHUB_REPOSITORY_OWNER")
    )
    token = os.environ.get("GITHUB_TOKEN")

    if not username:
        print(
            "PROFILE_USERNAME or GITHUB_REPOSITORY_OWNER is required.",
            file=sys.stderr,
        )
        return 2

    if not token:
        print("GITHUB_TOKEN is required.", file=sys.stderr)
        return 2

    calendar = fetch_calendar(username, token)

    output_dir = Path("profile")
    output_dir.mkdir(parents=True, exist_ok=True)

    for theme in ("dark", "light"):
        output = output_dir / f"contributions-{theme}.svg"
        output.write_text(
            render_svg(calendar, username, theme),
            encoding="utf-8",
        )
        print(f"Wrote {output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
