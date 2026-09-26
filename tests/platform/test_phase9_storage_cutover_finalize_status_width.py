from scripts import phase9_storage_cutover_finalize as cutover


class FakeConnection:
    def __init__(self, status_length=32):
        self.status_length = status_length
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1

    def query_all(self, sql, params=None):
        if "CHARACTER_MAXIMUM_LENGTH" in sql:
            if params == ("TB_PRODUCTION_FRAME", "STATUS"):
                return [{"CHARACTER_MAXIMUM_LENGTH": self.status_length}]
            return []
        if "information_schema.COLUMNS" in sql:
            table = params[0] if params else ""
            existing = {
                "TB_EVENT_LOG": ["TRACE_ID", "TASK_ID"],
                "TB_TRACE_SPAN": ["REQUEST_ID", "TASK_ID", "ERROR_TEXT"],
                "TB_ARTIFACT_INDEX": ["CREATED_BY", "TRACE_ID", "TASK_ID", "METADATA_BLOB", "METADATA_SHA256"],
            }
            return [{"COLUMN_NAME": name} for name in existing.get(table, [])]
        if "information_schema.STATISTICS" in sql:
            return [{"INDEX_NAME": "INDEX_TB_TRACE_SPAN_START_TIME"}]
        return []


def test_upgrade_expands_production_frame_status_when_legacy_width_is_32():
    conn = FakeConnection(32)
    changed = cutover.upgrade_runtime_tables(conn)
    assert "TB_PRODUCTION_FRAME.STATUS:VARCHAR(64)" in changed
    assert any(
        "ALTER TABLE TB_PRODUCTION_FRAME MODIFY COLUMN STATUS VARCHAR(64)" in sql
        for sql, _params in conn.executed
    )


def test_upgrade_does_not_alter_production_frame_status_when_already_64():
    conn = FakeConnection(64)
    changed = cutover.upgrade_runtime_tables(conn)
    assert "TB_PRODUCTION_FRAME.STATUS:VARCHAR(64)" not in changed
    assert not any(
        "ALTER TABLE TB_PRODUCTION_FRAME MODIFY COLUMN STATUS" in sql
        for sql, _params in conn.executed
    )
