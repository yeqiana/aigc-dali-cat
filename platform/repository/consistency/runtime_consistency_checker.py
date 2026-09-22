"""P9.26.6 Runtime Data Consistency Verification。

校验 Legacy(JSONL) 与 MySQL 双写数据一致性：
    - ID 一致性
    - 字段一致性
    - 时间戳合理性
    - JSON payload / 元数据 hash 一致性

单条结果：MATCH / MISMATCH / MISSING。
全量巡检：读取 Legacy -> 读取 MySQL -> Diff -> 生成 Evidence。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from platform.artifact.jsonl_artifact_store import JsonlArtifactStore
from platform.core.contracts.artifact_contract import ArtifactContract
from platform.core.contracts.event_contract import EventContract
from platform.core.contracts.trace_contract import TraceContract
from platform.core.enums.artifact_type import ArtifactType
from platform.core.enums.entity_type import EntityType
from platform.core.enums.event_type import EventType
from platform.core.enums.trace_status import TraceStatus
from platform.event.jsonl_event_store import JsonlEventStore
from platform.repository.artifact.mysql_artifact_repository import MySqlArtifactRepository
from platform.repository.mysql.mysql_event_repository import MySqlEventRepository
from platform.repository.trace.mysql_trace_repository import MySqlTraceRepository
from platform.trace.jsonl_trace_store import JsonlTraceStore


class ConsistencyStatus(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    MISSING = "MISSING"


EVENT_SCALAR_FIELDS = (
    "event_id", "event_type", "aggregate_type", "aggregate_id",
    "occurred_at", "trace_id", "task_id",
)
EVENT_JSON_FIELDS = ("payload", "metadata")

TRACE_SCALAR_FIELDS = (
    "trace_id", "span_id", "operation", "status", "started_at",
    "request_id", "episode_id", "task_id", "parent_span_id",
    "ended_at", "duration_ms", "error",
)
TRACE_JSON_FIELDS = ("inputs", "outputs", "attributes")

ARTIFACT_SCALAR_FIELDS = (
    "artifact_id", "artifact_type", "path", "sha256", "owner_type",
    "owner_id", "created_by", "created_at", "trace_id", "task_id",
)
ARTIFACT_JSON_FIELDS = ("metadata",)

# 时间字段统一按“墙钟时间”归一化：
# Legacy(JSONL) 用 default=str 落盘，MySQL 侧是 datetime 对象且 pymysql 写入时不带时区，
# 因此两侧只比较墙钟值，避免 +00:00 后缀造成假 MISMATCH。
DATETIME_FIELDS = frozenset({"occurred_at", "started_at", "ended_at", "created_at"})


def _canonical_json(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return '""'
        try:
            value = json.loads(text)
        except (ValueError, TypeError):
            return json.dumps(text, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _norm_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None).strftime("%Y-%m-%dT%H:%M:%S.%f")
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text).replace(tzinfo=None).strftime(
                "%Y-%m-%dT%H:%M:%S.%f"
            )
        except ValueError:
            return text
    return str(value)


def _norm_scalar(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return _norm_datetime(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, bool):
        return value
    return str(value)


def _parse_dt(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _event_from_record(record) -> EventContract:
    return EventContract(
        event_id=record["event_id"],
        event_type=EventType(record["event_type"]),
        aggregate_type=EntityType(record["aggregate_type"]),
        aggregate_id=record["aggregate_id"],
        occurred_at=_parse_dt(record["occurred_at"]),
        trace_id=record.get("trace_id"),
        task_id=record.get("task_id"),
        payload=record.get("payload") or {},
        metadata=record.get("metadata") or {},
    )


def _trace_from_record(record) -> TraceContract:
    ended_at = record.get("ended_at")
    return TraceContract(
        trace_id=record["trace_id"],
        span_id=record["span_id"],
        operation=record["operation"],
        status=TraceStatus(record["status"]),
        started_at=_parse_dt(record["started_at"]),
        request_id=record.get("request_id"),
        episode_id=record.get("episode_id"),
        task_id=record.get("task_id"),
        parent_span_id=record.get("parent_span_id"),
        ended_at=_parse_dt(ended_at) if ended_at else None,
        duration_ms=record.get("duration_ms"),
        inputs=record.get("inputs") or {},
        outputs=record.get("outputs") or {},
        error=record.get("error"),
        attributes=record.get("attributes") or {},
    )


def _artifact_from_record(record) -> ArtifactContract:
    return ArtifactContract(
        artifact_id=record["artifact_id"],
        artifact_type=ArtifactType(record["artifact_type"]),
        path=record["path"],
        sha256=record["sha256"],
        owner_type=EntityType(record["owner_type"]),
        owner_id=record["owner_id"],
        created_by=record["created_by"],
        created_at=_parse_dt(record["created_at"]),
        trace_id=record.get("trace_id"),
        task_id=record.get("task_id"),
        metadata=record.get("metadata") or {},
    )


@dataclass
class ConsistencyReport:
    entity_type: str
    entity_id: str
    status: ConsistencyStatus
    reason: str
    field_diffs: list = field(default_factory=list)
    payload_hash: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status is ConsistencyStatus.MATCH


class RuntimeConsistencyChecker:
    """按主键比对 Legacy 与 MySQL 单条数据。"""

    def __init__(
        self,
        event_legacy: JsonlEventStore | None = None,
        event_mysql: MySqlEventRepository | None = None,
        trace_legacy: JsonlTraceStore | None = None,
        trace_mysql: MySqlTraceRepository | None = None,
        artifact_legacy: JsonlArtifactStore | None = None,
        artifact_mysql: MySqlArtifactRepository | None = None,
    ) -> None:
        self.event_legacy = event_legacy
        self.event_mysql = event_mysql
        self.trace_legacy = trace_legacy
        self.trace_mysql = trace_mysql
        self.artifact_legacy = artifact_legacy
        self.artifact_mysql = artifact_mysql

    def compare_event(self, event_id: str) -> ConsistencyReport:
        legacy = self.event_legacy.read_by_id(event_id) if self.event_legacy else None
        mysql = self.event_mysql.get(event_id) if self.event_mysql else None
        return self._compare("event", event_id, legacy, mysql, EVENT_SCALAR_FIELDS, EVENT_JSON_FIELDS)

    def compare_trace(self, trace_id: str, span_id: str) -> ConsistencyReport:
        legacy = self.trace_legacy.read_by_id(trace_id, span_id) if self.trace_legacy else None
        mysql = self.trace_mysql.get(trace_id, span_id) if self.trace_mysql else None
        eid = trace_id + "/" + span_id
        return self._compare("trace", eid, legacy, mysql, TRACE_SCALAR_FIELDS, TRACE_JSON_FIELDS)

    def compare_artifact(self, artifact_id: str) -> ConsistencyReport:
        legacy = self.artifact_legacy.read_by_id(artifact_id) if self.artifact_legacy else None
        mysql = self.artifact_mysql.get(artifact_id) if self.artifact_mysql else None
        return self._compare("artifact", artifact_id, legacy, mysql, ARTIFACT_SCALAR_FIELDS, ARTIFACT_JSON_FIELDS)

    def _compare(self, entity_type, entity_id, legacy, mysql, scalar_fields, json_fields) -> ConsistencyReport:
        if legacy is None and mysql is None:
            return ConsistencyReport(entity_type, entity_id, ConsistencyStatus.MISSING, "both_missing")
        if legacy is not None and mysql is None:
            return ConsistencyReport(entity_type, entity_id, ConsistencyStatus.MISSING, "legacy_only")
        if legacy is None and mysql is not None:
            return ConsistencyReport(entity_type, entity_id, ConsistencyStatus.MISSING, "mysql_only")

        diffs = []
        for name in scalar_fields:
            normalize = _norm_datetime if name in DATETIME_FIELDS else _norm_scalar
            lv = normalize(legacy.get(name))
            mv = normalize(mysql.get(name))
            if lv != mv:
                diffs.append({"field": name, "legacy": lv, "mysql": mv})

        payload_hash = {}
        for name in json_fields:
            lh = _hash(legacy.get(name))
            mh = _hash(mysql.get(name))
            payload_hash[name] = {"legacy": lh, "mysql": mh, "match": lh == mh}
            if lh != mh:
                diffs.append({"field": name, "legacy_hash": lh, "mysql_hash": mh})

        if diffs:
            return ConsistencyReport(entity_type, entity_id, ConsistencyStatus.MISMATCH, "field_diff", diffs, payload_hash)
        return ConsistencyReport(entity_type, entity_id, ConsistencyStatus.MATCH, "ok", [], payload_hash)


@dataclass
class ScanPolicy:
    compensating_write: bool = False
    record_anomalies: bool = True
    repair_queue: bool = True
    merge_duplicates: bool = True


def _collect(records, key_fn):
    seen = {}
    order = []
    duplicates = []
    for record in records:
        key = key_fn(record)
        if key in seen:
            duplicates.append(key)
        else:
            order.append(key)
        seen[key] = record
    return seen, order, duplicates


def _eid(key) -> str:
    if isinstance(key, tuple):
        return "/".join(str(part) for part in key)
    return str(key)


def _mysql_records(repository):
    """优先用 keyset 分页流式读取（P9.27），无该能力时退回全量读取。"""
    if repository is None:
        return []
    iterator = getattr(repository, "iter_all", None)
    if callable(iterator):
        return iterator()
    return repository.list_all()


class RuntimeConsistencyScan:
    """Legacy vs MySQL 全量巡检，按策略处理异常。"""

    def __init__(self, checker: RuntimeConsistencyChecker) -> None:
        self.checker = checker

    def run(self, policy: ScanPolicy | None = None) -> dict:
        policy = policy or ScanPolicy()
        return {
            "event": self._scan_events(policy),
            "trace": self._scan_traces(policy),
            "artifact": self._scan_artifacts(policy),
        }

    def _scan_events(self, policy):
        legacy_records = self.checker.event_legacy.read_all() if self.checker.event_legacy else []
        mysql_records = _mysql_records(self.checker.event_mysql)
        legacy_map, order, duplicates = _collect(legacy_records, lambda r: r.get("event_id"))
        mysql_map = {r.get("event_id"): r for r in mysql_records}
        compensate = None
        if self.checker.event_mysql is not None:
            compensate = lambda rec: self.checker.event_mysql.save(_event_from_record(rec))
        return self._diff("event", legacy_map, mysql_map, policy, EVENT_SCALAR_FIELDS, EVENT_JSON_FIELDS, compensate, duplicates)

    def _scan_traces(self, policy):
        legacy_records = self.checker.trace_legacy.read_all() if self.checker.trace_legacy else []
        mysql_records = _mysql_records(self.checker.trace_mysql)
        key_fn = lambda r: (r.get("trace_id"), r.get("span_id"))
        legacy_map, order, duplicates = _collect(legacy_records, key_fn)
        mysql_map = {key_fn(r): r for r in mysql_records}
        compensate = None
        if self.checker.trace_mysql is not None:
            compensate = lambda rec: self.checker.trace_mysql.save(_trace_from_record(rec))
        return self._diff("trace", legacy_map, mysql_map, policy, TRACE_SCALAR_FIELDS, TRACE_JSON_FIELDS, compensate, duplicates)

    def _scan_artifacts(self, policy):
        legacy_records = self.checker.artifact_legacy.read_all() if self.checker.artifact_legacy else []
        mysql_records = _mysql_records(self.checker.artifact_mysql)
        legacy_map, order, duplicates = _collect(legacy_records, lambda r: r.get("artifact_id"))
        mysql_map = {r.get("artifact_id"): r for r in mysql_records}
        compensate = None
        if self.checker.artifact_mysql is not None:
            compensate = lambda rec: self.checker.artifact_mysql.save(_artifact_from_record(rec))
        return self._diff("artifact", legacy_map, mysql_map, policy, ARTIFACT_SCALAR_FIELDS, ARTIFACT_JSON_FIELDS, compensate, duplicates)

    def _diff(self, entity_type, legacy_map, mysql_map, policy, scalar_fields, json_fields, compensate, duplicates):
        keys = list(dict.fromkeys(list(legacy_map.keys()) + list(mysql_map.keys())))
        counts = {"match": 0, "mismatch": 0, "legacy_only": 0, "mysql_only": 0, "both_missing": 0}
        records = []
        compensated = []
        anomalies = []
        repair_queue = []
        for key in keys:
            entity_id = _eid(key)
            report = self.checker._compare(
                entity_type, entity_id,
                legacy_map.get(key), mysql_map.get(key),
                scalar_fields, json_fields,
            )
            records.append(report)
            if report.status is ConsistencyStatus.MATCH:
                counts["match"] += 1
            elif report.status is ConsistencyStatus.MISMATCH:
                counts["mismatch"] += 1
                if policy.repair_queue:
                    repair_queue.append({
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "diffs": report.field_diffs,
                    })
            else:
                if report.reason == "legacy_only":
                    counts["legacy_only"] += 1
                    if policy.compensating_write and compensate is not None:
                        compensate(legacy_map[key])
                        compensated.append(entity_id)
                elif report.reason == "mysql_only":
                    counts["mysql_only"] += 1
                    if policy.record_anomalies:
                        anomalies.append({"entity_type": entity_type, "entity_id": entity_id})
                else:
                    counts["both_missing"] += 1
        return {
            "counts": counts,
            "total_legacy": len(legacy_map),
            "total_mysql": len(mysql_map),
            "duplicates": [_eid(d) for d in duplicates] if policy.merge_duplicates else [],
            "records": records,
            "compensated": compensated,
            "anomalies": anomalies,
            "repair_queue": repair_queue,
        }
