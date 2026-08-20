from __future__ import annotations

import json
import math
import pathlib
import re
from collections import Counter
from collections.abc import Iterable, Mapping

from .models import Event, InputError, Summary


_ALLOWED_FIELDS = {"usable", "latency_ms", "cost_units", "rotated", "outcome"}
_OUTCOME_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_Z95 = 1.959963984540054


def _round(value: float | None, digits: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def _finite_nonnegative(value: object, *, line_number: int, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"line {line_number}: {field} must be a non-negative number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise InputError(f"line {line_number}: {field} must be a finite non-negative number")
    return number


def parse_event(raw: object, *, line_number: int) -> Event:
    """Parse one sanitized benchmark event without echoing raw input values."""
    if not isinstance(raw, Mapping):
        raise InputError(f"line {line_number}: event must be a JSON object")

    if set(raw) - _ALLOWED_FIELDS:
        raise InputError(f"line {line_number}: event contains unsupported fields")

    if "usable" not in raw or not isinstance(raw["usable"], bool):
        raise InputError(f"line {line_number}: usable must be a boolean")

    latency_ms = None
    if "latency_ms" in raw and raw["latency_ms"] is not None:
        latency_ms = _finite_nonnegative(
            raw["latency_ms"], line_number=line_number, field="latency_ms"
        )

    cost_units = None
    if "cost_units" in raw and raw["cost_units"] is not None:
        cost_units = _finite_nonnegative(
            raw["cost_units"], line_number=line_number, field="cost_units"
        )

    rotated = None
    if "rotated" in raw and raw["rotated"] is not None:
        if not isinstance(raw["rotated"], bool):
            raise InputError(f"line {line_number}: rotated must be a boolean")
        rotated = raw["rotated"]

    outcome = None
    if "outcome" in raw and raw["outcome"] is not None:
        if not isinstance(raw["outcome"], str) or not _OUTCOME_RE.fullmatch(raw["outcome"]):
            raise InputError(
                f"line {line_number}: outcome must be an uppercase categorical token"
            )
        outcome = raw["outcome"]

    return Event(
        usable=raw["usable"],
        latency_ms=latency_ms,
        cost_units=cost_units,
        rotated=rotated,
        outcome=outcome,
    )


def iter_jsonl(path: str | pathlib.Path) -> Iterable[Event]:
    """Yield validated events from JSONL while suppressing raw-line echo in errors."""
    with pathlib.Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise InputError(f"line {line_number}: invalid JSON") from exc
            yield parse_event(raw, line_number=line_number)


def wilson_interval(successes: int, total: int, *, z: float = _Z95) -> tuple[float, float] | None:
    """Return a descriptive Wilson score interval for a binomial proportion."""
    if total <= 0:
        return None
    p = successes / total
    denominator = 1 + (z * z / total)
    center = (p + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total)
        / denominator
    )
    return (_round(max(0.0, center - margin)), _round(min(1.0, center + margin)))


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def summarize(events: Iterable[Event]) -> Summary:
    requests = 0
    usable = 0
    rotations = 0
    rotation_seen = 0
    latencies: list[float] = []
    total_cost = 0.0
    cost_seen = 0
    outcome_seen = 0
    outcomes: Counter[str] = Counter()

    for event in events:
        requests += 1
        usable += int(event.usable)

        if event.rotated is not None:
            rotation_seen += 1
            rotations += int(event.rotated)

        if event.latency_ms is not None:
            latencies.append(event.latency_ms)

        if event.cost_units is not None:
            cost_seen += 1
            total_cost += event.cost_units

        if event.outcome is not None:
            outcome_seen += 1
            outcomes[event.outcome] += 1

    if requests == 0:
        raise InputError("input contains no benchmark events")

    success_rate = usable / requests
    rpu = requests / usable if usable else None

    full_rotation_coverage = rotation_seen == requests
    rotations_per_usable = (
        rotations / usable if usable and full_rotation_coverage else None
    )

    full_cost_coverage = cost_seen == requests
    cost_per_usable = (
        total_cost / usable if usable and full_cost_coverage else None
    )

    return Summary(
        requests=requests,
        usable_results=usable,
        usable_success_rate=_round(success_rate) or 0.0,
        usable_success_rate_wilson95=wilson_interval(usable, requests),
        requests_per_usable_result=_round(rpu),
        rotation_coverage=_round(rotation_seen / requests) or 0.0,
        rotations=rotations,
        rotations_per_usable_result=_round(rotations_per_usable),
        latency_coverage=_round(len(latencies) / requests) or 0.0,
        latency_ms_p50=_round(_quantile(latencies, 0.50)),
        latency_ms_p95=_round(_quantile(latencies, 0.95)),
        cost_coverage=_round(cost_seen / requests) or 0.0,
        total_cost_units=_round(total_cost) if cost_seen else None,
        cost_units_per_usable_result=_round(cost_per_usable),
        outcome_coverage=_round(outcome_seen / requests) or 0.0,
        outcome_counts=dict(sorted(outcomes.items())),
    )


def summarize_jsonl(path: str | pathlib.Path) -> Summary:
    return summarize(iter_jsonl(path))


def _pct_change(baseline: float | None, candidate: float | None) -> float | None:
    if baseline is None or candidate is None or baseline == 0:
        return None
    return _round(((candidate / baseline) - 1) * 100)


def compare_summaries(
    baseline: Summary,
    candidate: Summary,
    *,
    min_requests: int = 1,
    min_success_uplift_pp: float | None = None,
    max_rpu_regression_pct: float | None = None,
    max_cost_regression_pct: float | None = None,
    max_p95_latency_regression_pct: float | None = None,
) -> dict[str, object]:
    """Compare two summaries and optionally evaluate operator-defined gates."""
    if min_requests < 1:
        raise ValueError("min_requests must be >= 1")

    success_delta_pp = _round(
        (candidate.usable_success_rate - baseline.usable_success_rate) * 100
    )
    success_relative_pct = _pct_change(
        baseline.usable_success_rate, candidate.usable_success_rate
    )
    rpu_change_pct = _pct_change(
        baseline.requests_per_usable_result,
        candidate.requests_per_usable_result,
    )
    cost_change_pct = _pct_change(
        baseline.cost_units_per_usable_result,
        candidate.cost_units_per_usable_result,
    )
    rotation_change_pct = _pct_change(
        baseline.rotations_per_usable_result,
        candidate.rotations_per_usable_result,
    )
    p95_latency_change_pct = _pct_change(
        baseline.latency_ms_p95,
        candidate.latency_ms_p95,
    )

    configured = any(
        value is not None
        for value in (
            min_success_uplift_pp,
            max_rpu_regression_pct,
            max_cost_regression_pct,
            max_p95_latency_regression_pct,
        )
    )

    checks: dict[str, dict[str, object]] = {}
    verdict = "NO_GATES_CONFIGURED"

    if configured:
        if baseline.requests < min_requests or candidate.requests < min_requests:
            verdict = "INCONCLUSIVE"
        else:
            inconclusive = False
            failed = False

            def add_check(name: str, actual: float | None, threshold: float, *, mode: str) -> None:
                nonlocal inconclusive, failed
                if actual is None:
                    checks[name] = {
                        "actual": None,
                        "threshold": threshold,
                        "result": "INCONCLUSIVE",
                    }
                    inconclusive = True
                    return
                passed = actual >= threshold if mode == "min" else actual <= threshold
                checks[name] = {
                    "actual": actual,
                    "threshold": threshold,
                    "result": "PASS" if passed else "FAIL",
                }
                failed = failed or not passed

            if min_success_uplift_pp is not None:
                add_check(
                    "min_success_uplift_pp",
                    success_delta_pp,
                    min_success_uplift_pp,
                    mode="min",
                )
            if max_rpu_regression_pct is not None:
                add_check(
                    "max_rpu_regression_pct",
                    rpu_change_pct,
                    max_rpu_regression_pct,
                    mode="max",
                )
            if max_cost_regression_pct is not None:
                add_check(
                    "max_cost_regression_pct",
                    cost_change_pct,
                    max_cost_regression_pct,
                    mode="max",
                )
            if max_p95_latency_regression_pct is not None:
                add_check(
                    "max_p95_latency_regression_pct",
                    p95_latency_change_pct,
                    max_p95_latency_regression_pct,
                    mode="max",
                )

            if inconclusive:
                verdict = "INCONCLUSIVE"
            elif failed:
                verdict = "FAIL"
            else:
                verdict = "PASS"

    return {
        "baseline": baseline.to_dict(),
        "candidate": candidate.to_dict(),
        "delta": {
            "usable_success_uplift_pp": success_delta_pp,
            "usable_success_relative_pct": success_relative_pct,
            "requests_per_usable_result_change_pct": rpu_change_pct,
            "rotations_per_usable_result_change_pct": rotation_change_pct,
            "cost_per_usable_result_change_pct": cost_change_pct,
            "latency_p95_change_pct": p95_latency_change_pct,
        },
        "gate": {
            "min_requests_per_arm": min_requests,
            "verdict": verdict,
            "checks": checks,
        },
        "interpretation_note": (
            "Metrics and Wilson intervals are descriptive; request events may be correlated "
            "and this output is not a causal or independence claim."
        ),
    }
