from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


CostOptimizationStatus = Literal["OPTIMAL", "WARNING", "OPTIMIZATION_REQUIRED"]


@dataclass(frozen=True)
class CostOptimizationSnapshot:
    runtime: str
    current_cost: float
    budget_limit: float
    utilization: float
    optimization_recommendation: str
    status: CostOptimizationStatus
    reasons: tuple[str, ...]


class RuntimeCostOptimizationGovernance:
    """Evaluate runtime cost efficiency.

    This layer only produces governance recommendations. It never changes
    runtime configuration, models, or resource allocation directly.
    """

    def evaluate(
        self,
        *,
        runtime: str,
        current_cost: float,
        budget_limit: float,
    ) -> CostOptimizationSnapshot:
        utilization = 0 if budget_limit <= 0 else current_cost / budget_limit * 100
        reasons: list[str] = []

        if utilization < 70:
            status: CostOptimizationStatus = "OPTIMAL"
            recommendation = "continue_current_strategy"
        elif utilization < 100:
            status = "WARNING"
            recommendation = "review_cost_trend"
            reasons.append("cost_budget_attention")
        else:
            status = "OPTIMIZATION_REQUIRED"
            recommendation = "create_cost_optimization_review"
            reasons.append("budget_exceeded")

        return CostOptimizationSnapshot(
            runtime=runtime,
            current_cost=current_cost,
            budget_limit=budget_limit,
            utilization=utilization,
            optimization_recommendation=recommendation,
            status=status,
            reasons=tuple(reasons),
        )
