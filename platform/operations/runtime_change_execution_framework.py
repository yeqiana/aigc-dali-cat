from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ExecutionStatus = Literal[
    "PLANNED",
    "EXECUTING",
    "COMPLETED",
    "FAILED",
    "ROLLED_BACK",
]


@dataclass(frozen=True)
class ChangeExecutionRecord:
    change_id: str
    executor: str
    plan: str
    status: ExecutionStatus
    evidence_ref: str | None


class RuntimeChangeExecutionFramework:
    """Controlled execution layer for approved runtime changes.

    This layer tracks execution lifecycle only. It does not directly mutate
    production runtime components.
    """

    def __init__(self) -> None:
        self._records: list[ChangeExecutionRecord] = []

    def create_plan(
        self,
        *,
        change_id: str,
        executor: str,
        plan: str,
    ) -> ChangeExecutionRecord:
        record = ChangeExecutionRecord(
            change_id=change_id,
            executor=executor,
            plan=plan,
            status="PLANNED",
            evidence_ref=None,
        )
        self._records.append(record)
        return record

    def list_all(self) -> tuple[ChangeExecutionRecord, ...]:
        return tuple(self._records)

    def complete(
        self,
        change_id: str,
        evidence_ref: str,
    ) -> ChangeExecutionRecord:
        old = next(item for item in self._records if item.change_id == change_id)
        updated = ChangeExecutionRecord(
            change_id=old.change_id,
            executor=old.executor,
            plan=old.plan,
            status="COMPLETED",
            evidence_ref=evidence_ref,
        )
        self._records[self._records.index(old)] = updated
        return updated
