from datetime import datetime

from platform.core.contracts.event_contract import EventContract
from platform.core.enums.entity_type import EntityType
from platform.core.enums.event_type import EventType
from platform.repository.mysql.mysql_event_repository import MySqlEventRepository


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.queried = []
        self.one = None

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1

    def query_one(self, sql, params=None):
        self.queried.append((sql, params))
        return self.one

    def query_all(self, sql, params=None):
        return []


def _event():
    return EventContract(
        event_id="evt_test",
        event_type=EventType.TASK_STARTED,
        aggregate_type=EntityType.TASK,
        aggregate_id="task_test",
        occurred_at=datetime.utcnow(),
        payload={"n": 1},
        metadata={"src": "unit"},
    )


def test_mysql_event_repository_save():
    connection = FakeConnection()
    repository = MySqlEventRepository(connection)

    repository.save(_event())

    assert len(connection.executed) == 1
    sql, params = connection.executed[0]
    assert "INSERT INTO event_log" in sql
    assert params[0] == "evt_test"
    assert params[1] == "TASK_STARTED"
    assert params[2] == "TASK"


def test_mysql_event_repository_get():
    connection = FakeConnection()
    connection.one = {"event_id": "evt_test", "event_type": "TASK_STARTED"}
    repository = MySqlEventRepository(connection)

    row = repository.get("evt_test")

    assert row is not None
    assert row["event_id"] == "evt_test"
    assert connection.queried[-1][1] == ("evt_test",)


def test_mysql_event_repository_requires_connection():
    repository = MySqlEventRepository()
    try:
        repository.save(_event())
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError")
