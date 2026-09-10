from datetime import datetime

from platform.repository.consistency import (
    ConsistencyStatus,
    RuntimeConsistencyChecker,
    RuntimeConsistencyScan,
    ScanPolicy,
)


class FakeLegacyEventStore:
    def __init__(self, records):
        self.records = records

    def read_all(self):
        return list(self.records)

    def read_by_id(self, event_id):
        for record in self.records:
            if record.get("event_id") == event_id:
                return record
        return None


class FakeMysqlEventRepository:
    def __init__(self, rows):
        self.rows = rows
        self.saved = []

    def get(self, event_id):
        for row in self.rows:
            if row.get("event_id") == event_id:
                return row
        return None

    def list_all(self):
        return list(self.rows)

    def save(self, event):
        self.saved.append(event)


def _legacy_event(event_id, event_type="TASK_STARTED", occurred_at="2026-09-10 12:34:56.789012", payload=None):
    return {
        "event_id": event_id,
        "event_type": event_type,
        "aggregate_type": "TASK",
        "aggregate_id": "t1",
        "occurred_at": occurred_at,
        "trace_id": None,
        "task_id": None,
        "payload": payload if payload is not None else {"a": 1},
        "metadata": {},
    }


def _mysql_event(event_id, event_type="TASK_STARTED", occurred_at=None, payload='{"a": 1}'):
    return {
        "event_id": event_id,
        "event_type": event_type,
        "aggregate_type": "TASK",
        "aggregate_id": "t1",
        "occurred_at": occurred_at or datetime(2026, 9, 10, 12, 34, 56, 789012),
        "trace_id": None,
        "task_id": None,
        "payload": payload,
        "metadata": "{}",
    }


def _checker(legacy_records, mysql_rows):
    return RuntimeConsistencyChecker(
        event_legacy=FakeLegacyEventStore(legacy_records),
        event_mysql=FakeMysqlEventRepository(mysql_rows),
    )


def test_compare_match():
    checker = _checker([_legacy_event("e1")], [_mysql_event("e1")])

    report = checker.compare_event("e1")

    assert report.status is ConsistencyStatus.MATCH
    assert report.ok
    assert report.payload_hash["payload"]["match"] is True


def test_compare_match_without_microseconds():
    checker = _checker(
        [_legacy_event("e1", occurred_at="2026-09-10 12:34:56")],
        [_mysql_event("e1", occurred_at=datetime(2026, 9, 10, 12, 34, 56))],
    )

    report = checker.compare_event("e1")

    assert report.status is ConsistencyStatus.MATCH


def test_compare_field_mismatch():
    checker = _checker([_legacy_event("e1")], [_mysql_event("e1", event_type="TASK_FAILED")])

    report = checker.compare_event("e1")

    assert report.status is ConsistencyStatus.MISMATCH
    assert report.reason == "field_diff"
    assert any(diff["field"] == "event_type" for diff in report.field_diffs)


def test_compare_payload_hash_mismatch():
    checker = _checker([_legacy_event("e1", payload={"a": 1})], [_mysql_event("e1", payload='{"a": 2}')])

    report = checker.compare_event("e1")

    assert report.status is ConsistencyStatus.MISMATCH
    assert report.payload_hash["payload"]["match"] is False


def test_compare_legacy_only_and_mysql_only():
    legacy_only = _checker([_legacy_event("e1")], []).compare_event("e1")
    mysql_only = _checker([], [_mysql_event("e2")]).compare_event("e2")

    assert legacy_only.status is ConsistencyStatus.MISSING
    assert legacy_only.reason == "legacy_only"
    assert mysql_only.status is ConsistencyStatus.MISSING
    assert mysql_only.reason == "mysql_only"


def test_scan_compensating_write_for_legacy_only():
    legacy = FakeLegacyEventStore([_legacy_event("e1")])
    mysql = FakeMysqlEventRepository([])
    checker = RuntimeConsistencyChecker(event_legacy=legacy, event_mysql=mysql)
    scan = RuntimeConsistencyScan(checker)

    result = scan.run(ScanPolicy(compensating_write=True))

    assert result["event"]["counts"]["legacy_only"] == 1
    assert result["event"]["compensated"] == ["e1"]
    assert len(mysql.saved) == 1


def test_scan_records_anomaly_and_repair_queue():
    legacy = FakeLegacyEventStore([_legacy_event("e1", event_type="TASK_STARTED")])
    mysql = FakeMysqlEventRepository([
        _mysql_event("e1", event_type="TASK_FAILED"),
        _mysql_event("e2"),
    ])
    checker = RuntimeConsistencyChecker(event_legacy=legacy, event_mysql=mysql)
    scan = RuntimeConsistencyScan(checker)

    result = scan.run()

    assert result["event"]["counts"]["mismatch"] == 1
    assert result["event"]["counts"]["mysql_only"] == 1
    assert result["event"]["anomalies"] == [{"entity_type": "event", "entity_id": "e2"}]
    assert result["event"]["repair_queue"][0]["entity_id"] == "e1"


def test_scan_merges_duplicates():
    legacy = FakeLegacyEventStore([_legacy_event("e1"), _legacy_event("e1")])
    mysql = FakeMysqlEventRepository([_mysql_event("e1")])
    checker = RuntimeConsistencyChecker(event_legacy=legacy, event_mysql=mysql)
    scan = RuntimeConsistencyScan(checker)

    result = scan.run()

    assert result["event"]["total_legacy"] == 1
    assert result["event"]["duplicates"] == ["e1"]


class StreamingMysqlEventRepository:
    """只提供 iter_all 的仓储，用于确认巡检走 keyset 流式读取。"""

    def __init__(self, rows):
        self.rows = rows
        self.streamed = False

    def iter_all(self, batch_size=500):
        self.streamed = True
        for row in self.rows:
            yield row

    def list_all(self):
        raise AssertionError("list_all 不应在有 iter_all 时被调用")


def test_scan_prefers_keyset_streaming():
    legacy = FakeLegacyEventStore([_legacy_event("e1")])
    mysql = StreamingMysqlEventRepository([_mysql_event("e1")])
    checker = RuntimeConsistencyChecker(event_legacy=legacy, event_mysql=mysql)

    result = RuntimeConsistencyScan(checker).run()

    assert mysql.streamed is True
    assert result["event"]["counts"]["match"] == 1


class FakeMysqlTraceRepository:
    def __init__(self, rows):
        self.rows = rows

    def get(self, trace_id, span_id):
        for row in self.rows:
            if row.get("trace_id") == trace_id and row.get("span_id") == span_id:
                return row
        return None

    def list_all(self):
        return list(self.rows)


def _real_trace_store(tmp_path):
    from platform.trace.jsonl_trace_store import JsonlTraceStore

    return JsonlTraceStore(str(tmp_path / "traces.jsonl"))


def _trace(trace_id, span_id, status, started_at, ended_at=None, duration_ms=None):
    from platform.core.contracts.trace_contract import TraceContract

    return TraceContract(
        trace_id=trace_id,
        span_id=span_id,
        operation="agent.execute",
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        duration_ms=duration_ms,
    )


def test_jsonl_trace_read_by_id_is_last_wins(tmp_path):
    from datetime import datetime

    from platform.core.enums.trace_status import TraceStatus

    store = _real_trace_store(tmp_path)
    started = datetime(2026, 9, 10, 12, 0, 0, 123456)
    store.append(_trace("t1", "s1", TraceStatus.RUNNING, started))
    store.append(
        _trace("t1", "s1", TraceStatus.SUCCESS, started, datetime(2026, 9, 10, 12, 0, 5, 654321), 5)
    )

    assert len(store.read_all()) == 2
    assert store.read_by_id("t1", "s1")["status"] == "SUCCESS"


def test_compare_trace_matches_after_running_to_success_overwrite(tmp_path):
    """回归：RUNNING -> SUCCESS 同主键覆盖后，单条比对不得报假 MISMATCH。"""
    from datetime import datetime

    from platform.core.enums.trace_status import TraceStatus

    store = _real_trace_store(tmp_path)
    started = datetime(2026, 9, 10, 12, 0, 0, 123456)
    ended = datetime(2026, 9, 10, 12, 0, 5, 654321)
    store.append(_trace("t1", "s1", TraceStatus.RUNNING, started))
    store.append(_trace("t1", "s1", TraceStatus.SUCCESS, started, ended, 5))

    checker = RuntimeConsistencyChecker(
        trace_legacy=store,
        trace_mysql=FakeMysqlTraceRepository([
            {
                "trace_id": "t1",
                "span_id": "s1",
                "operation": "agent.execute",
                "status": "SUCCESS",
                "started_at": started,
                "request_id": None,
                "episode_id": None,
                "task_id": None,
                "parent_span_id": None,
                "ended_at": ended,
                "duration_ms": 5,
                "inputs": "{}",
                "outputs": "{}",
                "error": None,
                "attributes": "{}",
            }
        ]),
    )

    report = checker.compare_trace("t1", "s1")

    assert report.status is ConsistencyStatus.MATCH
    assert report.field_diffs == []


def test_jsonl_event_read_by_id_is_last_wins(tmp_path):
    from platform.core.clock import utc_now
    from platform.core.contracts.event_contract import EventContract
    from platform.core.enums.entity_type import EntityType
    from platform.core.enums.event_type import EventType
    from platform.event.jsonl_event_store import JsonlEventStore

    store = JsonlEventStore(str(tmp_path / "events.jsonl"))
    occurred_at = utc_now()
    store.append(
        EventContract(
            event_id="e1",
            event_type=EventType.TASK_STARTED,
            aggregate_type=EntityType.TASK,
            aggregate_id="t1",
            occurred_at=occurred_at,
        )
    )
    store.append(
        EventContract(
            event_id="e1",
            event_type=EventType.TASK_COMPLETED,
            aggregate_type=EntityType.TASK,
            aggregate_id="t1",
            occurred_at=occurred_at,
        )
    )

    assert store.read_by_id("e1")["event_type"] == "TASK_COMPLETED"
    assert store.read_by_id("missing") is None


def test_jsonl_artifact_read_by_id_is_last_wins(tmp_path):
    from platform.artifact.jsonl_artifact_store import JsonlArtifactStore
    from platform.core.clock import utc_now
    from platform.core.contracts.artifact_contract import ArtifactContract
    from platform.core.enums.artifact_type import ArtifactType
    from platform.core.enums.entity_type import EntityType

    store = JsonlArtifactStore(str(tmp_path / "artifacts.jsonl"))
    base = dict(
        artifact_id="a1",
        artifact_type=ArtifactType.IMAGE,
        path="images/a.png",
        owner_type=EntityType.TASK,
        owner_id="t1",
        created_by="tester",
        created_at=utc_now(),
    )
    store.append(ArtifactContract(sha256="a" * 64, **base))
    store.append(ArtifactContract(sha256="b" * 64, **base))

    assert store.read_by_id("a1")["sha256"] == "b" * 64

