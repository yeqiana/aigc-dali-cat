from __future__ import annotations

import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import preimage_storage_preflight


def _mock_database(monkeypatch, names, tables):
    result = {"conn": None, "sql": []}
    class FakeConnection:
        def __init__(self, **kwargs):
            assert kwargs["database"] == "information_schema"
            result["conn"] = self
            self.closed = False
        def query_all(self, sql, params=None):
            result["sql"].append(sql)
            assert not any(word in sql.upper() for word in
                           ("INSERT ", "UPDATE ", "DELETE ", "CREATE ", "DROP ", "ALTER "))
            if sql == "SHOW DATABASES":
                return [{"Database": x} for x in names]
            return [{"TABLE_NAME": x} for x in tables]
        def close(self):
            self.closed = True
    monkeypatch.setattr(preimage_storage_preflight.storage_config,
                        "mysql_connection_kwargs", lambda override: dict(override))
    monkeypatch.setattr(preimage_storage_preflight, "MySqlConnection", FakeConnection)
    return result


def test_missing_v2_schema_fails_closed_on_case_only_match(monkeypatch):
    fake = _mock_database(monkeypatch, ["information_schema", "story_os_runtime"], [])
    report = preimage_storage_preflight.inspect()
    assert report["status"] == "V2_SCHEMA_MISSING"
    assert report["case_only_schema_present"] is True
    assert report["schema_check_passed"] is False
    assert fake["conn"].closed is True


def test_existing_schema_with_missing_tables_still_blocks(monkeypatch):
    fake = _mock_database(monkeypatch, ["STORY_OS_RUNTIME"], ["TB_SCHEMA_VERSION"])
    report = preimage_storage_preflight.inspect()
    assert report["status"] == "V2_TABLES_MISSING"
    assert "TB_RUNTIME_REVIEW_REQUEST" in report["missing_required_tables"]
    assert report["schema_check_passed"] is False
    assert fake["conn"].closed is True


def test_valid_v2_schema_is_read_only_ready(monkeypatch):
    fake = _mock_database(monkeypatch, ["STORY_OS_RUNTIME"],
                          preimage_storage_preflight.REQUIRED_TABLES)
    report = preimage_storage_preflight.inspect()
    assert report["status"] == "V2_SCHEMA_PRESENT_UNATTESTED"
    assert report["schema_check_passed"] is True
    assert report["read_only"] is True
    assert fake["conn"].closed is True
    assert report["production_authority_granted"] is False
    assert len(fake["sql"]) == 2


def test_connection_exception_fails_closed_without_credentials(monkeypatch):
    monkeypatch.setattr(preimage_storage_preflight.storage_config,
                        "mysql_connection_kwargs", lambda _x: {"database": "information_schema"})
    def broken(**kwargs):
        raise RuntimeError("bad credentials")
    monkeypatch.setattr(preimage_storage_preflight, "MySqlConnection", broken)
    report = preimage_storage_preflight.inspect()
    assert report["status"] == "V2_SCHEMA_PROBE_FAILED"
    assert report["error_type"] == "RuntimeError"
    assert "credentials" not in str(report)
    assert report["schema_check_passed"] is False
