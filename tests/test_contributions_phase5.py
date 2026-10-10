"""Phase 5: strict snapshot schema, HTTP failure policy, rendering, and publication rollback.

All network responses are injected; CI never requires a GitHub token or network.
"""
from __future__ import annotations

from copy import deepcopy
import datetime as dt
from io import BytesIO
import json
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import generate_contributions as gen

DATE = dt.datetime(2026, 10, 10, 12, 30, tzinfo=dt.timezone.utc)


def snapshot(start="2026-10-04", count=14, active=(1, 5, 10)):
    """Synthetic complete time span; can cross Sundays, months, and year boundaries."""
    first = dt.date.fromisoformat(start)
    weeks = []
    total = 0
    for i in range(count):
        date = first + dt.timedelta(days=i)
        week_start = date - dt.timedelta(days=(date.weekday() + 1) % 7)
        if not weeks or weeks[-1]["firstDay"] != week_start.isoformat():
            weeks.append({"firstDay": week_start.isoformat(), "contributionDays": []})
        value = 2 if i in active else 0
        total += value
        weeks[-1]["contributionDays"].append({
            "date": date.isoformat(), "weekday": (date.weekday() + 1) % 7,
            "contributionCount": value,
            "contributionLevel": "FIRST_QUARTILE" if value else "NONE",
        })
    return {"totalContributions": total, "weeks": weeks}


def response(calendar):
    return {"data": {"user": {"contributionsCollection": {"contributionCalendar": calendar}}}}


class Reply:
    def __init__(self, obj):
        self.content = json.dumps(obj).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, amount=-1):
        return self.content[:amount]


class InputValidationTests(unittest.TestCase):
    def test_valid_partial_edges(self):
        data = snapshot("2025-12-30", 17, active=(0, 1, 16))
        self.assertEqual(gen.validate_calendar(data), data)

    def test_explicit_zero_activity_is_valid(self):
        data = snapshot("2026-10-04", 7, active=())
        self.assertEqual(gen.validate_calendar(data)["totalContributions"], 0)

    def test_missing_or_empty_weeks_not_zero_activity(self):
        for data in ({"totalContributions": 0}, {"totalContributions": 0, "weeks": []},
                     {"totalContributions": 0, "weeks": [{"firstDay": "2026-10-04", "contributionDays": []}]}):
            with self.subTest(data=data), self.assertRaises(gen.CalendarError):
                gen.validate_calendar(data)

    def test_negative_boolean_string_and_fractional_counts_rejected(self):
        for bad in (-1, True, "2", 2.0, None):
            data = snapshot()
            data["weeks"][0]["contributionDays"][1]["contributionCount"] = bad
            with self.subTest(value=bad), self.assertRaisesRegex(gen.CalendarError, "nonnegative integer"):
                gen.validate_calendar(data)

    def test_invalid_total_and_mismatch_rejected(self):
        for total in (None, "6", -1, True, 999):
            data = snapshot()
            data["totalContributions"] = total
            with self.subTest(total=total), self.assertRaises(gen.CalendarError):
                gen.validate_calendar(data)

    def test_bad_day_shape_and_missing_day_fields_rejected(self):
        for bad in ({}, {"date": "2026-10-04"}, [], "bad", None):
            data = snapshot()
            data["weeks"][0]["contributionDays"][0] = bad
            with self.subTest(data=bad), self.assertRaises(gen.CalendarError):
                gen.validate_calendar(data)

    def test_unknown_levels_or_zero_positive_mismatch_rejected(self):
        for level in ("FIFTH_QUARTILE", None, 4, "NONE"):
            data = snapshot()
            data["weeks"][0]["contributionDays"][1]["contributionLevel"] = level
            with self.subTest(level=level), self.assertRaises(gen.CalendarError):
                gen.validate_calendar(data)
        data = snapshot()
        data["weeks"][0]["contributionDays"][0]["contributionLevel"] = "FIRST_QUARTILE"
        with self.assertRaises(gen.CalendarError):
            gen.validate_calendar(data)

    def test_bad_weekday_type_range_and_semantics_rejected(self):
        for weekday in (7, -1, 23, True, "0", 1):
            data = snapshot()
            data["weeks"][0]["contributionDays"][0]["weekday"] = weekday
            with self.subTest(weekday=weekday), self.assertRaises(gen.CalendarError):
                gen.validate_calendar(data)

    def test_duplicate_unordered_or_missing_dates_rejected(self):
        for new_date in ("2026-10-05", "2026-10-03", "2026-10-07"):
            data = snapshot()
            data["weeks"][0]["contributionDays"][2]["date"] = new_date
            with self.subTest(date=new_date), self.assertRaises(gen.CalendarError):
                gen.validate_calendar(data)

    def test_invalid_iso_dates_rejected(self):
        for bad in ("2026-02-29", "2026/10/05", "20261005", 20261005, "2026-13-05"):
            data = snapshot()
            data["weeks"][0]["contributionDays"][1]["date"] = bad
            with self.subTest(date=bad), self.assertRaises(gen.CalendarError):
                gen.validate_calendar(data)

    def test_missing_internal_week_boundary_rejected(self):
        data = snapshot(count=21)
        data["weeks"][1]["contributionDays"].pop(0)
        with self.assertRaises(gen.CalendarError):
            gen.validate_calendar(data)

    def test_invalid_first_day_and_week_gap_rejected(self):
        for start in ("2026-10-05", "2026-10-18", "2026-02-29"):
            data = snapshot()
            data["weeks"][1]["firstDay"] = start
            with self.subTest(firstDay=start), self.assertRaises(gen.CalendarError):
                gen.validate_calendar(data)

    def test_extra_fields_rejected(self):
        data = snapshot()
        data["extra"] = "unexpected"
        with self.assertRaises(gen.CalendarError):
            gen.validate_calendar(data)

    def test_invalid_api_graph(self):
        for body in (None, [], {}, {"data": None}, {"data": {}},
                     {"data": {"user": {}}}, {"data": {"user": None}},
                     {"data": {"user": {"contributionsCollection": {"contributionCalendar": []}}}},
                     {"errors": [{"message": "rate limit"}]}):
            with self.subTest(body=body), self.assertRaises(gen.CalendarError):
                gen.validate_api_response(body, "test")

    def test_no_inplace_mutation(self):
        data = snapshot()
        before = deepcopy(data)
        result = gen.validate_calendar(data)
        self.assertEqual(before, data)
        self.assertIsNot(result, data)


class RetryTests(unittest.TestCase):
    def test_transient_503_then_success(self):
        events = []
        def open_request(request, timeout):
            events.append("request")
            if len(events) == 1:
                raise urllib.error.HTTPError(gen.GRAPHQL_URL, 503, "Unavailable", {}, BytesIO(b"unavailable"))
            return Reply(response(snapshot()))
        waits = []
        result = gen.fetch_calendar("test", "notprinted", opener=open_request, sleeper=waits.append)
        self.assertEqual(result["totalContributions"], 6)
        self.assertEqual(events, ["request", "request"])
        self.assertEqual(waits, [1.0])

    def test_http_403_with_retry_after_recovers(self):
        tries = [0]
        def open_request(request, timeout):
            tries[0] += 1
            if tries[0] == 1:
                raise urllib.error.HTTPError(gen.GRAPHQL_URL, 403, "Rate limited", {"Retry-After": "2"}, BytesIO(b""))
            return Reply(response(snapshot()))
        delays=[]
        gen.fetch_calendar("test", "secret", opener=open_request, sleeper=delays.append)
        self.assertEqual(delays, [2.0])

    def test_retry_after_is_bounded(self):
        self.assertEqual(gen._retry_delay({"Retry-After": "999999"},0), 8)
        self.assertEqual(gen._retry_delay({"Retry-After": "bad"}, 1), 2.0)

    def test_permanent_401_does_not_retry_or_echo_body(self):
        attempts = []
        def open_request(request, timeout):
            attempts.append(1)
            raise urllib.error.HTTPError(gen.GRAPHQL_URL, 401, "Unauthorized", {}, BytesIO(b"TOP_SECRET"))
        with self.assertRaises(gen.CalendarError) as ctx:
            gen.fetch_calendar("test", "token", opener=open_request, sleeper=lambda d: None)
        self.assertEqual(len(attempts), 1)
        self.assertNotIn("TOP_SECRET", str(ctx.exception))
        self.assertNotIn("token", str(ctx.exception))

    def test_retry_exhaustion(self):
        attempts = []
        def open_request(request, timeout):
            attempts.append(1)
            raise urllib.error.URLError("offline")
        waits = []
        with self.assertRaisesRegex(gen.CalendarError,"after 3 attempts"):
            gen.fetch_calendar("test", "token", opener=open_request, sleeper=waits.append)
        self.assertEqual(len(attempts), 3)
        self.assertEqual(waits, [1.0, 2.0])

    def test_malformed_json_not_retried(self):
        hits=[]
        def open_request(request, timeout):
            hits.append(1)
            reply = Reply({})
            reply.content = b"{not JSON"
            return reply
        with self.assertRaisesRegex(gen.CalendarError, "malformed"):
            gen.fetch_calendar("test", "token", opener=open_request, sleeper=lambda x: None)
        self.assertEqual(len(hits),1)

    def test_response_size_cap(self):
        def open_request(request, timeout):
            reply = Reply({})
            reply.content = b"x" * (gen.MAX_RESPONSE_BYTES+2)
            return reply
        with self.assertRaisesRegex(gen.CalendarError, "2 MB"):
            gen.fetch_calendar("test", "token", opener=open_request, sleeper=lambda x: None)


class RenderAndPublishTests(unittest.TestCase):
    def test_boundary_month_labels_include_end_of_year(self):
        data = snapshot("2025-12-30", 43, active=())
        self.assertEqual([name for _, name in gen.month_labels(data["weeks"])], ["Dec", "Jan", "Feb"])

    def test_leap_day_valid(self):
        data = snapshot("2024-02-26", 14, active=())
        self.assertEqual(gen.validate_calendar(data),data)

    def test_all_outputs_matching_time_count_and_xml(self):
        data = snapshot("2025-12-28", 42, active=(0, 10, 40))
        outputs=gen.render_outputs(data, "test", fetched_at=DATE)
        self.assertEqual(set(outputs), set(gen.OUTPUT_NAMES))
        gen.verify_outputs(outputs,data,DATE)
        self.assertIn("2026-10-10T12:30:00Z", outputs["contributions-summary.md"])
        self.assertIn("| 2025-12-28 |",outputs["contributions-summary.md"])
        for k,v in outputs.items():
            if k.endswith('.svg'):
                ET.fromstring(v)
                self.assertIn('retrieved (UTC)', v)

    def test_invalid_dataset_never_rendered(self):
        data = snapshot()
        data["totalContributions"] = 100
        for renderer in (gen.render_svg, gen.render_mobile_svg):
            with self.assertRaises(gen.CalendarError):
                renderer(data,"test","dark")
        with self.assertRaises(gen.CalendarError):
            gen.render_summary(data,"test")

    def test_missing_fetched_at_is_identified_not_faked(self):
        data=snapshot()
        result=gen.render_summary(data,"test")
        self.assertIn("unknown (archived snapshot",result)
        with self.assertRaises(gen.CalendarError):
            gen.render_summary(data,"test",fetched_at=dt.datetime(2026,10,10))

    def test_complete_publication_and_nonowned_file_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"profile").mkdir()
            (root/"profile"/"handwritten.txt").write_text("preserve")
            gen.publish_assets(root,snapshot(),"test",fetched_at=DATE)
            self.assertEqual((root/"profile/handwritten.txt").read_text(),"preserve")
            published={name:(root/"profile"/name).read_text() for name in gen.OUTPUT_NAMES}
            gen.verify_outputs(published,snapshot(),DATE)
            self.assertEqual(list(root.glob('.profile-candidate-*')),[])

    def test_render_failure_keeps_previous_bytes_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); folder=root/"profile";folder.mkdir()
            for name in gen.OUTPUT_NAMES:
                (folder/name).write_text(f"OLD:{name}")
            old={name:(folder/name).read_bytes() for name in gen.OUTPUT_NAMES}
            data=snapshot();data["totalContributions"]=999
            with self.assertRaises(gen.CalendarError):
                gen.publish_assets(root,data,"test",fetched_at=DATE)
            self.assertEqual(old,{name:(folder/name).read_bytes() for name in gen.OUTPUT_NAMES})

    def test_publication_rollback_when_second_directory_replace_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); folder=root/"profile";folder.mkdir()
            for name in gen.OUTPUT_NAMES:
                (folder/name).write_text(f"OLD:{name}")
            old={name:(folder/name).read_bytes() for name in gen.OUTPUT_NAMES}
            original=gen.os.replace
            calls=[0]
            def replace(a,b):
                calls[0]+=1
                if calls[0]==2:
                    raise OSError("injected replacement failure")
                return original(a,b)
            with patch.object(gen.os,'replace',side_effect=replace):
                with self.assertRaisesRegex(OSError,'injected'):
                    gen.publish_assets(root,snapshot(),"test",fetched_at=DATE)
            self.assertEqual(calls[0],3)
            self.assertEqual(old,{name:(folder/name).read_bytes() for name in gen.OUTPUT_NAMES})
            self.assertEqual(list(root.glob('.profile-candidate-*')),[])

    def test_main_uses_module_repo_root_from_other_working_directory(self):
        with tempfile.TemporaryDirectory() as root_temp, tempfile.TemporaryDirectory() as cwd:
            root=Path(root_temp)
            with patch.object(gen,'ROOT',root), patch.object(gen,'fetch_calendar',return_value=snapshot()), \
                 patch.dict(os.environ,{'PROFILE_USERNAME':'test','GITHUB_TOKEN':'secret'}):
                before=Path.cwd()
                try:
                    os.chdir(cwd)
                    self.assertEqual(gen.main(),0)
                finally:
                    os.chdir(before)
            self.assertTrue((root/'profile/contributions-summary.md').exists())
            self.assertFalse((Path(cwd)/'profile').exists())


if __name__ == '__main__':
    unittest.main()
