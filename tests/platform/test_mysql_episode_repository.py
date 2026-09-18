from platform.repository.mysql.mysql_episode_repository import MySqlEpisodeRepository


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.row = None

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1

    def query_one(self, sql, params=None):
        return self.row


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
