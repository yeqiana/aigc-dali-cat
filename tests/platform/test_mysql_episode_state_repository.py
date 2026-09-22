from platform.repository.mysql.mysql_episode_state_repository import (
    MySqlEpisodeStateRepository,
)


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.one = None
        self.rows = []
        self.affected = 1

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return self.affected

    def query_one(self, sql, params=None):
        return self.one

    def query_all(self, sql, params=None):
        return self.rows


def test_initialize_writes_current_and_history_rows():
    conn = FakeConnection()
    repo = MySqlEpisodeStateRepository(conn)
    repo.initialize(
        "EPU_1",
        "STORYBOARD_LOCKED",
        [
            {"state": "IDEA_LOCKED", "at": "2026-09-18T00:00:00+00:00", "note": "init"},
            {"state": "STORYBOARD_LOCKED", "at": "2026-09-18T00:10:00+00:00", "note": "story"},
        ],
        source="MIGRATION",
    )
    assert len(conn.executed) == 3
    assert conn.executed[0][1][2] == 2
    assert conn.executed[1][1][1:4] == (None, "IDEA_LOCKED", 1)
    assert conn.executed[2][1][1:4] == ("IDEA_LOCKED", "STORYBOARD_LOCKED", 2)


def test_transition_uses_optimistic_state_and_version_then_appends_history():
    conn = FakeConnection()
    repo = MySqlEpisodeStateRepository(conn)
    result = repo.transition(
        "EPU_1",
        expected_state="IDEA_LOCKED",
        expected_version=3,
        target_state="STORYBOARD_LOCKED",
        source="episode_state.transition",
        reason="gate passed",
        at="2026-09-18T01:00:00+00:00",
    )
    assert result["state_version"] == 4
    assert conn.executed[0][1][0:2] == ("STORYBOARD_LOCKED", 4)
    assert conn.executed[1][1][1:4] == ("IDEA_LOCKED", "STORYBOARD_LOCKED", 4)


def test_transition_conflict_fails_closed_without_history_append():
    conn = FakeConnection()
    conn.affected = 0
    repo = MySqlEpisodeStateRepository(conn)
    try:
        repo.transition(
            "EPU_1",
            expected_state="IDEA_LOCKED",
            expected_version=3,
            target_state="STORYBOARD_LOCKED",
            source="test",
            reason="x",
            at="2026-09-18T01:00:00+00:00",
        )
    except RuntimeError as exc:
        assert "EPISODE_STATE_CONFLICT" in str(exc)
    else:
        raise AssertionError("expected optimistic conflict")
    assert len(conn.executed) == 1
