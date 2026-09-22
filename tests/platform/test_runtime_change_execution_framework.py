from platform.operations.runtime_change_execution_framework import (
    RuntimeChangeExecutionFramework,
)


def test_change_execution_plan_and_complete():
    framework = RuntimeChangeExecutionFramework()

    planned = framework.create_plan(
        change_id="chg-001",
        executor="controlled_executor",
        plan="apply approved agent capability change",
    )

    assert planned.status == "PLANNED"

    completed = framework.complete(
        "chg-001",
        "evidence-001",
    )

    assert completed.status == "COMPLETED"
    assert completed.evidence_ref == "evidence-001"
