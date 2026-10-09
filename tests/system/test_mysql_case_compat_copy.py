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
