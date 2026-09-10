from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


HealthStatus = Literal["HEALTHY", "DEGRADED", "UNHEALTHY"]


@dataclass(frozen=True)
class RuntimeHealthSnapshot:
    runtime: str
    status: HealthStatus
    health_score: float
    reasons: tuple[str, ...]


class RuntimeHealthMonitor:
    """Production runtime health evaluation layer.

    This module observes runtime state and emits health evidence only.
    It does not restart services or mutate runtime state.
    """

    def evaluate(
        self,
        *,
        runtime: str = "V3_RUNTIME",
        agent_success_rate: float,
        workflow_success_rate: float,
        trace_health: bool | None = None,
        memory_health: bool | None = None,
        trace_healthy: bool | None = None,
        memory_healthy: bool | None = None,
    ) -> RuntimeHealthSnapshot:
        """Evaluate runtime health.

        Supports both current naming (trace_health/memory_health) and
        legacy validation naming (trace_healthy/memory_healthy) during
        Phase9 migration validation.
        """
        if trace_health is None:
            trace_health = trace_healthy

        if memory_health is None:
            memory_health = memory_healthy

        if trace_health is None or memory_health is None:
            raise ValueError("trace and memory health signals are required")

        reasons: list[str] = []
        score = 100.0

        if agent_success_rate < 0.95:
            score -= 25
            reasons.append("agent_success_rate_low")

        if workflow_success_rate < 0.95:
            score -= 25
            reasons.append("workflow_success_rate_low")

        if not trace_health:
            score -= 25
            reasons.append("trace_unhealthy")

        if not memory_health:
            score -= 25
            reasons.append("memory_unhealthy")

        if score >= 90:
            status: HealthStatus = "HEALTHY"
        elif score >= 50:
            status = "DEGRADED"
        else:
            status = "UNHEALTHY"

        return RuntimeHealthSnapshot(
            runtime=runtime,
            status=status,
            health_score=max(score, 0),
            reasons=tuple(reasons),
        )
