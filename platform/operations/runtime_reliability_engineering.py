from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ReliabilityStatus = Literal["HEALTHY", "DEGRADED", "UNRELIABLE"]


@dataclass(frozen=True)
class ReliabilitySnapshot:
    runtime: str
    agent_success_rate: float
    workflow_success_rate: float
    trace_completeness: float
    mttr_minutes: float
    reliability_score: float
    status: ReliabilityStatus
    reasons: tuple[str, ...]


class RuntimeReliabilityEngineering:
    """Production reliability evaluation layer.

    Collects reliability indicators only. It does not trigger recovery,
    routing changes, or runtime mutation.
    """

    def evaluate(
        self,
        *,
        runtime: str,
        agent_success_rate: float,
        workflow_success_rate: float,
        trace_completeness: float,
        mttr_minutes: float,
    ) -> ReliabilitySnapshot:
        score = (
            agent_success_rate * 0.35
            + workflow_success_rate * 0.35
            + trace_completeness * 0.2
            + max(0, 100 - mttr_minutes) * 0.1
        )

        reasons: list[str] = []
        if agent_success_rate < 95:
            reasons.append("agent_reliability_low")
        if workflow_success_rate < 95:
            reasons.append("workflow_reliability_low")
        if trace_completeness < 95:
            reasons.append("trace_completeness_low")

        status: ReliabilityStatus
        if score < 70:
            status = "UNRELIABLE"
        elif (
            agent_success_rate < 95
            or workflow_success_rate < 95
            or trace_completeness < 95
        ):
            status = "DEGRADED"
        else:
            status = "HEALTHY"

        return ReliabilitySnapshot(
            runtime=runtime,
            agent_success_rate=agent_success_rate,
            workflow_success_rate=workflow_success_rate,
            trace_completeness=trace_completeness,
            mttr_minutes=mttr_minutes,
            reliability_score=score,
            status=status,
            reasons=tuple(reasons),
        )
