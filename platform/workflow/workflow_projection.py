from dataclasses import dataclass
from typing import Any


@dataclass
class ProjectionResult:
    event_type: str
    handled: bool
    message: str = ""


class WorkflowProjection:
    """Build workflow query view from events.

    This class only projects facts. It does not change runtime state.
    """

    def apply(self, event: dict[str, Any]) -> ProjectionResult:
        event_type = event.get("event_type", "")

        supported = {
            "WORKFLOW_STARTED",
            "TASK_STARTED",
            "TASK_COMPLETED",
            "TASK_FAILED",
        }

        return ProjectionResult(
            event_type=event_type,
            handled=event_type in supported,
            message="workflow projection applied"
            if event_type in supported
            else "event ignored",
        )
