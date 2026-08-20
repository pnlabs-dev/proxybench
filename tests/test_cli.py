import contextlib
import io
import json
import pathlib
import tempfile
import unittest

from proxybench.cli import run


class CliTests(unittest.TestCase):
    def test_summarize_outputs_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "events.jsonl"
            path.write_text('{"usable": true}\n{"usable": false}\n', encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = run(["summarize", str(path)])
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["requests"], 2)
        self.assertEqual(payload["usable_results"], 1)

    def test_compare_outputs_gate_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            baseline = pathlib.Path(tmp) / "baseline.jsonl"
            candidate = pathlib.Path(tmp) / "candidate.jsonl"
            baseline.write_text(
                '{"usable": true}\n{"usable": false}\n{"usable": false}\n{"usable": false}\n',
                encoding="utf-8",
            )
            candidate.write_text(
                '{"usable": true}\n{"usable": true}\n{"usable": false}\n{"usable": false}\n',
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = run(
                    [
                        "compare",
                        str(baseline),
                        str(candidate),
                        "--min-requests",
                        "4",
                        "--min-success-uplift-pp",
                        "20",
                    ]
                )
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["gate"]["verdict"], "PASS")

    def test_validation_error_does_not_echo_input(self):
        marker = "DO-NOT-ECHO-SECRET-CONTEXT"
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "events.jsonl"
            path.write_text(
                '{"usable": true, "private_context": "' + marker + '"}\n',
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = run(["summarize", str(path)])
        self.assertEqual(code, 2)
        self.assertNotIn(marker, stderr.getvalue())
        self.assertEqual(stderr.getvalue().strip(), "proxybench: input validation failed")

    def test_missing_file_does_not_echo_path(self):
        sensitive_path = "/private/customer-secret/events.jsonl"
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = run(["summarize", sensitive_path])
        self.assertEqual(code, 2)
        self.assertNotIn(sensitive_path, stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
