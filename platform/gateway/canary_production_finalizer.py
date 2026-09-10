from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from platform.gateway.canary_migration_record import CanaryMigrationRecord
from platform.gateway.canary_production_switch_decision import ProductionSwitchDecision


FinalizationStatus = Literal["FINALIZED", "BLOCKED"]


@dataclass(frozen=True)
class MigrationFinalizationResult:
    episode_id: str
    status: FinalizationStatus
    primary_runtime: str
    reasons: tuple[str, ...]


class CanaryProductionFinalizer:
    """Finalize V3 production migration after switch decision.

    This component records the migration conclusion only. It does not delete
    V2 runtime, mutate episode state, or modify production artifacts.
    """

    def finalize(
        self,
        decision: ProductionSwitchDecision,
        migration_record: CanaryMigrationRecord,
    ) -> MigrationFinalizationResult:
        if (
            decision.action == "SWITCH_TO_V3"
            and decision.target_runtime == "V3_RUNTIME"
            and migration_record.to_runtime == "V3_RUNTIME"
        ):
            return MigrationFinalizationResult(
                episode_id=decision.episode_id,
                status="FINALIZED",
                primary_runtime="V3_RUNTIME",
                reasons=("production_migration_completed",),
            )

        return MigrationFinalizationResult(
            episode_id=decision.episode_id,
            status="BLOCKED",
            primary_runtime="V2_RUNTIME",
            reasons=("migration_conditions_not_satisfied",),
        )
