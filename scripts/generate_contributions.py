#!/usr/bin/env python3
"""Generate static, accessible GitHub activity summaries and SVG visualizations."""

from __future__ import annotations

import datetime as dt
import email.utils
import html
import json
import os
import re
import shutil
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
import sys
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
GRAPHQL_URL = "https://api.github.com/graphql"
MAX_ATTEMPTS = 3
MAX_RETRY_DELAY_SECONDS = 8.0
MAX_RESPONSE_BYTES = 2_000_000
OUTPUT_NAMES = (
    "contributions-dark.svg", "contributions-light.svg",
    "contributions-mobile-dark.svg", "contributions-mobile-light.svg",
    "contributions-summary.md",
)
ALLOWED_LEVELS = frozenset(("NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"))


class CalendarError(ValueError):
    """Invalid, incomplete, or inconsistent contribution snapshot."""


def _object(value: object, name: str) -> dict:
    if not isinstance(value, dict):
        raise CalendarError(f"{name} must be an object")
    return value


def _exact_integer(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise CalendarError(f"{name} must be a nonnegative integer (not boolean)")
    return value


def _date(value: object, name: str) -> dt.date:
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        raise CalendarError(f"{name} must be an ISO YYYY-MM-DD date")
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise CalendarError(f"{name} has an invalid calendar date: {value!r}") from exc


def _weekday(date: dt.date) -> int:
    """GitHub uses Sunday=0 through Saturday=6."""
    return (date.weekday() + 1) % 7


def validate_calendar(value: object) -> dict:
    """Validate a complete, uninterrupted GitHub date span and copy its safe fields.

    Zero-contribution periods are valid only with explicit zero-count day cells;
    omitted weeks or days are missing data, not evidence of zero activity.
    Partial starting and ending weeks are allowed, never internal gaps.
    """
    cal = _object(value, "calendar")
    if set(cal) != {"totalContributions", "weeks"}:
        raise CalendarError("calendar requires only totalContributions and weeks")
    total = _exact_integer(cal["totalContributions"], "calendar.totalContributions")
    weeks = cal["weeks"]
    if not isinstance(weeks, list) or not (1 <= len(weeks) <= 54):
        raise CalendarError("calendar.weeks must contain 1–54 nonempty calendar weeks")
    normalized = []
    previous_start = None
    previous_date = None
    accumulated = 0
    for wi, candidate in enumerate(weeks):
        week = _object(candidate, f"weeks[{wi}]")
        if set(week) != {"firstDay", "contributionDays"}:
            raise CalendarError(f"weeks[{wi}] requires firstDay and contributionDays")
        first = _date(week["firstDay"], f"weeks[{wi}].firstDay")
        if _weekday(first) != 0:
            raise CalendarError(f"weeks[{wi}].firstDay must be a Sunday")
        if previous_start is not None and first != previous_start + dt.timedelta(days=7):
            raise CalendarError(f"weeks[{wi}].firstDay is not seven days after previous week")
        days = week["contributionDays"]
        if not isinstance(days, list) or not (1 <= len(days) <= 7):
            raise CalendarError(f"weeks[{wi}].contributionDays must contain 1–7 dated cells")
        output_days = []
        for di, candidate_day in enumerate(days):
            path = f"weeks[{wi}].contributionDays[{di}]"
            day = _object(candidate_day, path)
            required = {"date", "weekday", "contributionCount", "contributionLevel"}
            if set(day) != required:
                raise CalendarError(f"{path} requires date, weekday, contributionCount and contributionLevel")
            day_date = _date(day["date"], f"{path}.date")
            expected = (day_date - first).days
            if not (0 <= expected <= 6):
                raise CalendarError(f"{path}.date is outside the declared week")
            weekday = day["weekday"]
            if type(weekday) is not int or not (0 <= weekday <= 6):
                raise CalendarError(f"{path}.weekday must be an integer from 0 to 6")
            if weekday != expected or weekday != _weekday(day_date):
                raise CalendarError(f"{path}.weekday disagrees with its date and firstDay")
            if previous_date is not None and day_date != previous_date + dt.timedelta(days=1):
                raise CalendarError(f"{path}.date must follow the preceding calendar date without gaps or duplicates")
            count = _exact_integer(day["contributionCount"], f"{path}.contributionCount")
            level = day["contributionLevel"]
            if not isinstance(level, str) or level not in ALLOWED_LEVELS:
                raise CalendarError(f"{path}.contributionLevel is not a recognized GitHub level")
            # The quartiles are relative to GitHub's own classification; zero must be NONE.
            if (count == 0) != (level == "NONE"):
                raise CalendarError(f"{path} has inconsistent count and contribution level")
            accumulated += count
            output_days.append({"date": day["date"], "weekday": weekday,
                                "contributionCount": count, "contributionLevel": level})
            previous_date = day_date
        if wi > 0 and output_days[0]["weekday"] != 0:
            raise CalendarError(f"weeks[{wi}] has missing Sunday/start-of-week cells")
        if wi < len(weeks) - 1 and output_days[-1]["weekday"] != 6:
            raise CalendarError(f"weeks[{wi}] has missing end-of-week cells")
        normalized.append({"firstDay": week["firstDay"], "contributionDays": output_days})
        previous_start = first
    if accumulated != total:
        raise CalendarError(f"calendar.totalContributions {total} disagrees with daily sum {accumulated}")
    return {"totalContributions": total, "weeks": normalized}


def validate_api_response(response: object, username: str) -> dict:
    obj = _object(response, "GitHub GraphQL response")
    errors = obj.get("errors")
    if errors:
        if not isinstance(errors, list):
            raise CalendarError("GitHub GraphQL errors must be an array")
        messages = [str(e.get("message", "unknown error"))[:200] if isinstance(e, dict) else "unknown error" for e in errors[:3]]
        raise CalendarError("GitHub GraphQL returned errors: " + "; ".join(messages))
    if "errors" in obj and not isinstance(errors, list) and errors is not None:
        raise CalendarError("GitHub GraphQL errors field has invalid type")
    data = _object(obj.get("data"), "response.data")
    user = data.get("user")
    if user is None:
        raise CalendarError(f"GitHub user {username!r} was not found")
    collection = _object(_object(user, "response.data.user").get("contributionsCollection"), "response.data.user.contributionsCollection")
    return validate_calendar(collection.get("contributionCalendar"))


def _retry_delay(headers: object, attempt: int, *, now: dt.datetime | None = None) -> float:
    fallback = min(float(2 ** attempt), MAX_RETRY_DELAY_SECONDS)
    retry_after = headers.get("Retry-After") if headers is not None else None
    if retry_after is None:
        return fallback
    try:
        seconds = float(retry_after)
        if seconds >= 0 and seconds != float("inf"):
            return min(seconds, MAX_RETRY_DELAY_SECONDS)
    except (TypeError, ValueError):
        pass
    try:
        specified = email.utils.parsedate_to_datetime(str(retry_after))
        if specified.tzinfo is not None:
            current = now or dt.datetime.now(dt.timezone.utc)
            return min(max((specified - current).total_seconds(), 0), MAX_RETRY_DELAY_SECONDS)
    except (TypeError, ValueError, OverflowError):
        pass
    return fallback


def _retryable_http(error: urllib.error.HTTPError) -> bool:
    if error.code in {408, 425, 429, 500, 502, 503, 504}:
        return True
    headers = error.headers
    return error.code == 403 and headers is not None and (
        headers.get("Retry-After") is not None or headers.get("X-RateLimit-Remaining") == "0"
    )


def fetch_calendar(username: str, token: str, *, opener=None, sleeper=None, max_attempts: int = MAX_ATTEMPTS) -> dict:
    """Fetch and verify a complete snapshot with bounded transient retries."""
    if not username or not token:
        raise CalendarError("A nonempty GitHub username and API token are required")
    if type(max_attempts) is not int or not 1 <= max_attempts <= 5:
        raise ValueError("max_attempts must be from 1 to 5")
    opener = opener or urllib.request.urlopen
    sleeper = sleeper or time.sleep
    payload = json.dumps({"query": QUERY, "variables": {"login": username}}).encode("utf-8")
    request = urllib.request.Request(
        GRAPHQL_URL, data=payload, method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "github-profile-contribution-calendar"},
    )
    for attempt in range(max_attempts):
        try:
            with opener(request, timeout=30) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise CalendarError("GitHub response exceeds the allowed 2 MB size")
            try:
                response_data = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                raise CalendarError("GitHub returned malformed UTF-8 JSON") from exc
            return validate_api_response(response_data, username)
        except urllib.error.HTTPError as exc:
            retry = _retryable_http(exc)
            if retry and attempt + 1 < max_attempts:
                sleeper(_retry_delay(exc.headers, attempt))
                continue
            raise CalendarError(f"GitHub GraphQL HTTP {exc.code} after {attempt+1} attempt(s); {'retry limit reached' if retry else 'not retryable'}") from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            if attempt + 1 < max_attempts:
                sleeper(min(float(2 ** attempt), MAX_RETRY_DELAY_SECONDS))
                continue
            raise CalendarError(f"GitHub GraphQL connection failed after {max_attempts} attempts: {type(exc).__name__}") from exc
    raise AssertionError("unreachable retry state")


def snapshot_stamp(value: dt.datetime | None) -> str:
    """Include a timezone-aware capture timestamp, or disclose missing provenance."""
    if value is None:
        return "unknown (archived snapshot; API retrieval time was not recorded)"
    if not isinstance(value, dt.datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise CalendarError("snapshot timestamp must be a timezone-aware datetime")
    return value.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def month_labels(weeks: list[dict]) -> list[tuple[int, str]]:
    """Find first visible dates of months and space their SVG labels legibly.

    A partial first month can share a week with the next month. Never overlay
    their text at the same x coordinate. Exact dates remain in the text table.
    """
    changes: list[tuple[int, str]] = []
    previous_month: tuple[int, int] | None = None
    for index, week in enumerate(weeks):
        for day in week["contributionDays"]:
            date = dt.date.fromisoformat(day["date"])
            month = (date.year, date.month)
            if month != previous_month:
                changes.append((index, date.strftime("%b")))
                previous_month = month
    labels: list[tuple[int, str]] = []
    for index, name in changes:
        # Three 14px columns leave room for a three-letter month label at 12px.
        visual_index = max(index, labels[-1][0] + 3) if labels else index
        if visual_index < len(weeks):
            labels.append((visual_index, name))
    return labels

def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def activity_days(calendar: dict) -> list[dict]:
    return sorted(
        (day for week in calendar["weeks"] for day in week["contributionDays"]),
        key=lambda day: day["date"],
    )


def monthly_activity(calendar: dict) -> list[tuple[str, int, str, str]]:
    """Month, count, actual first date, actual last date (partial months supported)."""
    totals: dict[str, int] = {}
    firsts: dict[str, str] = {}
    lasts: dict[str, str] = {}
    for day in activity_days(calendar):
        date = day["date"]
        key = date[:7]
        totals[key] = totals.get(key, 0) + int(day["contributionCount"])
        firsts.setdefault(key, date)
        lasts[key] = date
    return [(key, totals[key], firsts[key], lasts[key]) for key in sorted(totals)]


def render_summary(calendar: dict, username: str, *, fetched_at: dt.datetime | None = None) -> str:
    """Accessible numerical equivalent, including the full date sequence."""
    calendar = validate_calendar(calendar)
    days = activity_days(calendar)
    months = monthly_activity(calendar)
    total = int(calendar["totalContributions"])
    period = f"{days[0]['date']} through {days[-1]['date']}" if days else "no dated cells"
    lines = [
        "# GitHub contribution activity — accessible snapshot",
        "",
        f"**Account:** [{username}](https://github.com/{username}?tab=overview)  ",
        f"**Reporting dates:** {period}  ",
        f"**Reported contribution total:** {total:,}  ",
        f"**Snapshot retrieved (UTC):** {snapshot_stamp(fetched_at)}  ",
        "**Status:** A generated public GitHub snapshot, not a real-time feed.",
        "",
        "Counts reflect GitHub's public contribution-calendar API; activity does not measure engineering quality.",
        "Partial first and last months are explicitly identified by their covered dates.",
        "For current data and full context, open the linked GitHub contributions view.",
        "",
        "## Monthly totals",
        "",
        "| Month | Contributions | Dates represented |",
        "| --- | ---: | --- |",
    ]
    lines += [f"| {month} | {count} | {start} to {end} |" for month, count, start, end in months]
    lines += ["", "## Daily counts", "", "| Date | Contributions |", "| --- | ---: |"]
    lines += [f"| {day['date']} | {int(day['contributionCount'])} |" for day in days]
    return "\n".join(lines) + "\n"


def render_svg(calendar: dict, username: str, theme: str, *, fetched_at: dt.datetime | None = None) -> str:
    """Desktop: static full-year daily chart; no animated elements or CSS."""
    calendar = validate_calendar(calendar)
    p = PALETTES[theme]
    weeks = calendar["weeks"]
    days = activity_days(calendar)
    total = int(calendar["totalContributions"])
    width, height = 900, 224
    grid_x, grid_y, cell, step = 67, 74, 11, 14
    month_text = "".join(
        f'<text x="{grid_x + idx*step}" y="58" class="muted">{esc(label)}</text>'
        for idx, label in month_labels(weeks)
    )
    cells = []
    for week_index, week in enumerate(weeks):
        for day in week["contributionDays"]:
            x = grid_x + week_index * step
            y = grid_y + int(day["weekday"]) * step
            level = day["contributionLevel"]
            color = p[level]
            count = int(day["contributionCount"])
            date = day["date"]
            cells.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                f'fill="{color}" stroke="{p["border"]}" stroke-width="0.6">'
                f'<title>{esc(date)}: {count} contributions</title></rect>'
            )
    labels = "".join(
        f'<text x="17" y="{grid_y + row*step + 9}" class="muted">{day}</text>'
        for row, day in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )
    legend = "".join(
        f'<rect x="{690 + i*18}" y="192" width="13" height="13" rx="2" '
        f'fill="{p[level]}" stroke="{p["border"]}" stroke-width="1"/>'
        for i, level in enumerate(("NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"))
    )
    period = f"{days[0]['date']} to {days[-1]['date']}" if days else "No dated cells"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="224" viewBox="0 0 900 224"
    role="img" aria-labelledby="title desc">
  <title id="title">GitHub contribution activity for {esc(username)}</title>
  <desc id="desc">Static calendar: {esc(total)} contributions during {esc(period)}. The
    README links to an accessible Markdown summary containing numeric monthly and daily counts.
    Snapshot retrieved (UTC): {esc(snapshot_stamp(fetched_at))}.</desc>
  <style>
    text {{font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;fill:{p["text"]}}}
    .muted {{fill:{p["secondary"]};font-size:12px}}
  </style>
  <rect width="899" height="223" x="0.5" y="0.5" rx="12" fill="{p["background"]}" stroke="{p["border"]}"/>
  <text x="20" y="29" font-size="17" font-weight="700">{total:,} contributions · public GitHub snapshot</text>
  {month_text}{labels}{''.join(cells)}
  <text x="20" y="199" class="muted">{esc(period)}</text>
  <text x="646" y="201" class="muted">Less</text>{legend}<text x="790" y="201" class="muted">More</text>
</svg>"""


def render_mobile_svg(calendar: dict, username: str, theme: str, *, fetched_at: dt.datetime | None = None) -> str:
    """Mobile: numeric recent-month totals at readable 320px viewport scales."""
    calendar = validate_calendar(calendar)
    p = PALETTES[theme]
    months = monthly_activity(calendar)[-6:]
    total = int(calendar["totalContributions"])
    dates = activity_days(calendar)
    recent = []
    for i, (month, count, first, last) in enumerate(months):
        col, row = i % 2, i // 2
        x, y = 14 + col*174, 95 + row*65
        label = dt.date.fromisoformat(month + "-01").strftime("%b %Y")
        recent.append(
            f'<rect x="{x}" y="{y}" width="160" height="55" rx="9" '
            f'fill="{p["background"]}" stroke="{p["border"]}"/>'
            f'<text x="{x+12}" y="{y+22}" font-size="14" fill="{p["secondary"]}">{esc(label)}</text>'
            f'<text x="{x+12}" y="{y+46}" font-size="23" font-weight="700" fill="{p["text"]}">{count}</text>'
        )
    period = f"{dates[0]['date']} to {dates[-1]['date']}" if dates else "No dates"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="362" height="323" viewBox="0 0 362 323"
    role="img" aria-labelledby="title desc">
  <title id="title">Recent GitHub activity for {esc(username)}</title>
  <desc id="desc">Static six-month numerical summary. {total} contributions in the reporting period {esc(period)}.
    The accompanying Markdown summary provides all monthly and daily counts.
    Snapshot retrieved (UTC): {esc(snapshot_stamp(fetched_at))}.</desc>
  <rect x="0.5" y="0.5" width="361" height="322" rx="12" stroke="{p["border"]}" fill="{p["background"]}"/>
  <text x="14" y="31" font-size="21" font-weight="700" fill="{p["text"]}" font-family="Arial,sans-serif">{total} contributions</text>
  <text x="14" y="53" font-size="13" fill="{p["secondary"]}" font-family="Arial,sans-serif">Reporting period: {esc(period)}</text>
  <text x="14" y="76" font-size="13" fill="{p["secondary"]}" font-family="Arial,sans-serif">Latest six months · monthly counts</text>
  <g font-family="Arial,sans-serif">{''.join(recent)}</g>
  <text x="14" y="309" font-size="12" fill="{p["secondary"]}" font-family="Arial,sans-serif">Exact dated counts: see linked text summary</text>
</svg>"""



def render_outputs(calendar: dict, username: str, *, fetched_at: dt.datetime | None) -> dict[str, str]:
    """Prepare the complete immutable candidate asset set in memory."""
    calendar = validate_calendar(calendar)
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", username):
        raise CalendarError("PROFILE_USERNAME must be a valid GitHub login")
    outputs = {}
    for theme in ("dark", "light"):
        outputs[f"contributions-{theme}.svg"] = render_svg(calendar, username, theme, fetched_at=fetched_at)
        outputs[f"contributions-mobile-{theme}.svg"] = render_mobile_svg(calendar, username, theme, fetched_at=fetched_at)
    outputs["contributions-summary.md"] = render_summary(calendar, username, fetched_at=fetched_at)
    return outputs


def verify_outputs(outputs: dict[str, str], calendar: dict, fetched_at: dt.datetime | None) -> None:
    """Ensure every candidate exists and shares period, total, and retrieval metadata."""
    if set(outputs) != set(OUTPUT_NAMES):
        raise CalendarError("generated asset set must contain exactly the five owned outputs")
    calendar = validate_calendar(calendar)
    stamp = snapshot_stamp(fetched_at)
    total = calendar["totalContributions"]
    days = activity_days(calendar)
    summary = outputs["contributions-summary.md"]
    if f"**Reported contribution total:** {total:,}" not in summary or stamp not in summary:
        raise CalendarError("accessible summary total or snapshot provenance is inconsistent")
    actual = re.findall(r"^\| (\d{4}-\d{2}-\d{2}) \| (\d+) \|$", summary, flags=re.M)
    expected = [(day["date"], str(day["contributionCount"])) for day in days]
    if actual != expected:
        raise CalendarError("accessible summary daily counts disagree with validated API snapshot")
    for filename in OUTPUT_NAMES:
        if not filename.endswith(".svg"):
            continue
        raw = outputs[filename]
        if any(marker in raw.lower() for marker in ("<animate", "@keyframes", "animation:")):
            raise CalendarError(f"{filename} contains unexpected motion")
        try:
            svg = ET.fromstring(raw)
        except ET.ParseError as exc:
            raise CalendarError(f"generated {filename} has invalid SVG XML") from exc
        ns = "{http://www.w3.org/2000/svg}"
        if svg.tag != ns + "svg" or svg.get("role") != "img":
            raise CalendarError(f"generated {filename} lacks SVG image semantics")
        title, desc = svg.find(ns + "title"), svg.find(ns + "desc")
        if title is None or desc is None:
            raise CalendarError(f"generated {filename} lacks accessible title or description")
        desc_text = "".join(desc.itertext())
        if str(total) not in desc_text or stamp not in desc_text:
            raise CalendarError(f"generated {filename} has inconsistent total or retrieval provenance")
    if summary.splitlines().count("| --- | ---: |") != 1:
        raise CalendarError("accessible summary daily table structure is unexpected")


def publish_assets(root: Path, calendar: dict, username: str, *, fetched_at: dt.datetime | None) -> None:
    """Validate all outputs before replacing any; restore the old directory on error.

    The publishing workflow commits all five verified files in one Git commit.
    Local directory replacement restores its backup on ordinary exceptions.
    The separate backup directory survives abrupt termination during the swap;
    the Git workflow publishes the complete file set in a single Git commit.
    This is not an OS-level atomic multi-file swap for simultaneous readers.
    """
    root = Path(root).resolve()
    output_dir = root / "profile"
    if output_dir.is_symlink() or (output_dir.exists() and not output_dir.is_dir()):
        raise CalendarError("profile output path must be a regular directory")
    outputs = render_outputs(calendar, username, fetched_at=fetched_at)
    verify_outputs(outputs, calendar, fetched_at)
    with tempfile.TemporaryDirectory(prefix=".profile-candidate-", dir=root) as temp:
        tmp_root = Path(temp)
        staged = tmp_root / "candidate"
        if output_dir.is_dir():
            shutil.copytree(output_dir, staged, symlinks=True)
        else:
            staged.mkdir()
        for filename, text in outputs.items():
            if (staged / filename).is_symlink():
                raise CalendarError(f"refusing to overwrite symbolic-link output {filename}")
            (staged / filename).write_text(text, encoding="utf-8")
        # Verify physical candidate bytes, including after staging and serialization.
        verify_outputs({name: (staged / name).read_text(encoding="utf-8") for name in OUTPUT_NAMES}, calendar, fetched_at)
        # Backup lives outside the temporary staging directory, so abrupt
        # termination does not silently discard the previous published set.
        backup = root / (".profile-previous-" + tmp_root.name)
        had_previous = output_dir.exists()
        if had_previous:
            os.replace(output_dir, backup)
        try:
            os.replace(staged, output_dir)
        except BaseException:
            if had_previous:
                try:
                    os.replace(backup, output_dir)
                except OSError as recovery_error:
                    raise CalendarError(
                        f"publication failed and automatic restoration failed; "
                        f"last known-good files remain at {backup}"
                    ) from recovery_error
            raise
        else:
            if had_previous:
                shutil.rmtree(backup)
    for filename in OUTPUT_NAMES:
        print(f"Verified and published {output_dir / filename}")


def main() -> int:
    username = os.environ.get("PROFILE_USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER")
    token = os.environ.get("GITHUB_TOKEN")
    if not username or not token:
        print("PROFILE_USERNAME (or GITHUB_REPOSITORY_OWNER) and GITHUB_TOKEN are required.", file=sys.stderr)
        return 2
    try:
        calendar = fetch_calendar(username, token)
        # Capture time immediately after the successful validated API response.
        retrieved_at = dt.datetime.now(dt.timezone.utc)
        publish_assets(ROOT, calendar, username, fetched_at=retrieved_at)
    except (CalendarError, OSError, ET.ParseError) as exc:
        print(f"Contribution refresh failed without publishing: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
