#!/usr/bin/env python3
"""Generate GitHub-native-style animated contribution-calendar SVGs."""

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
    total = calendar["totalContributions"]

    width = 900
    height = 205

    grid_x = 67
    grid_y = 68

    cell = 11
    gap = 3
    step = cell + gap

    grid_width = max(1, len(weeks)) * step - gap
    grid_height = 7 * step - gap

    title = f"{total:,} contributions in the last year"

    cells: list[str] = []
    mask_cells: list[str] = []

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

    months = []

    for week_index, label in month_labels(weeks):
        x = grid_x + week_index * step

        months.append(
            f'<text x="{x}" y="54" class="secondary month">'
            f'{esc(label)}'
            f'</text>'
        )

    weekdays = []

    for row, label in (
        (1, "Mon"),
        (3, "Wed"),
        (5, "Fri"),
    ):
        weekdays.append(
            f'<text x="20" y="{grid_y + row * step + 9}" '
            f'class="secondary weekday">{label}</text>'
        )

    legend_x = width - 205
    legend_y = 181

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
            f'<rect x="{x}" y="{legend_y - 9}" '
            f'width="10" height="10" rx="2" '
            f'fill="{color}" stroke="{stroke}" stroke-width="1"/>'
        )

    scan_start = grid_x - 180
    scan_end = grid_x + grid_width + 180

    return f"""<svg xmlns="http://www.w3.org/2000/svg"
    width="{width}"
    height="{height}"
    viewBox="0 0 {width} {height}"
    role="img"
    aria-labelledby="title desc">

  <title id="title">
    GitHub contribution calendar for {esc(username)}
  </title>

  <desc id="desc">
    {esc(title)}.
    Cell colors encode real GitHub contribution levels.
    A decorative violet scan animates only cell borders.
  </desc>

  <defs>

    <linearGradient
      id="scanGradient"
      x1="0"
      y1="0"
      x2="1"
      y2="0"
    >
      <stop
        offset="0%"
        stop-color="{p["accent"]}"
        stop-opacity="0"
      />

      <stop
        offset="38%"
        stop-color="{p["accent"]}"
        stop-opacity="0.08"
      />

      <stop
        offset="50%"
        stop-color="{p["accent_strong"]}"
        stop-opacity="0.95"
      />

      <stop
        offset="62%"
        stop-color="{p["accent"]}"
        stop-opacity="0.08"
      />

      <stop
        offset="100%"
        stop-color="{p["accent"]}"
        stop-opacity="0"
      />
    </linearGradient>

    <filter
      id="softGlow"
      x="-40%"
      y="-40%"
      width="180%"
      height="180%"
    >
      <feGaussianBlur
        stdDeviation="2.4"
        result="blur"
      />

      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <mask id="cellBorders">

      <rect
        width="100%"
        height="100%"
        fill="black"
      />

      {"".join(mask_cells)}

    </mask>

  </defs>

  <style>

    text {{
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Helvetica,
        Arial,
        sans-serif;

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

    #scan {{
      opacity: 0.72;
    }}

    @media (prefers-reduced-motion: reduce) {{

      #scan {{
        display: none;
      }}

    }}

  </style>

  <rect
    width="{width}"
    height="{height}"
    rx="8"
    fill="{p["background"]}"
    stroke="{p["border"]}"
  />

  <text
    x="20"
    y="29"
    class="title"
  >
    {esc(title)}
  </text>

  {"".join(months)}

  {"".join(weekdays)}

  {"".join(cells)}

  <g
    id="scan"
    mask="url(#cellBorders)"
    filter="url(#softGlow)"
  >

    <rect
      x="{scan_start}"
      y="{grid_y - 6}"
      width="180"
      height="{grid_height + 12}"
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

  <text
    x="20"
    y="181"
    class="secondary"
  >
    GitHub contribution activity
  </text>

  <text
    x="{legend_x}"
    y="{legend_y}"
    class="secondary"
  >
    Less
  </text>

  {"".join(legend_cells)}

  <text
    x="{legend_x + 118}"
    y="{legend_y}"
    class="secondary"
  >
    More
  </text>

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
        print(
            "GITHUB_TOKEN is required.",
            file=sys.stderr,
        )
        return 2

    calendar = fetch_calendar(
        username,
        token,
    )

    output_dir = Path("profile")
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    for theme in (
        "dark",
        "light",
    ):
        output = (
            output_dir
            / f"contributions-{theme}.svg"
        )

        output.write_text(
            render_svg(
                calendar,
                username,
                theme,
            ),
            encoding="utf-8",
        )

        print(f"Wrote {output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
