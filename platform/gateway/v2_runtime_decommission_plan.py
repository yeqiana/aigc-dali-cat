from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


DecommissionStage = Literal["ACTIVE", "READ_ONLY", "OBSERVE", "ARCHIVED"]


@dataclass(frozen=True)
class V2DecommissionPlan:
    """Safe retirement plan for legacy V2 runtime.

    This plan describes migration readiness only. It never removes runtime code
    or production data automatically.
    """

    episode_id: str
    current_stage: DecommissionStage
    reason: str


class V2RuntimeDecommissionPlanner:
    """Generate V2 retirement steps after V3 becomes primary."""

    def create_plan(self, episode_id: str, *, v3_primary: bool) -> V2DecommissionPlan:
        if not v3_primary:
            return V2DecommissionPlan(
                episode_id=episode_id,
                current_stage="ACTIVE",
                reason="v3_not_primary",
            )

        return V2DecommissionPlan(
            episode_id=episode_id,
            current_stage="READ_ONLY",
            reason="v3_primary_runtime_enabled",
        )

    def advance_observation(self, plan: V2DecommissionPlan) -> V2DecommissionPlan:
        if plan.current_stage != "READ_ONLY":
            return plan

        return V2DecommissionPlan(
            episode_id=plan.episode_id,
            current_stage="OBSERVE",
            reason="legacy_runtime_observation_window",
        )

    def archive(self, plan: V2DecommissionPlan) -> V2DecommissionPlan:
        if plan.current_stage != "OBSERVE":
            return plan

        return V2DecommissionPlan(
            episode_id=plan.episode_id,
            current_stage="ARCHIVED",
            reason="legacy_runtime_archived",
        )
