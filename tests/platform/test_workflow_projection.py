from platform.workflow.workflow_projection import WorkflowProjection


def test_workflow_projection_accepts_task_event():
    projection = WorkflowProjection()

    result = projection.apply(
        {
            "event_type": "TASK_COMPLETED",
            "aggregate_id": "task001",
        }
    )

    assert result.handled is True


def test_workflow_projection_ignores_unknown_event():
    result = WorkflowProjection().apply(
        {"event_type": "UNKNOWN"}
    )

    assert result.handled is False
