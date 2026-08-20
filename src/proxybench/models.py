from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


class InputError(ValueError):
    """Raised when sanitized benchmark input does not satisfy the public schema."""


@dataclass(frozen=True)
class Event:
    usable: bool
    latency_ms: float | None = None
    cost_units: float | None = None
    rotated: bool | None = None
    outcome: str | None = None


@dataclass(frozen=True)
class Summary:
    requests: int
    usable_results: int
    usable_success_rate: float
    usable_success_rate_wilson95: tuple[float, float] | None
    requests_per_usable_result: float | None
    rotation_coverage: float
    rotations: int
    rotations_per_usable_result: float | None
    latency_coverage: float
    latency_ms_p50: float | None
    latency_ms_p95: float | None
    cost_coverage: float
    total_cost_units: float | None
    cost_units_per_usable_result: float | None
    outcome_coverage: float
    outcome_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        interval = self.usable_success_rate_wilson95
        data["usable_success_rate_wilson95"] = (
            list(interval) if interval is not None else None
        )
        return data
