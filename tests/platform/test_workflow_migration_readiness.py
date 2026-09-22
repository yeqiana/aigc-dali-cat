from platform.workflow.workflow_migration_readiness import (
    WorkflowMigrationReadinessChecker,
)


def test_ready_when_metrics_pass():
    report = WorkflowMigrationReadinessChecker().evaluate(
        1.0, 1.0, 1.0
    )

    assert report.ready is True


def test_not_ready_when_metric_failed():
    report = WorkflowMigrationReadinessChecker().evaluate(
        0.9, 1.0, 1.0
    )

    assert report.ready is False
