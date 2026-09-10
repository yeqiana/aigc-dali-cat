from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from platform.gateway.canary_auto_rollback import (
    CanaryAutoRollbackPolicy,
    CanaryRollbackDecision,
    CanaryRollbackPolicy,
)
from platform.gateway.canary_observability_metrics import CanaryMetricsSnapshot
from platform.gateway.canary_runtime_gateway import CanaryRuntimeGateway


RolloutAction = Literal["HOLD", "PROMOTE", "ROLLBACK", "COMPLETE"]


@dataclass(frozen=True)
class CanaryRolloutPlan:
    stages: tuple[int, ...] = (1, 5, 10, 25, 50, 100)
    min_requests_per_stage: int = 20

    def validate(self) -> None:
        if not self.stages:
            raise ValueError("rollout stages must not be empty")
        if self.stages[-1] != 100:
            raise ValueError("rollout stages must end at 100")
        if any(stage < 1 or stage > 100 for stage in self.stages):
            raise ValueError("rollout stages must be between 1 and 100")
        if tuple(sorted(set(self.stages))) != self.stages:
            raise ValueError("rollout stages must be unique and strictly increasing")
        if self.min_requests_per_stage < 1:
            raise ValueError("min_requests_per_stage must be at least 1")


@dataclass(frozen=True)
class CanaryRolloutDecision:
    episode_id: str
    action: RolloutAction
    current_percent: int
    next_percent: int
    reasons: tuple[str, ...]
    rollback_decision: CanaryRollbackDecision | None = None


@dataclass(frozen=True)
class CanaryRolloutApplyResult:
    enabled: bool
    percent: int
    action: RolloutAction


class CanaryProgressiveRollout:
    """Evaluate one progressive canary rollout step.

    The evaluator does not mutate routing. It combines stage progression with
    the existing P8.5 rollback policy and emits an explicit decision.
    """

    def __init__(
        self,
        plan: CanaryRolloutPlan | None = None,
        rollback_policy: CanaryRollbackPolicy | None = None,
    ) -> None:
        self.plan = plan or CanaryRolloutPlan()
        self.plan.validate()
        self.rollback_evaluator = CanaryAutoRollbackPolicy(rollback_policy)

    def evaluate(
        self,
        snapshot: CanaryMetricsSnapshot,
        *,
        current_percent: int,
        trace_healthy: bool = True,
    ) -> CanaryRolloutDecision:
        if current_percent == 0:
            return CanaryRolloutDecision(
                episode_id=snapshot.episode_id,
                action="PROMOTE",
                current_percent=0,
                next_percent=self.plan.stages[0],
                reasons=("rollout_started",),
            )

        if current_percent not in self.plan.stages:
            raise ValueError("current_percent must be 0 or one of the configured rollout stages")

        rollback_decision = self.rollback_evaluator.evaluate(
            snapshot,
            trace_healthy=trace_healthy,
        )
        if rollback_decision.should_rollback:
            return CanaryRolloutDecision(
                episode_id=snapshot.episode_id,
                action="ROLLBACK",
                current_percent=current_percent,
                next_percent=0,
                reasons=rollback_decision.reasons,
                rollback_decision=rollback_decision,
            )

        if snapshot.total_requests < self.plan.min_requests_per_stage:
            return CanaryRolloutDecision(
                episode_id=snapshot.episode_id,
                action="HOLD",
                current_percent=current_percent,
                next_percent=current_percent,
                reasons=("insufficient_stage_sample_size",),
                rollback_decision=rollback_decision,
            )

        if current_percent == 100:
            return CanaryRolloutDecision(
                episode_id=snapshot.episode_id,
                action="COMPLETE",
                current_percent=100,
                next_percent=100,
                reasons=("rollout_complete",),
                rollback_decision=rollback_decision,
            )

        current_index = self.plan.stages.index(current_percent)
        next_percent = self.plan.stages[current_index + 1]
        return CanaryRolloutDecision(
            episode_id=snapshot.episode_id,
            action="PROMOTE",
            current_percent=current_percent,
            next_percent=next_percent,
            reasons=("stage_healthy",),
            rollback_decision=rollback_decision,
        )


class CanaryProgressiveRolloutController:
    """Apply a rollout decision to gateway configuration only."""

    def apply(
        self,
        decision: CanaryRolloutDecision,
        gateway: CanaryRuntimeGateway,
    ) -> CanaryRolloutApplyResult:
        if decision.action == "ROLLBACK":
            gateway.configure(enabled=False, percent=0)
        elif decision.action in ("PROMOTE", "COMPLETE"):
            gateway.configure(enabled=True, percent=decision.next_percent)

        return CanaryRolloutApplyResult(
            enabled=gateway.canary_enabled,
            percent=gateway.canary_percent,
            action=decision.action,
        )
