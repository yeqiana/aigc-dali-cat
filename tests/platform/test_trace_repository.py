from datetime import datetime

from platform.core.contracts.trace_contract import TraceContract
from platform.core.enums.trace_status import TraceStatus
from platform.repository.trace.mysql_trace_repository import MySqlTraceRepository


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


def _trace():
    return TraceContract(
        trace_id="trace_001",
        span_id="span_001",
        operation="image_generation",
        status=TraceStatus.SUCCESS,
        started_at=datetime.utcnow(),
        inputs={"model": "gpt-image-2"},
    )


def test_mysql_trace_repository_save():
    connection = FakeConnection()
    repository = MySqlTraceRepository(connection)

    repository.save(_trace())

    assert len(connection.executed) == 1
    sql, params = connection.executed[0]
    assert "INSERT INTO TB_TRACE_SPAN" in sql
    assert params[0] == "span_001"
    assert params[1] == "trace_001"
    assert params[8] == "SUCCESS"


def test_mysql_trace_repository_get():
    connection = FakeConnection()
    connection.one = {
        "TRACE_ID": "trace_001",
        "SPAN_ID": "span_001",
        "START_TIME": datetime(2026, 1, 1, 0, 0, 0),
        "END_TIME": datetime(2026, 1, 1, 0, 0, 1),
        "ELAPSED_MS": 1000,
        "ERROR_TEXT": None,
    }
    repository = MySqlTraceRepository(connection)

    row = repository.get("trace_001", "span_001")

    assert row is not None
    assert row["trace_id"] == "trace_001"
    assert row["started_at"] == datetime(2026, 1, 1, 0, 0, 0)
    assert row["ended_at"] == datetime(2026, 1, 1, 0, 0, 1)
    assert row["duration_ms"] == 1000
    assert row["error"] is None
    assert connection.queried[-1][1] == ("trace_001", "span_001")
