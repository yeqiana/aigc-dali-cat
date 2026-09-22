from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


GovernanceStatus = Literal[
    "CREATED",
    "PENDING_APPROVAL",
    "APPROVED",
    "REJECTED",
    "COMPLETED",
]


@dataclass(frozen=True)
class GovernanceTask:
    """A governance workflow item derived from operational evidence.

    Governance tasks record decisions. They do not directly mutate production
    runtime components.
    """

    task_id: str
    source: str
    recommendation: str
    evidence_refs: tuple[str, ...]
    status: GovernanceStatus


class OperationsGovernanceWorkflow:
    """Human-in-the-loop governance workflow layer."""

    def create_task(
        self,
        *,
        task_id: str,
        source: str,
        recommendation: str,
        evidence_refs: tuple[str, ...],
    ) -> GovernanceTask:
        return GovernanceTask(
            task_id=task_id,
            source=source,
            recommendation=recommendation,
            evidence_refs=evidence_refs,
            status="PENDING_APPROVAL",
        )

    def approve(self, task: GovernanceTask) -> GovernanceTask:
        return GovernanceTask(
            task_id=task.task_id,
            source=task.source,
            recommendation=task.recommendation,
            evidence_refs=task.evidence_refs,
            status="APPROVED",
        )
