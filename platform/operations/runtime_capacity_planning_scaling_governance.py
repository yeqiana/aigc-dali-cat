from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


CapacityStatus = Literal["OPTIMAL", "WARNING", "INSUFFICIENT"]


@dataclass(frozen=True)
class CapacityPlanningSnapshot:
    runtime: str
    current_load: float
    capacity_limit: float
    utilization: float
    scaling_recommendation: str
    status: CapacityStatus
    reasons: tuple[str, ...]


class RuntimeCapacityPlanningScalingGovernance:
    """Capacity evaluation layer.

    This module evaluates capacity pressure and produces scaling
    recommendations. It does not directly scale production resources or
    mutate runtime configuration.
    """

    def evaluate(
        self,
        *,
        runtime: str,
        current_load: float,
        capacity_limit: float,
    ) -> CapacityPlanningSnapshot:
        utilization = 0.0 if capacity_limit <= 0 else current_load / capacity_limit * 100
        reasons: list[str] = []

        if utilization >= 90:
            status: CapacityStatus = "INSUFFICIENT"
            recommendation = "scale_up_review_required"
            reasons.append("capacity_pressure_high")
        elif utilization >= 70:
            status = "WARNING"
            recommendation = "monitor_capacity_trend"
            reasons.append("capacity_usage_increasing")
        else:
            status = "OPTIMAL"
            recommendation = "no_scaling_action"

        return CapacityPlanningSnapshot(
            runtime=runtime,
            current_load=current_load,
            capacity_limit=capacity_limit,
            utilization=utilization,
            scaling_recommendation=recommendation,
            status=status,
            reasons=tuple(reasons),
        )
