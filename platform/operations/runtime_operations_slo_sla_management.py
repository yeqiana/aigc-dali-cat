from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


SLOStatus = Literal["COMPLIANT", "WARNING", "VIOLATED"]


@dataclass(frozen=True)
class RuntimeSLOSnapshot:
    runtime: str
    availability: float
    latency_ms: float
    error_rate: float
    mttr_minutes: float
    status: SLOStatus
    reasons: tuple[str, ...]


class RuntimeOperationsSLOSLAManagement:
    """Evaluates runtime SLO/SLA indicators.

    This module only evaluates service objectives. It does not trigger
    remediation, change runtime configuration, or execute operations.
    """

    def evaluate(
        self,
        *,
        runtime: str,
        availability: float,
        latency_ms: float,
        error_rate: float,
        mttr_minutes: float,
    ) -> RuntimeSLOSnapshot:
        reasons: list[str] = []

        if availability < 99.0:
            reasons.append("availability_below_target")
        if latency_ms > 3000:
            reasons.append("latency_above_target")
        if error_rate > 5:
            reasons.append("error_rate_above_target")
        if mttr_minutes > 60:
            reasons.append("mttr_above_target")

        if not reasons:
            status: SLOStatus = "COMPLIANT"
        elif len(reasons) <= 2:
            status = "WARNING"
        else:
            status = "VIOLATED"

        return RuntimeSLOSnapshot(
            runtime=runtime,
            availability=availability,
            latency_ms=latency_ms,
            error_rate=error_rate,
            mttr_minutes=mttr_minutes,
            status=status,
            reasons=tuple(reasons),
        )
