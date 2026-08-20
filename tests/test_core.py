import io
import json
import math
import pathlib
import tempfile
import unittest

from proxybench import Event, InputError, compare_summaries, parse_event, summarize, summarize_jsonl, wilson_interval


class CoreTests(unittest.TestCase):
    def test_parse_minimal_event(self):
        event = parse_event({"usable": True}, line_number=1)
        self.assertEqual(event, Event(usable=True))

    def test_unknown_fields_are_rejected(self):
        with self.assertRaises(InputError):
            parse_event({"usable": True, "url": "https://example.invalid"}, line_number=1)

    def test_private_context_fields_are_not_part_of_schema(self):
        for field in ("proxy_ip", "provider", "cookie", "authorization", "target"):
            with self.subTest(field=field):
                with self.assertRaises(InputError):
                    parse_event({"usable": True, field: "redacted"}, line_number=1)

    def test_non_finite_values_are_rejected(self):
        for value in (math.inf, -math.inf, math.nan):
            with self.subTest(value=value):
                with self.assertRaises(InputError):
                    parse_event({"usable": True, "latency_ms": value}, line_number=1)

    def test_negative_cost_is_rejected(self):
        with self.assertRaises(InputError):
            parse_event({"usable": True, "cost_units": -1}, line_number=1)

    def test_outcome_must_be_categorical_token(self):
        with self.assertRaises(InputError):
            parse_event({"usable": True, "outcome": "https://private.invalid/x"}, line_number=1)

    def test_summary_metrics(self):
        summary = summarize(
            [
                Event(True, latency_ms=100, cost_units=1, rotated=False, outcome="SUCCESS"),
                Event(False, latency_ms=200, cost_units=1, rotated=True, outcome="HTTP_RATE_LIMIT"),
                Event(True, latency_ms=300, cost_units=1, rotated=False, outcome="SUCCESS"),
                Event(False, latency_ms=400, cost_units=1, rotated=True, outcome="HTTP_5XX"),
            ]
        )
        self.assertEqual(summary.requests, 4)
        self.assertEqual(summary.usable_results, 2)
        self.assertEqual(summary.usable_success_rate, 0.5)
        self.assertEqual(summary.requests_per_usable_result, 2.0)
        self.assertEqual(summary.rotations, 2)
        self.assertEqual(summary.rotations_per_usable_result, 1.0)
        self.assertEqual(summary.latency_ms_p50, 250.0)
        self.assertEqual(summary.latency_ms_p95, 385.0)
        self.assertEqual(summary.total_cost_units, 4.0)
        self.assertEqual(summary.cost_units_per_usable_result, 2.0)
        self.assertEqual(summary.outcome_counts["SUCCESS"], 2)

    def test_partial_cost_coverage_does_not_invent_cost_per_success(self):
        summary = summarize([Event(True, cost_units=1), Event(False)])
        self.assertEqual(summary.cost_coverage, 0.5)
        self.assertIsNone(summary.cost_units_per_usable_result)

    def test_partial_rotation_coverage_does_not_invent_rotation_rate(self):
        summary = summarize([Event(True, rotated=True), Event(True)])
        self.assertEqual(summary.rotation_coverage, 0.5)
        self.assertIsNone(summary.rotations_per_usable_result)

    def test_empty_input_is_rejected(self):
        with self.assertRaises(InputError):
            summarize([])

    def test_wilson_interval_is_bounded(self):
        interval = wilson_interval(5, 10)
        self.assertIsNotNone(interval)
        low, high = interval
        self.assertGreaterEqual(low, 0)
        self.assertLessEqual(high, 1)
        self.assertLess(low, 0.5)
        self.assertGreater(high, 0.5)

    def test_compare_directional_metrics_and_pass_gate(self):
        baseline = summarize([Event(True), Event(False), Event(False), Event(False)])
        candidate = summarize([Event(True), Event(True), Event(False), Event(False)])
        result = compare_summaries(
            baseline,
            candidate,
            min_requests=4,
            min_success_uplift_pp=20,
            max_rpu_regression_pct=0,
        )
        self.assertEqual(result["delta"]["usable_success_uplift_pp"], 25.0)
        self.assertEqual(result["gate"]["verdict"], "PASS")

    def test_compare_missing_cost_is_inconclusive_when_cost_gate_enabled(self):
        baseline = summarize([Event(True), Event(False)])
        candidate = summarize([Event(True), Event(True)])
        result = compare_summaries(
            baseline,
            candidate,
            max_cost_regression_pct=5,
        )
        self.assertEqual(result["gate"]["verdict"], "INCONCLUSIVE")

    def test_compare_without_thresholds_does_not_claim_pass(self):
        baseline = summarize([Event(True)])
        candidate = summarize([Event(True)])
        result = compare_summaries(baseline, candidate)
        self.assertEqual(result["gate"]["verdict"], "NO_GATES_CONFIGURED")

    def test_jsonl_error_does_not_include_raw_line(self):
        marker = "DO-NOT-ECHO-THIS-SENSITIVE-VALUE"
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "events.jsonl"
            path.write_text('{"usable": true, "x": "' + marker + '"}\n', encoding="utf-8")
            with self.assertRaises(InputError) as caught:
                summarize_jsonl(path)
        self.assertNotIn(marker, str(caught.exception))

    def test_invalid_json_error_does_not_include_raw_line(self):
        marker = "DO-NOT-ECHO-INVALID-LINE"
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "events.jsonl"
            path.write_text("{" + marker + "\n", encoding="utf-8")
            with self.assertRaises(InputError) as caught:
                summarize_jsonl(path)
        self.assertNotIn(marker, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
