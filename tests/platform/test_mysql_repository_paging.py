from platform.repository.artifact.mysql_artifact_repository import MySqlArtifactRepository
from platform.repository.mysql.mysql_event_repository import MySqlEventRepository
from platform.repository.trace.mysql_trace_repository import MySqlTraceRepository


class PagedConnection:
    """按 keyset 语义返回分页结果的假连接。"""

    def __init__(self, rows, key_columns):
        self.rows = rows
        self.key_columns = key_columns
        self.queries = []

    def query_all(self, sql, params=None):
        self.queries.append((sql, params))
        last = tuple(params[:-1])
        limit = params[-1]
        remaining = [
            row
            for row in self.rows
            if tuple(row[column] for column in self.key_columns) > last
        ]
        remaining.sort(key=lambda row: tuple(row[column] for column in self.key_columns))
        return remaining[:limit]


def test_event_iter_all_pages_by_keyset():
    rows = [{"event_id": f"evt_{index:03d}"} for index in range(7)]
    connection = PagedConnection(rows, ("event_id",))
    repository = MySqlEventRepository(connection)

    seen = [row["event_id"] for row in repository.iter_all(batch_size=3)]

    assert seen == [f"evt_{index:03d}" for index in range(7)]
    assert len(connection.queries) == 3
    assert all(
        sql.startswith("SELECT * FROM event_log WHERE event_id >")
        for sql, _ in connection.queries
    )
    assert connection.queries[0][1] == ("", 3)
    assert connection.queries[1][1] == ("evt_002", 3)


def test_trace_iter_all_pages_by_composite_key():
    rows = [
        {"trace_id": "t1", "span_id": "s1"},
        {"trace_id": "t1", "span_id": "s2"},
        {"trace_id": "t2", "span_id": "s1"},
    ]
    connection = PagedConnection(rows, ("trace_id", "span_id"))
    repository = MySqlTraceRepository(connection)

    seen = [(row["trace_id"], row["span_id"]) for row in repository.iter_all(batch_size=2)]

    assert seen == [("t1", "s1"), ("t1", "s2"), ("t2", "s1")]
    assert connection.queries[0][1] == ("", "", 2)
    assert connection.queries[1][1] == ("t1", "s2", 2)
    assert all("(trace_id, span_id) > (%s, %s)" in sql for sql, _ in connection.queries)


def test_artifact_iter_all_pages_by_keyset():
    rows = [{"artifact_id": f"art_{index}"} for index in range(3)]
    connection = PagedConnection(rows, ("artifact_id",))
    repository = MySqlArtifactRepository(connection)

    seen = [row["artifact_id"] for row in repository.iter_all(batch_size=5)]

    assert seen == ["art_0", "art_1", "art_2"]
    assert len(connection.queries) == 1


def test_iter_all_rejects_non_positive_batch_size():
    repository = MySqlEventRepository(PagedConnection([], ("event_id",)))

    try:
        list(repository.iter_all(batch_size=0))
    except ValueError:
        return

    raise AssertionError("expected ValueError")

