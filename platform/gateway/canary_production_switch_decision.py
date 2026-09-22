from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from platform.gateway.canary_promotion_evidence import CanaryPromotionEvidence


SwitchAction = Literal["KEEP_CANARY", "SWITCH_TO_V3", "BLOCK"]


@dataclass(frozen=True)
class ProductionSwitchDecision:
    episode_id: str
    action: SwitchAction
    reasons: tuple[str, ...]
    target_runtime: str


@dataclass(frozen=True)
class ProductionSwitchPolicy:
    required_stage_percent: int = 100
    min_requests: int = 100
    max_error_rate: float = 0.05


class CanaryProductionSwitchDecision:
    """Final decision layer before V3 becomes production primary.

    This layer only decides. It does not delete V2 runtime or mutate episode data.
    """

    def __init__(self, policy: ProductionSwitchPolicy | None = None):
        self.policy = policy or ProductionSwitchPolicy()

    def evaluate(self, evidence: CanaryPromotionEvidence) -> ProductionSwitchDecision:
        if evidence.stage_percent < self.policy.required_stage_percent:
            return ProductionSwitchDecision(
                evidence.episode_id,
                "KEEP_CANARY",
                ("canary_not_completed",),
                "V2_RUNTIME",
            )

        if evidence.request_count < self.policy.min_requests:
            return ProductionSwitchDecision(
                evidence.episode_id,
                "BLOCK",
                ("insufficient_production_evidence",),
                "V2_RUNTIME",
            )

        if evidence.error_rate > self.policy.max_error_rate:
            return ProductionSwitchDecision(
                evidence.episode_id,
                "BLOCK",
                ("error_rate_not_acceptable",),
                "V2_RUNTIME",
            )

        return ProductionSwitchDecision(
            evidence.episode_id,
            "SWITCH_TO_V3",
            ("canary_production_ready",),
            "V3_RUNTIME",
        )
