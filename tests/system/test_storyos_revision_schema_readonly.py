"""SELECT-only production Revision Schema admission tests."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "storyos_revision_schema_readonly.py"
spec = importlib.util.spec_from_file_location("storyos_revision_schema_readonly", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeDB:
    def __init__(self, *, db=module.DATABASE_NAME, case_mode=0,
                 absent=(), states=module.REQUIRED_STATES, fail=False):
        self.db = db
        self.case_mode = case_mode
        self.absent = set(absent)
        self.states = states
        self.fail = fail
        self.queries = []

    def query_one(self, sql, params=None):
        self.queries.append(sql)
        assert sql.strip().upper().startswith("SELECT")
        if self.fail:
            raise ConnectionError("TEST_ONLY no credentials")
        return {"db": self.db, "case_mode": self.case_mode, "version": "8.0.test"}

    def query_all(self, sql, params=None):
        self.queries.append(sql)
        assert sql.strip().upper().startswith("SELECT")
        if "information_schema.TABLES" in sql:
            return [{"TABLE_NAME": name} for name in module.REVISION_TABLES + module.DEPENDENCIES
                    if name not in self.absent]
        if "information_schema.CHECK_CONSTRAINTS" in sql:
            return [{"CHECK_CLAUSE": "STATUS IN (" +
                     ",".join("'" + s + "'" for s in self.states) + ")"}]
        raise AssertionError("unexpected schema read")


def test_complete_schema_is_not_a_production_activation():
    c = FakeDB()
    report = module.inspect_revision_schema(c)
    assert report["status"] == "READY_FOR_FURTHER_ADMISSION"
    assert not report["migration_performed"]
    assert not report["production_activation_performed"]
    assert len(c.queries) == 3
    assert all(query.upper().startswith("SELECT") for query in c.queries)


def test_missing_revision_tables_fail_closed():
    c = FakeDB(absent=module.REVISION_TABLES)
    r = module.inspect_revision_schema(c)
    assert r["status"] == "BLOCKED"
    assert all(v is False for v in r["revision_tables"].values())
    assert r["lifecycle_constraint_ready"] is False


def test_dependency_absence_blocks_even_when_revision_tables_exist():
    r = module.inspect_revision_schema(FakeDB(absent=("TB_REVIEW_RECORD",)))
    assert r["status"] == "BLOCKED"


def test_missing_new_status_in_check_blocks_migration_readiness():
    r = module.inspect_revision_schema(FakeDB(states=("PREPARING", "ACTIVE", "RETIRED")))
    assert r["status"] == "BLOCKED"
    assert r["lifecycle_constraint_ready"] is False


def test_wrong_schema_or_case_mode_never_queries_other_database_tables():
    for db, case_mode in (("story_os_runtime", 0), (module.DATABASE_NAME, 1)):
        c = FakeDB(db=db, case_mode=case_mode)
        r = module.inspect_revision_schema(c)
        assert r["status"] == "BLOCKED"
        assert r["reason"] == "DATABASE_IDENTITY_OR_CASE_MODE_MISMATCH"
        assert len(c.queries) == 1


def test_mysql_8_information_schema_escaped_quotes_are_recognized():
    class EscapedCheck(FakeDB):
        def query_all(self, sql, params=None):
            if "information_schema.CHECK_CONSTRAINTS" in sql:
                self.queries.append(sql)
                return [{"CHECK_CLAUSE": "(`STATUS` in (" +
                         ",".join("_utf8mb4\\\\'" + status + "\\\\'"
                                  for status in module.REQUIRED_STATES) + "))"}]
            return super().query_all(sql, params)

    db = EscapedCheck()
    result = module.inspect_revision_schema(db)
    assert result["lifecycle_constraint_ready"]
    assert result["status"] == "READY_FOR_FURTHER_ADMISSION"
