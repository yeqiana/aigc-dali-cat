from datetime import datetime

from platform.core.contracts.trace_contract import TraceContract
from platform.core.enums.trace_status import TraceStatus
from platform.repository.trace.mysql_trace_repository import MySqlTraceRepository


class FakeConnection:
    def __init__(self):
        self.records = []

    def insert_trace(self, data):
        self.records.append(data)


def test_mysql_trace_repository_save():
    connection = FakeConnection()
    repository = MySqlTraceRepository(connection)

    trace = TraceContract(
        trace_id="trace_001",
        span_id="span_001",
        operation="image_generation",
        status=TraceStatus.SUCCESS,
        started_at=datetime.utcnow(),
    )

    repository.save(trace)

    assert len(connection.records) == 1
    assert connection.records[0]["trace_id"] == "trace_001"
