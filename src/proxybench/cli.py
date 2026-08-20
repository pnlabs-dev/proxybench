from __future__ import annotations

import argparse
import json
import sys

from .core import compare_summaries, summarize_jsonl
from .models import InputError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="proxybench",
        description="Benchmark sanitized proxy/web-retrieval outcomes without network I/O.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    summarize_cmd = sub.add_parser("summarize", help="summarize one JSONL benchmark arm")
    summarize_cmd.add_argument("input")

    compare_cmd = sub.add_parser("compare", help="compare baseline and candidate JSONL arms")
    compare_cmd.add_argument("baseline")
    compare_cmd.add_argument("candidate")
    compare_cmd.add_argument("--min-requests", type=int, default=1)
    compare_cmd.add_argument("--min-success-uplift-pp", type=float)
    compare_cmd.add_argument("--max-rpu-regression-pct", type=float)
    compare_cmd.add_argument("--max-cost-regression-pct", type=float)
    compare_cmd.add_argument("--max-p95-latency-regression-pct", type=float)

    return parser


def _validate_thresholds(args: argparse.Namespace) -> None:
    if getattr(args, "min_requests", 1) < 1:
        raise InputError("min_requests must be >= 1")

    for name in (
        "max_rpu_regression_pct",
        "max_cost_regression_pct",
        "max_p95_latency_regression_pct",
    ):
        value = getattr(args, name, None)
        if value is not None and value < 0:
            raise InputError(f"{name} must be >= 0")


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        _validate_thresholds(args)

        if args.command == "summarize":
            payload = summarize_jsonl(args.input).to_dict()
        else:
            baseline = summarize_jsonl(args.baseline)
            candidate = summarize_jsonl(args.candidate)
            payload = compare_summaries(
                baseline,
                candidate,
                min_requests=args.min_requests,
                min_success_uplift_pp=args.min_success_uplift_pp,
                max_rpu_regression_pct=args.max_rpu_regression_pct,
                max_cost_regression_pct=args.max_cost_regression_pct,
                max_p95_latency_regression_pct=args.max_p95_latency_regression_pct,
            )
    except (InputError, OSError):
        print("proxybench: input validation failed", file=sys.stderr)
        return 2

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
