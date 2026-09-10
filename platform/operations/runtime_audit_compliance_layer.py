from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


AuditStatus = Literal["RECORDED", "REVIEW_REQUIRED"]


@dataclass(frozen=True)
class AuditRecord:
    audit_id: str
    action_type: str
    actor: str
    target: str
    evidence_ref: str
    status: AuditStatus


class RuntimeAuditComplianceLayer:
    """Production runtime audit and compliance evidence layer.

    This module records governance evidence only. It does not authorize,
    execute, rollback, or mutate runtime changes.
    """

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def record(self, record: AuditRecord) -> None:
        self._records.append(record)

    def list_all(self) -> tuple[AuditRecord, ...]:
        return tuple(self._records)

    def review_required(self) -> tuple[AuditRecord, ...]:
        return tuple(
            item for item in self._records if item.status == "REVIEW_REQUIRED"
        )
