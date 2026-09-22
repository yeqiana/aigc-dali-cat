from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


ReleasePackageStatus = Literal["READY", "BLOCKED"]


@dataclass(frozen=True)
class Phase8FinalReleasePackage:
    status: ReleasePackageStatus
    runtime: str
    migration_state: str
    v2_retirement_state: str
    generated_at: str
    reasons: tuple[str, ...]


class Phase8FinalReleasePackageBuilder:
    """Builds the final delivery package for Phase 8 migration.

    This is an evidence summary layer. It does not change runtime routing,
    episode state, or retirement execution.
    """

    def build(
        self,
        *,
        migration_completed: bool,
        primary_runtime: str,
        v2_retirement_state: str = "PLANNED",
    ) -> Phase8FinalReleasePackage:
        if not migration_completed:
            return Phase8FinalReleasePackage(
                status="BLOCKED",
                runtime=primary_runtime,
                migration_state="INCOMPLETE",
                v2_retirement_state=v2_retirement_state,
                generated_at=datetime.now(timezone.utc).isoformat(),
                reasons=("migration_not_completed",),
            )

        if primary_runtime != "V3_RUNTIME":
            return Phase8FinalReleasePackage(
                status="BLOCKED",
                runtime=primary_runtime,
                migration_state="INCOMPLETE",
                v2_retirement_state=v2_retirement_state,
                generated_at=datetime.now(timezone.utc).isoformat(),
                reasons=("v3_not_primary_runtime",),
            )

        return Phase8FinalReleasePackage(
            status="READY",
            runtime="V3_RUNTIME",
            migration_state="COMPLETED",
            v2_retirement_state=v2_retirement_state,
            generated_at=datetime.now(timezone.utc).isoformat(),
            reasons=("phase8_release_ready",),
        )
