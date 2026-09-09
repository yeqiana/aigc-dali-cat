from platform.workflow.dual_workflow_state import DualWorkflowStateChecker


def test_dual_state_match():
    result = DualWorkflowStateChecker().compare("SUCCESS", "SUCCESS")
    assert result.matched is True


def test_dual_state_mismatch():
    result = DualWorkflowStateChecker().compare("RUNNING", "SUCCESS")
    assert result.matched is False
