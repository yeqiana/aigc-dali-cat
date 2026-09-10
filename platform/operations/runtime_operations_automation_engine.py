from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


AutomationStatus = Literal["READY", "BLOCKED", "MANUAL_APPROVAL"]


@dataclass(frozen=True)
class AutomationPlan:
    change_id: str
    executor: str
    action: str
    status: AutomationStatus
    reasons: tuple[str, ...]


class RuntimeOperationsAutomationEngine:
    """Automation orchestration layer.

    This layer creates execution plans only. It does not directly mutate
    production runtime, agents, workflows, or configurations.
    """

    def create_plan(
        self,
        *,
        change_id: str,
        approved: bool,
        policy_allowed: bool,
        risk_level: str,
    ) -> AutomationPlan:
        reasons: list[str] = []

        if not approved:
            return AutomationPlan(
                change_id=change_id,
                executor="none",
                action="none",
                status="BLOCKED",
                reasons=("approval_missing",),
            )

        if not policy_allowed:
            return AutomationPlan(
                change_id=change_id,
                executor="none",
                action="none",
                status="BLOCKED",
                reasons=("policy_blocked",),
            )

        if risk_level.upper() == "HIGH":
            reasons.append("high_risk_requires_manual_approval")
            return AutomationPlan(
                change_id=change_id,
                executor="manual",
                action="review_required",
                status="MANUAL_APPROVAL",
                reasons=tuple(reasons),
            )

        return AutomationPlan(
            change_id=change_id,
            executor="controlled_executor",
            action="execute_change_plan",
            status="READY",
            reasons=tuple(reasons),
        )
