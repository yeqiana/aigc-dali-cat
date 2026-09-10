from typing import Any
from uuid import uuid4

from platform.core.clock import utc_now
from platform.core.contracts.event_contract import EventContract
from platform.core.enums.entity_type import EntityType
from platform.core.enums.event_type import EventType
from platform.repository.event_repository import EventRepository


class EventObserver:
    """Runtime事件观察器。

    只负责产生事实事件，不修改业务状态。
    P9.27 起 record() 会把事件交给注入的 repository（JSONL / MySQL / DualWrite）。
    """

    def __init__(self, repository: EventRepository | None = None):
        self.repository = repository

    def record(
        self,
        event_type: EventType,
        aggregate_type: EntityType,
        aggregate_id: str,
        payload: dict[str, Any] | None = None,
        trace_id: str | None = None,
        task_id: str | None = None,
    ) -> EventContract:
        event = EventContract(
            event_id=f"evt_{uuid4().hex}",
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            occurred_at=utc_now(),
            trace_id=trace_id,
            task_id=task_id,
            payload=payload or {},
        )
        self.save(event)
        return event

    def save(self, event: EventContract) -> None:
        """持久化已经构造好的事件契约。

        没有注入 repository 时只做观察，不落库（保持 Phase 0 行为）。
        """
        if self.repository:
            self.repository.save(event)
