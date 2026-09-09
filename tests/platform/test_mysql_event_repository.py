from datetime import datetime

from platform.core.contracts.event_contract import EventContract
from platform.core.enums.entity_type import EntityType
from platform.core.enums.event_type import EventType
from platform.repository.mysql.mysql_event_repository import MySqlEventRepository


class FakeConnection:
    def __init__(self):
        self.records = []

    def insert_event(self, record):
        self.records.append(record)


def test_mysql_event_repository_save():
    connection = FakeConnection()
    repository = MySqlEventRepository(connection)

    event = EventContract(
        event_id="evt_test",
        event_type=EventType.TASK_STARTED,
        aggregate_type=EntityType.TASK,
        aggregate_id="task_test",
        occurred_at=datetime.utcnow(),
    )

    repository.save(event)

    assert len(connection.records) == 1
    assert connection.records[0]["event_id"] == "evt_test"
