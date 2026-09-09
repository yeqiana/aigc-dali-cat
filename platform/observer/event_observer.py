from datetime import datetime
from uuid import uuid4
from typing import Any

from platform.core.contracts.event_contract import EventContract
from platform.core.enums.entity_type import EntityType
from platform.core.enums.event_type import EventType
from platform.repository.event_repository import EventRepository


class EventObserver:
    """Runtime事件观察器。

    只负责产生事实事件，不修改业务状态。
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
            occurred_at=datetime.utcnow(),
            trace_id=trace_id,
            task_id=task_id,
            payload=payload or {},
        )

        if self.repository:
            self.repository.save(event)

        return event
