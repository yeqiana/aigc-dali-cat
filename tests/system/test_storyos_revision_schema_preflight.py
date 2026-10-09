"""Hermetic read-only Revision schema audit; does not connect to MySQL."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import storyos_revision_schema_preflight as schema_audit


class ReadOnlyConnection:
    def __init__(self, *, database="STORY_OS_RUNTIME", missing=(), clause=None,
                 fail=False):
        self.database = database
        self.missing = set(missing)
        self.clause = clause if clause is not None else (
            "`STATUS` in ('PREPARING','CREATED','PREPARED',"
            "'VISUAL_LOCK_PENDING','READY','ACTIVE','RETIRED','FAILED')")
        self.calls = []
        self.fail = fail

    def query_one(self, sql, params=None):
        self.calls.append(sql)
        if self.fail:
            raise ConnectionError("redacted-db-token-must-never-appear")
        assert sql == "SELECT DATABASE() AS selected_database"
        return {"selected_database": self.database}

    def query_all(self, sql, params=None):
        self.calls.append(sql)
        assert "information_schema." in sql
        if "TABLES" in sql:
            return [{"TABLE_NAME": table} for table in schema_audit.REVISION_TABLES
                    if table not in self.missing]
        return [{"CHECK_CLAUSE": self.clause}] if self.clause else []

    def execute(self, *args):
        raise AssertionError("READONLY_PREFLIGHT_MUST_NOT_WRITE")


def test_current_schema_selects_only_and_reports_nonproduction_scope():
    conn = ReadOnlyConnection()
    result = schema_audit.audit_schema(conn)
    assert result["status"] == "SCHEMA_READONLY_VERIFIED"
    assert result["sql_writes"] == result["provider_calls"] == 0
    assert all(sql.startswith("SELECT ") for sql in conn.calls)


def test_missing_schema_tables_never_triggers_migration():
    conn = ReadOnlyConnection(missing=("TB_PRODUCTION_REVISION_HEAD",))
    result = schema_audit.audit_schema(conn)
    assert result["status"] == "BLOCKED"
    assert result["missing_tables"] == ["TB_PRODUCTION_REVISION_HEAD"]
    assert result["reason"] == "PRODUCTION_REVISION_SCHEMA_TABLES_MISSING"
    assert all(sql.startswith("SELECT ") for sql in conn.calls)


def test_old_lifecycle_requires_explicit_migration_not_automatic():
    conn = ReadOnlyConnection(clause="'PREPARING','ACTIVE','RETIRED'")
    result = schema_audit.audit_schema(conn)
    assert result["status"] == "BLOCKED"
    assert "READY" in result["missing_revision_states"]
    assert result["reason"] == "PRODUCTION_REVISION_SCHEMA_LIFECYCLE_MIGRATION_REQUIRED"


def test_connection_error_is_redacted_and_not_mistaken_for_legacy():
    result = schema_audit.audit_schema(ReadOnlyConnection(fail=True))
    assert result["status"] == "BLOCKED"
    assert result["reason"] == "PRODUCTION_REVISION_SCHEMA_QUERY_FAILED"
    assert "redacted-db-token-must-never-appear" not in str(result)


def test_wrong_db_is_blocked_before_any_schema_reads():
    conn = ReadOnlyConnection(database="MY_OTHER_DB")
    result = schema_audit.audit_schema(conn)
    assert result["status"] == "BLOCKED"
    assert result["reason"] == "PRODUCTION_REVISION_SCHEMA_WRONG_DATABASE"
    assert len(conn.calls) == 1
