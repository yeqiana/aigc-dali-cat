from datetime import datetime, timezone

from platform.gateway.ep002_production_runtime_verification import (
    EP002ProductionRuntimeVerificationResult,
)
from platform.gateway.production_migration_audit_report import (
    ProductionMigrationAuditReportBuilder,
)
from platform.gateway.runtime_primary_registry import RuntimePrimaryRecord


class FakeEvidence:
    episode_id = "10-02"
    current_runtime = "V3_RUNTIME"


def test_audit_report_verified_when_all_evidence_ready():
    report = ProductionMigrationAuditReportBuilder().build(
        final_evidence=FakeEvidence(),
        runtime_state=RuntimePrimaryRecord(
            primary_runtime="V3_RUNTIME",
            previous_runtime="V2_RUNTIME",
            reason="migration",
            updated_at=datetime.now(timezone.utc).isoformat(),
        ),
        ep002_verification=EP002ProductionRuntimeVerificationResult(
            episode_id="10-02",
            status="VERIFIED",
            checks=("all_checks_passed",),
            failures=(),
        ),
    )

    assert report.status == "VERIFIED"
    assert report.primary_runtime == "V3_RUNTIME"
