from platform.repository.mysql.mysql_production_frame_repository import (
    MySqlProductionFrameRepository,
)


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.one = None
        self.rows = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1

    def query_one(self, sql, params=None):
        return self.one

    def query_all(self, sql, params=None):
        return self.rows


def test_upsert_projects_current_frame_state():
    conn = FakeConnection()
    result = MySqlProductionFrameRepository(conn).upsert({
        "episode_id": "EPU_1",
        "frame_no": 3,
        "status": "GENERATING",
        "approved_artifact_id": None,
        "current_attempt_id": "att-3",
        "contract_sha256": "a" * 64,
    })
    assert result == {
        "episode_id": "EPU_1",
        "frame_no": 3,
        "status": "GENERATING",
    }
    assert conn.executed[-1][1] == (
        "EPU_1", 3, "GENERATING", None, "att-3", "a" * 64
    )


def test_list_episode_decodes_current_rows():
    conn = FakeConnection()
    conn.rows = [
        {"EPISODE_ID": "EPU_1", "FRAME_NO": 1, "STATUS": "PENDING"},
        {"EPISODE_ID": "EPU_1", "FRAME_NO": 2, "STATUS": "LOCKED"},
    ]
    rows = MySqlProductionFrameRepository(conn).list_episode("EPU_1")
    assert [row["frame_no"] for row in rows] == [1, 2]
    assert rows[-1]["status"] == "LOCKED"


def test_frame_number_is_bounded():
    conn = FakeConnection()
    try:
        MySqlProductionFrameRepository(conn).upsert({
            "episode_id": "EPU_1", "frame_no": 0, "status": "PENDING"
        })
    except ValueError as exc:
        assert "1..999" in str(exc)
    else:
        raise AssertionError("expected frame range failure")
