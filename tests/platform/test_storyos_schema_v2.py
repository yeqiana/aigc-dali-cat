from platform.repository.mysql import schema_v2


class FakeConnection:
    def __init__(self):
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1


def test_v2_database_and_tables_follow_storyos_database_standard():
    assert schema_v2.DATABASE_NAME == "STORY_OS_RUNTIME"
    assert "utf8mb4_0900_ai_ci" in schema_v2.CREATE_DATABASE_SQL
    assert len(schema_v2.DDL_STEPS) >= 20
    for _step, sql in schema_v2.DDL_STEPS:
        assert "CREATE TABLE IF NOT EXISTS TB_" in sql
        assert "ENGINE=InnoDB" in sql
        assert "DEFAULT CHARSET=utf8mb4" in sql
        assert "COLLATE=utf8mb4_0900_ai_ci" in sql
        assert " COMMENT='" in sql
        assert "utf8mb4_unicode_ci" not in sql


def test_v2_schema_contains_high_volume_json_targets():
    ddl = "\n".join(sql for _step, sql in schema_v2.DDL_STEPS)
    for table in (
        "TB_FRAME_CONTRACT",
        "TB_FRAME_REVIEW",
        "TB_PROVIDER_RECEIPT",
        "TB_HOST_REQUEST",
        "TB_PRODUCTION_ATTEMPT",
        "TB_METRIC_SNAPSHOT",
        "TB_PROMPT_PACKAGE",
    ):
        assert table in ddl


def test_apply_schema_is_explicit_and_ordered():
    connection = FakeConnection()
    steps = schema_v2.apply_schema(connection)
    assert steps == [name for name, _sql in schema_v2.DDL_STEPS]
    assert len(connection.executed) == len(schema_v2.DDL_STEPS)

