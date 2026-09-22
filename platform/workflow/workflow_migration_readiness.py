from dataclasses import dataclass


@dataclass
class WorkflowMigrationReadinessReport:
    event_coverage: float
    projection_accuracy: float
    shadow_engine_match_rate: float
    ready: bool


class WorkflowMigrationReadinessChecker:
    """评估 Workflow 从 Runtime 接管前的准备度。"""

    def evaluate(
        self,
        event_coverage: float,
        projection_accuracy: float,
        shadow_engine_match_rate: float,
    ) -> WorkflowMigrationReadinessReport:
        ready = (
            event_coverage >= 0.99
            and projection_accuracy >= 0.99
            and shadow_engine_match_rate >= 0.99
        )

        return WorkflowMigrationReadinessReport(
            event_coverage=event_coverage,
            projection_accuracy=projection_accuracy,
            shadow_engine_match_rate=shadow_engine_match_rate,
            ready=ready,
        )
