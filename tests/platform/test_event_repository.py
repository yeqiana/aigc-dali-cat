from datetime import datetime

from platform.core.contracts.event_contract import EventContract
from platform.core.enums.entity_type import EntityType
from platform.core.enums.event_type import EventType
from platform.repository.event_repository import DualWriteEventRepository


class MemoryEventStore:
    def __init__(self):
        self.events = []

    def append(self, event):
        self.events.append(event)


def test_event_repository_save():
    store = MemoryEventStore()
    repo = DualWriteEventRepository(store)

    event = EventContract(
        event_id="evt_test",
        event_type=EventType.TASK_STARTED,
        aggregate_type=EntityType.TASK,
        aggregate_id="task001",
        occurred_at=datetime.utcnow(),
    )

    repo.save(event)

    assert len(store.events) == 1
    assert store.events[0].event_id == "evt_test"
