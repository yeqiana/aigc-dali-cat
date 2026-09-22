from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


OperationStatus = Literal["READY", "DEGRADED", "FAILED"]


@dataclass(frozen=True)
class PostMigrationOperationsSnapshot:
    primary_runtime: str
    runtime_health: bool
    agent_reliability: bool
    memory_health: bool
    trace_health: bool
    status: OperationStatus
    reasons: tuple[str, ...]


class PostMigrationOperations:
    """Phase 9 operational health evaluation after V3 migration.

    This module observes production state. It does not replace migration
    decisions and does not mutate runtime configuration.
    """

    def evaluate(
        self,
        *,
        primary_runtime: str,
        runtime_health: bool,
        agent_reliability: bool,
        memory_health: bool,
        trace_health: bool,
    ) -> PostMigrationOperationsSnapshot:
        reasons: list[str] = []

        if primary_runtime != "V3_RUNTIME":
            reasons.append("v3_not_primary")
        if not runtime_health:
            reasons.append("runtime_unhealthy")
        if not agent_reliability:
            reasons.append("agent_reliability_degraded")
        if not memory_health:
            reasons.append("memory_unhealthy")
        if not trace_health:
            reasons.append("trace_unhealthy")

        if reasons:
            status: OperationStatus = "DEGRADED"
        else:
            status = "READY"

        return PostMigrationOperationsSnapshot(
            primary_runtime=primary_runtime,
            runtime_health=runtime_health,
            agent_reliability=agent_reliability,
            memory_health=memory_health,
            trace_health=trace_health,
            status=status,
            reasons=tuple(reasons),
        )
