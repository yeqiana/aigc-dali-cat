from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from platform.gateway.canary_migration_final_evidence import CanaryMigrationFinalEvidence
from platform.gateway.ep002_production_runtime_verification import (
    EP002ProductionRuntimeVerificationResult,
)
from platform.gateway.runtime_primary_registry import RuntimePrimaryState


AuditStatus = str


@dataclass(frozen=True)
class ProductionMigrationAuditReport:
    episode_id: str
    status: AuditStatus
    primary_runtime: str
    evidence_items: tuple[str, ...]
    generated_at: str


class ProductionMigrationAuditReportBuilder:
    """Aggregate migration facts into an audit report.

    This is an evidence aggregation layer only. It does not perform migration
    actions and does not mutate runtime state.
    """

    def build(
        self,
        *,
        final_evidence: CanaryMigrationFinalEvidence,
        runtime_state: RuntimePrimaryState,
        ep002_verification: EP002ProductionRuntimeVerificationResult,
    ) -> ProductionMigrationAuditReport:
        evidence_items: list[str] = [
            "canary_migration_final_evidence",
            "runtime_primary_registry",
            "ep002_production_runtime_verification",
        ]

        verified = (
            final_evidence.current_runtime == "V3_RUNTIME"
            and runtime_state.primary_runtime == "V3_RUNTIME"
            and ep002_verification.verified
        )

        return ProductionMigrationAuditReport(
            episode_id=final_evidence.episode_id,
            status="VERIFIED" if verified else "FAILED",
            primary_runtime=runtime_state.primary_runtime,
            evidence_items=tuple(evidence_items),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
