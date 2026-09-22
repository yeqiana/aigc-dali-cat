from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ChangeStatus = Literal[
    "CREATED",
    "RISK_ASSESSED",
    "APPROVED",
    "EXECUTING",
    "COMPLETED",
    "ROLLED_BACK",
]


@dataclass(frozen=True)
class RuntimeChangeRequest:
    """Controlled runtime change request.

    Change requests describe approved intent only. They do not mutate runtime
    configuration directly.
    """

    change_id: str
    source_task: str
    target: str
    reason: str
    risk_level: str
    rollback_plan: str
    status: ChangeStatus


class RuntimeChangeManagement:
    """Runtime change governance abstraction."""

    def __init__(self) -> None:
        self._changes: list[RuntimeChangeRequest] = []

    def create(self, request: RuntimeChangeRequest) -> None:
        self._changes.append(request)

    def list_all(self) -> tuple[RuntimeChangeRequest, ...]:
        return tuple(self._changes)

    def approve(self, change_id: str) -> RuntimeChangeRequest | None:
        for item in self._changes:
            if item.change_id == change_id:
                updated = RuntimeChangeRequest(
                    change_id=item.change_id,
                    source_task=item.source_task,
                    target=item.target,
                    reason=item.reason,
                    risk_level=item.risk_level,
                    rollback_plan=item.rollback_plan,
                    status="APPROVED",
                )
                self._changes[self._changes.index(item)] = updated
                return updated
        return None
