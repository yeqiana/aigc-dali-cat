from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from platform.gateway.production_ownership_consumer import OwnershipEvidence


CompletionStatus = Literal["COMPLETED", "BLOCKED"]


@dataclass(frozen=True)
class ProductionMigrationCompletionResult:
    status: CompletionStatus
    primary_runtime: str
    message: str
    recorded_ownership: bool = False
    effective_ownership: bool = False
    production_consumers: tuple[str, ...] = ()
    phase: str = "Phase 8"

    @property
    def takeover_state(self) -> str:
        if self.effective_ownership:
            return "EFFECTIVE"
        if self.recorded_ownership:
            return "RECORDED_ONLY"
        return "NOT_SWITCHED"


class ProductionMigrationCompletion:
    """Final completion gate for Story OS V3 production migration.

    This module closes the migration process after audit verification.
    It does not remove V2 runtime or mutate business state.

    A recorded switch is not a takeover. Until 2026-09-15 this gate returned
    COMPLETED on ``audit_verified and primary_runtime == "V3_RUNTIME"`` alone --
    both of which are satisfied by the ownership record describing itself. On the
    real repository that produced "story_os_v3_production_migration_completed"
    while the production kernel read the record zero times and ran unchanged
    (W-11). The record cannot be its own witness, so completion now also requires
    evidence of a production-side consumer, and absence of that evidence
    fail-closes to BLOCKED.
    """

    def complete(
        self,
        *,
        audit_verified: bool,
        primary_runtime: str,
        production_consumers: tuple[str, ...] = (),
    ) -> ProductionMigrationCompletionResult:
        """Close the migration, or explain which precondition is unmet.

        ``production_consumers`` defaults to empty rather than to a permissive
        value: a caller that supplies no consumer evidence has not shown a
        takeover, and the safe reading of "no evidence" is "not established".
        """
        consumers = tuple(production_consumers)
        recorded = primary_runtime == "V3_RUNTIME"
        effective = bool(consumers)
        evidence = {
            "primary_runtime": primary_runtime,
            "recorded_ownership": recorded,
            "effective_ownership": effective,
            "production_consumers": consumers,
        }

        if not audit_verified:
            return ProductionMigrationCompletionResult(
                status="BLOCKED",
                message="production_migration_audit_failed",
                **evidence,
            )

        if not recorded:
            return ProductionMigrationCompletionResult(
                status="BLOCKED",
                message="v3_is_not_primary_runtime",
                **evidence,
            )

        if not effective:
            return ProductionMigrationCompletionResult(
                status="BLOCKED",
                message="ownership_recorded_but_no_production_consumer",
                **evidence,
            )

        return ProductionMigrationCompletionResult(
            status="COMPLETED",
            message="story_os_v3_production_migration_completed",
            **evidence,
        )


def complete_from_repository(
    *,
    audit_verified: bool,
    root,
    recorded_runtime: str,
    assess=None,
) -> ProductionMigrationCompletionResult:
    """Run the gate against the tree instead of against caller-supplied strings.

    Convenience for the readiness path: derives ``production_consumers`` from
    :mod:`platform.gateway.production_ownership_consumer` so a caller cannot
    accidentally assert a consumer set by hand.
    """
    if assess is None:
        from platform.gateway.production_ownership_consumer import assess as assess_fn

        assess = assess_fn
    evidence: OwnershipEvidence = assess(root, recorded_runtime)
    return ProductionMigrationCompletion().complete(
        audit_verified=audit_verified,
        primary_runtime=recorded_runtime,
        production_consumers=evidence.production_consumers,
    )
