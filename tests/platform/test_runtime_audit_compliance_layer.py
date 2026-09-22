from platform.operations.runtime_audit_compliance_layer import (
    AuditRecord,
    RuntimeAuditComplianceLayer,
)


def test_audit_record():
    layer = RuntimeAuditComplianceLayer()

    layer.record(
        AuditRecord(
            audit_id="audit-001",
            action_type="runtime_change",
            actor="operator",
            target="story-agent",
            evidence_ref="chg-evidence-001",
            status="RECORDED",
        )
    )

    assert len(layer.list_all()) == 1
    assert layer.review_required() == ()


def test_review_required():
    layer = RuntimeAuditComplianceLayer()

    layer.record(
        AuditRecord(
            audit_id="audit-002",
            action_type="runtime_change",
            actor="operator",
            target="workflow-engine",
            evidence_ref="chg-evidence-002",
            status="REVIEW_REQUIRED",
        )
    )

    assert len(layer.review_required()) == 1
