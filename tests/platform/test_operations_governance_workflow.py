from platform.operations.operations_governance_workflow import (
    OperationsGovernanceWorkflow,
)


def test_governance_task_creation_and_approval():
    workflow = OperationsGovernanceWorkflow()

    task = workflow.create_task(
        task_id="gov-001",
        source="learning_pattern",
        recommendation="improve_tool_retry_strategy",
        evidence_refs=("exp-001",),
    )

    assert task.status == "PENDING_APPROVAL"

    approved = workflow.approve(task)

    assert approved.status == "APPROVED"
    assert approved.evidence_refs == ("exp-001",)
