from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "storyos_mysql_case_compat_copy.py"


def _module():
    spec = importlib.util.spec_from_file_location("storyos_casecopy_test_target", SCRIPT)
    target = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(target)
    return target


def test_source_schema_is_immutable_and_target_is_distinct():
    copy = _module()
    assert copy.SOURCE == "story_os_runtime"
    assert copy.TARGET == "STORY_OS_RUNTIME"
    assert copy.SOURCE != copy.TARGET
    assert copy.BACKUP.name.endswith(".sql.gz")


def test_all_v2_tables_have_explicit_column_mappings():
    from platform.repository.mysql.schema_v2 import DDL_STEPS
    copy = _module()
    mapping = copy.definitions(DDL_STEPS)
    assert len(mapping) == 27
    assert len({row[0] for row in mapping}) == 27
    assert all(columns for name, columns, ddl in mapping)
    assert all("CREATE TABLE IF NOT EXISTS" in ddl for _, _, ddl in mapping)
    for name in ("TB_EVENT_LOG", "TB_TRACE_SPAN", "TB_ARTIFACT_INDEX"):
        assert name in {row[0] for row in mapping}


def test_casecopy_rejects_unsafe_sql_identifiers():
    copy = _module()
    for name in ("bad.name", "name;DROP TABLE", "space name", ""):
        with pytest.raises(ValueError, match="UNSAFE_IDENTIFIER"):
            copy.quote(name)
    assert copy.quote("TB_EPISODE").strip(chr(96)) == "TB_EPISODE"


def test_verify_casecopy_fails_closed_on_digest_mismatch(monkeypatch):
    copy = _module()
    defs = [("TB_EPISODE", ["EPISODE_ID"], "CREATE TABLE")]
    monkeypatch.setattr(copy, "rows", lambda *_a, **_k: (
        [{"Database": copy.SOURCE}, {"Database": copy.TARGET}]
        if _a[1] == "SHOW DATABASES"
        else [{"n": 0}]
    ))
    monkeypatch.setattr(copy, "names", lambda _conn, schema: (
        {"TB_EPISODE"} if schema == copy.TARGET
        else {"tb_episode", "platform_latest_record"}
    ))
    monkeypatch.setattr(copy, "columns", lambda *_a: ["EPISODE_ID"])
    monkeypatch.setattr(copy, "fingerprint", lambda _conn, schema, *_a: (
        (1, "source") if schema == copy.SOURCE else (1, "target")
    ))
    with pytest.raises(RuntimeError, match="SOURCE_TARGET_DIGEST_MISMATCH"):
        copy.verify_casecopy(object(), defs)


def test_verify_casecopy_reports_equal_hashes_without_writes(monkeypatch):
    copy = _module()
    defs = [("TB_EPISODE", ["EPISODE_ID"], "CREATE TABLE")]
    monkeypatch.setattr(copy, "rows", lambda *_a, **_k: (
        [{"Database": copy.SOURCE}, {"Database": copy.TARGET}]
        if _a[1] == "SHOW DATABASES"
        else [{"n": 0}]
    ))
    monkeypatch.setattr(copy, "names", lambda _conn, schema: (
        {"TB_EPISODE"} if schema == copy.TARGET
        else {"tb_episode", "platform_latest_record"}
    ))
    monkeypatch.setattr(copy, "columns", lambda *_a: ["EPISODE_ID"])
    monkeypatch.setattr(copy, "fingerprint", lambda *_a: (1, "digest"))
    out = copy.verify_casecopy(object(), defs)
    assert out == {
        "status": "SOURCE_TARGET_VERIFIED",
        "tables_verified": 1,
        "total_rows": 1,
        "source_target_sha256_match": True,
        "authorized_shadow_supersessions": 0,
        "read_only": True,
        "runtime_env_unchanged": True,
    }
