from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


CompletionStatus = Literal["COMPLETED", "BLOCKED"]


@dataclass(frozen=True)
class ProductionMigrationCompletionResult:
    status: CompletionStatus
    primary_runtime: str
    message: str
    phase: str = "Phase 8"


class ProductionMigrationCompletion:
    """Final completion gate for Story OS V3 production migration.

    This module closes the migration process after audit verification.
    It does not remove V2 runtime or mutate business state.
    """

    def complete(
        self,
        *,
        audit_verified: bool,
        primary_runtime: str,
    ) -> ProductionMigrationCompletionResult:
        if not audit_verified:
            return ProductionMigrationCompletionResult(
                status="BLOCKED",
                primary_runtime=primary_runtime,
                message="production_migration_audit_failed",
            )

        if primary_runtime != "V3_RUNTIME":
            return ProductionMigrationCompletionResult(
                status="BLOCKED",
                primary_runtime=primary_runtime,
                message="v3_is_not_primary_runtime",
            )

        return ProductionMigrationCompletionResult(
            status="COMPLETED",
            primary_runtime="V3_RUNTIME",
            message="story_os_v3_production_migration_completed",
        )
