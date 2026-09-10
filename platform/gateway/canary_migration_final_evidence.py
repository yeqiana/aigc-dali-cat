from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from platform.gateway.canary_production_switch_decision import ProductionSwitchDecision
from platform.gateway.canary_promotion_evidence import CanaryPromotionEvidence
from platform.gateway.canary_migration_record import CanaryMigrationRecord


@dataclass(frozen=True)
class CanaryMigrationFinalEvidence:
    """Final audit evidence for Canary -> Production migration.

    This object records why V3 was allowed to become primary runtime.
    It is evidence only and does not mutate runtime routing or business state.
    """

    episode_id: str
    previous_runtime: str
    current_runtime: str
    decision: str
    switch_reasons: tuple[str, ...]
    stage_percent: int
    request_count: int
    error_rate: float
    avg_latency_ms: float
    rollback_count: int
    generated_at: str


def build_final_evidence(
    *,
    decision: ProductionSwitchDecision,
    promotion: CanaryPromotionEvidence,
    migration: CanaryMigrationRecord,
    rollback_count: int = 0,
) -> CanaryMigrationFinalEvidence:
    return CanaryMigrationFinalEvidence(
        episode_id=decision.episode_id,
        previous_runtime=migration.from_runtime,
        current_runtime=migration.to_runtime,
        decision=decision.action,
        switch_reasons=decision.reasons,
        stage_percent=promotion.stage_percent,
        request_count=promotion.request_count,
        error_rate=promotion.error_rate,
        avg_latency_ms=promotion.avg_latency_ms,
        rollback_count=rollback_count,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
