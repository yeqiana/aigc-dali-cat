from __future__ import annotations

import pytest

from platform.repository.mysql import schema_v2


OLD_CHECK = "`STATUS` in ('PREPARING','ACTIVE','RETIRED')"
NEW_CHECK = "`STATUS` in ('PREPARING','CREATED','PREPARED','VISUAL_LOCK_PENDING','READY','ACTIVE','RETIRED','FAILED')"


class FakeConnection:
    def __init__(self, clause):
        self.clause = clause
        self.statements = []
        self.locked = True

    def query_one(self, sql, params):
        if "GET_LOCK" in sql:
            return {"ACQUIRED": 1 if self.locked else 0}
        if "RELEASE_LOCK" in sql:
            return {"RELEASED": 1}
        raise AssertionError(sql)

    def query_all(self, sql, params):
        if "information_schema.CHECK_CONSTRAINTS" in sql:
            return [{"CONSTRAINT_NAME": "CHECK_TB_PRODUCTION_REVISION_STATUS",
                     "CHECK_CLAUSE": self.clause}] if self.clause else []
        raise AssertionError(sql)

    def execute(self, sql):
        self.statements.append(sql)
        self.clause = NEW_CHECK
        return 0


def test_revision_lifecycle_migration_uses_atomic_alter_and_preserves_unknown_old_statuses():
    connection = FakeConnection(OLD_CHECK)
    result = schema_v2.migrate_production_revision_lifecycle(
        connection, expected_database=schema_v2.DATABASE_NAME)
    assert result == {"status": "MIGRATED", "changed": True,
                      "constraint": "CHECK_TB_PRODUCTION_REVISION_STATUS"}
    assert len(connection.statements) == 1
    assert "DROP CHECK CHECK_TB_PRODUCTION_REVISION_STATUS, ADD CONSTRAINT" in connection.statements[0]
    assert "'OUTCOME_UNKNOWN'" not in connection.statements[0]


def test_revision_lifecycle_migration_is_idempotent():
    connection = FakeConnection(NEW_CHECK)
    result = schema_v2.migrate_production_revision_lifecycle(
        connection, expected_database=schema_v2.DATABASE_NAME)
    assert result["status"] == "CURRENT"
    assert result["changed"] is False
    assert connection.statements == []


def test_revision_lifecycle_migration_refuses_wrong_database_or_missing_lock():
    with pytest.raises(ValueError, match="DATABASE_MISMATCH"):
        schema_v2.migrate_production_revision_lifecycle(
            FakeConnection(OLD_CHECK), expected_database="some_other_database")
    connection = FakeConnection(OLD_CHECK)
    connection.locked = False
    with pytest.raises(RuntimeError, match="LOCK_UNAVAILABLE"):
        schema_v2.migrate_production_revision_lifecycle(
            connection, expected_database=schema_v2.DATABASE_NAME)
    assert connection.statements == []
