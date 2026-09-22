from platform.operations.runtime_change_management import (
    RuntimeChangeManagement,
    RuntimeChangeRequest,
)


def test_change_request_create_and_approve():
    manager = RuntimeChangeManagement()

    manager.create(
        RuntimeChangeRequest(
            change_id="chg-001",
            source_task="gov-001",
            target="story-agent",
            reason="improve_retry_strategy",
            risk_level="LOW",
            rollback_plan="restore_previous_policy",
            status="CREATED",
        )
    )

    updated = manager.approve("chg-001")

    assert updated is not None
    assert updated.status == "APPROVED"


def test_change_request_empty():
    manager = RuntimeChangeManagement()

    assert manager.list_all() == ()
