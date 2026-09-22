from __future__ import annotations

import json

import pytest

from platform.repository.mysql import schema_v2
from platform.repository.mysql.mysql_latest_record_store import MySqlLatestRecordStore
from platform.repository.mysql.schema import (
    CREATE_PLATFORM_LATEST_RECORD_TABLE_SQL,
    apply_schema,
)
from platform.repository.platform_record_store_provider import build_platform_record_stores


class FakeConnection:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1

    def query_all(self, sql, params=None):
        self.executed.append((sql, params))
        return list(self.rows)


def test_mysql_latest_record_store_upserts_namespaced_json_snapshot():
    conn = FakeConnection()
    store = MySqlLatestRecordStore(conn, namespace="execution", key_field="execution_id")
    store.upsert({"execution_id": "exec-1", "status": "SUCCESS", "nested": {"ok": True}})

    sql, params = conn.executed[-1]
    assert "ON DUPLICATE KEY UPDATE" in sql
    assert params[0] == "execution"
    assert params[1] == "exec-1"
    assert json.loads(params[2])["nested"] == {"ok": True}


def test_mysql_latest_record_store_loads_and_validates_payload_key():
    conn = FakeConnection([
        {"record_key": "exp-1", "payload": json.dumps({"experience_id": "exp-1", "pattern": "stable"})}
    ])
    store = MySqlLatestRecordStore(conn, namespace="experience", key_field="experience_id")
    assert store.load_all()["exp-1"]["pattern"] == "stable"
    assert conn.executed[-1][1] == ("experience",)

    broken = MySqlLatestRecordStore(
        FakeConnection([{"record_key": "exp-1", "payload": {"experience_id": "exp-2"}}]),
        namespace="experience",
        key_field="experience_id",
    )
    with pytest.raises(ValueError, match="key mismatch"):
        broken.load_all()


def test_platform_record_store_provider_can_opt_into_mysql_without_touching_real_db():
    conn = FakeConnection()
    stores = build_platform_record_stores(mysql_connection=conn)
    assert isinstance(stores.execution, MySqlLatestRecordStore)
    assert isinstance(stores.experience, MySqlLatestRecordStore)
    stores.execution.upsert({"execution_id": "exec-provider"})
    stores.experience.upsert({"experience_id": "exp-provider"})
    assert [params[0] for _sql, params in conn.executed] == ["execution", "experience"]


def test_provider_rejects_ambiguous_jsonl_and_mysql_implicit_modes(tmp_path):
    with pytest.raises(ValueError, match="mutually exclusive"):
        build_platform_record_stores(tmp_path, mysql_connection=FakeConnection())


def test_schema_includes_shared_platform_latest_record_table():
    assert "platform_latest_record" in CREATE_PLATFORM_LATEST_RECORD_TABLE_SQL
    assert "PRIMARY KEY (namespace, record_key)" in CREATE_PLATFORM_LATEST_RECORD_TABLE_SQL
    conn = FakeConnection()
    steps = apply_schema(conn)
    assert steps[-1] == "create_platform_latest_record"
    assert len(conn.executed) == len(schema_v2.DDL_STEPS) + 1
