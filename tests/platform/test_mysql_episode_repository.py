from platform.repository.mysql.mysql_episode_repository import MySqlEpisodeRepository


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.queries = []
        self.row = None
        self.rows = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1

    def query_one(self, sql, params=None):
        return self.row

    def query_all(self, sql, params=None):
        self.queries.append((sql, params))
        return self.rows


def test_upsert_keeps_storage_and_business_identity_separate():
    conn = FakeConnection()
    MySqlEpisodeRepository(conn).upsert({
        "episode_id": "EPU_abc",
        "business_episode_id": "10-01",
        "episode_namespace": "10_series/01_title",
        "series_id": "10_series",
        "title": "title",
        "tool_version": "3",
        "disposition": "ACTIVE",
    })
    _sql, params = conn.executed[-1]
    assert params[:4] == ("EPU_abc", "10-01", "10_series/01_title", "10_series")


def test_get_maps_database_columns():
    conn = FakeConnection()
    conn.row = {
        "EPISODE_ID": "EPU_abc",
        "BUSINESS_EPISODE_ID": "10-01",
        "EPISODE_NAMESPACE": "10_series/01_title",
        "SERIES_ID": "10_series",
        "TITLE": "title",
        "TOOL_VERSION": "3",
        "DISPOSITION": "ACTIVE",
    }
    row = MySqlEpisodeRepository(conn).get("EPU_abc")
    assert row["business_episode_id"] == "10-01"
    assert row["episode_namespace"] == "10_series/01_title"



def test_get_by_namespace_maps_database_columns():
    conn = FakeConnection()
    conn.row = {
        "EPISODE_ID": "EPU_abc",
        "BUSINESS_EPISODE_ID": "10-01",
        "EPISODE_NAMESPACE": "10_series/01_title",
        "SERIES_ID": "10_series",
        "TITLE": "title",
        "TOOL_VERSION": "3",
        "DISPOSITION": "ACTIVE",
    }
    row = MySqlEpisodeRepository(conn).get_by_namespace("10_series/01_title")
    assert row["episode_id"] == "EPU_abc"


def test_list_namespaces_returns_canonical_episode_paths():
    conn = FakeConnection()
    conn.rows = [
        {"EPISODE_NAMESPACE": "series/a"},
        {"EPISODE_NAMESPACE": "series/b"},
    ]
    assert MySqlEpisodeRepository(conn).list_namespaces() == ["series/a", "series/b"]


def test_list_active_summaries_maps_episode_and_state_rows():
    conn = FakeConnection()
    conn.rows = [{
        "EPISODE_ID": "EPU_abc",
        "BUSINESS_EPISODE_ID": "10-01",
        "EPISODE_NAMESPACE": "10_series/01_title",
        "SERIES_ID": "10_series",
        "TITLE": "title",
        "TOOL_VERSION": "3",
        "DISPOSITION": "ACTIVE",
        "CURRENT_STATE": "VISUAL_CALIBRATED",
        "STATE_SOURCE": "MYSQL_REDIS_CUTOVER",
        "STATE_UPDATE_TIME": "2026-09-20 03:30:00",
    }]

    rows = MySqlEpisodeRepository(conn).list_active_summaries(limit=21, offset=20)

    assert rows[0]["episode_namespace"] == "10_series/01_title"
    assert rows[0]["current_state"] == "VISUAL_CALIBRATED"
    assert rows[0]["state_source"] == "MYSQL_REDIS_CUTOVER"
    sql, params = conn.queries[-1]
    assert "LEFT JOIN TB_EPISODE_STATE" in sql
    assert "LEFT(e.EPISODE_NAMESPACE, 1) NOT IN ('_', '.')" in sql
    assert params == (21, 20)


def test_update_disposition_is_compare_and_set():
    conn = FakeConnection()
    MySqlEpisodeRepository(conn).update_disposition(
        "EPU_abc", "ABANDONED", expected="ACTIVE"
    )
    _sql, params = conn.executed[-1]
    assert params == ("ABANDONED", "EPU_abc", "ACTIVE")
