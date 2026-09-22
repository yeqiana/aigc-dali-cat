from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


OperationsStatus = Literal["HEALTHY", "DEGRADED", "ACTION_REQUIRED"]


@dataclass(frozen=True)
class RuntimeOperationsSnapshot:
    runtime: str
    health_status: str
    incident_count: int
    recovery_ready: bool
    reliability_status: str
    cost_status: str
    performance_status: str
    learning_status: str
    operations_status: OperationsStatus
    reasons: tuple[str, ...]


class RuntimeOperationsControlPlane:
    """Aggregates production operations signals.

    This is a governance/control plane aggregation layer. It observes
    existing operations modules and does not mutate runtime behavior.
    """

    def evaluate(
        self,
        *,
        runtime: str,
        health_status: str,
        incident_count: int,
        recovery_ready: bool,
        reliability_status: str,
        cost_status: str,
        performance_status: str,
        learning_status: str,
    ) -> RuntimeOperationsSnapshot:
        reasons: list[str] = []

        if health_status != "HEALTHY":
            reasons.append("health_degraded")
        if incident_count > 0:
            reasons.append("active_incident")
        if not recovery_ready:
            reasons.append("recovery_not_ready")
        if cost_status != "NORMAL":
            reasons.append("cost_attention_required")
        if performance_status != "OPTIMAL":
            reasons.append("performance_attention_required")

        if reasons:
            status: OperationsStatus = "ACTION_REQUIRED"
        elif learning_status in ("NEEDS_REVIEW", "BLOCKED"):
            reasons.append("learning_review_required")
            status = "DEGRADED"
        else:
            status = "HEALTHY"

        return RuntimeOperationsSnapshot(
            runtime=runtime,
            health_status=health_status,
            incident_count=incident_count,
            recovery_ready=recovery_ready,
            reliability_status=reliability_status,
            cost_status=cost_status,
            performance_status=performance_status,
            learning_status=learning_status,
            operations_status=status,
            reasons=tuple(reasons),
        )
