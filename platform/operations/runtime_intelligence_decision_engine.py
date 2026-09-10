"""
Runtime Intelligence Decision Engine
Phase 9-P9.23

Aggregates operational signals into governance decisions.
This module only produces recommendations and does not execute changes.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class DecisionRecommendation:
    priority: str
    action: str
    risk_level: str
    requires_human_review: bool
    reasons: List[str]


class RuntimeIntelligenceDecisionEngine:
    def evaluate(
        self,
        slo_status: str,
        error_budget_status: str,
        capacity_status: str,
        cost_status: str,
        performance_status: str,
    ) -> DecisionRecommendation:
        reasons = []

        if slo_status == "VIOLATED":
            return DecisionRecommendation(
                priority="CRITICAL",
                action="stabilize_runtime",
                risk_level="HIGH",
                requires_human_review=True,
                reasons=["slo_violation"],
            )

        if error_budget_status == "EXHAUSTED":
            reasons.append("error_budget_exhausted")

        if capacity_status == "INSUFFICIENT":
            reasons.append("capacity_pressure")

        if cost_status == "OPTIMIZATION_REQUIRED":
            reasons.append("cost_pressure")

        if performance_status == "DEGRADED":
            reasons.append("performance_bottleneck")

        if reasons:
            return DecisionRecommendation(
                priority="WARNING",
                action="create_governance_review",
                risk_level="MEDIUM",
                requires_human_review=True,
                reasons=reasons,
            )

        return DecisionRecommendation(
            priority="NORMAL",
            action="continue_observation",
            risk_level="LOW",
            requires_human_review=False,
            reasons=[],
        )
