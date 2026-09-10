from typing import Protocol

from platform.core.contracts.event_contract import EventContract
from platform.repository.dual_write.runtime_dual_write import (
    DualWriteEventRepository,
)

__all__ = ["EventRepository", "DualWriteEventRepository"]


class EventRepository(Protocol):
    """Event持久化抽象。

    Phase 1 使用Repository隔离存储实现。
    P9.26.5 起真实双写由 DualWriteEventRepository 承担（Legacy JSONL + MySQL）。
    """

    def save(self, event: EventContract) -> None:
        ...
