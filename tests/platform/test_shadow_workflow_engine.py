from platform.workflow.shadow_workflow_engine import ShadowWorkflowEngine


def test_shadow_engine_calculates_next_step():
    engine = ShadowWorkflowEngine()

    result = engine.decide_next_step("IMAGE_GENERATE", "SUCCESS")

    assert result.next_step == "IMAGE_REVIEW"


def test_shadow_engine_does_not_execute():
    engine = ShadowWorkflowEngine()

    result = engine.decide_next_step("UNKNOWN", "SUCCESS")

    assert result.next_step is None
