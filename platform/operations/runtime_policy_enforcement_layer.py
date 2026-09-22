from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PolicyStatus = Literal["ALLOWED", "BLOCKED", "REVIEW_REQUIRED"]


@dataclass(frozen=True)
class PolicyEvaluation:
    target: str
    status: PolicyStatus
    reasons: tuple[str, ...]


class RuntimePolicyEnforcementLayer:
    """Runtime governance policy evaluation layer.

    This layer evaluates governance rules only. It does not execute changes,
    approve requests, or mutate runtime resources.
    """

    def evaluate(
        self,
        *,
        target: str,
        has_approval: bool,
        has_rollback_plan: bool,
        evidence_count: int,
        risk_level: str,
    ) -> PolicyEvaluation:
        reasons: list[str] = []

        if not has_approval:
            reasons.append("approval_missing")
        if not has_rollback_plan:
            reasons.append("rollback_plan_missing")
        if evidence_count < 1:
            reasons.append("evidence_missing")
        if risk_level == "HIGH":
            reasons.append("high_risk_review_required")

        if not has_approval or not has_rollback_plan or evidence_count < 1:
            status: PolicyStatus = "BLOCKED"
        elif risk_level == "HIGH":
            status = "REVIEW_REQUIRED"
        else:
            status = "ALLOWED"

        return PolicyEvaluation(
            target=target,
            status=status,
            reasons=tuple(reasons),
        )
