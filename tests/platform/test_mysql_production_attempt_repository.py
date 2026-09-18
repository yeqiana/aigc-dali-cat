import json

from platform.repository.mysql.mysql_production_attempt_repository import (
    MySqlProductionAttemptRepository,
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


def test_upsert_projects_attempt_and_keeps_bounded_payload():
    conn = FakeConnection()
    payload = {"attempt_id": "att-1", "request": {"model": "gpt-image"}}
    result = MySqlProductionAttemptRepository(conn).upsert({
        "attempt_id": "att-1",
        "episode_id": "EPU_1",
        "frame_no": 1,
        "attempt_no": 2,
        "attempt_kind": "repair",
        "status": "pending",
        "provider": "openai",
        "model": "gpt-image",
        "payload": payload,
    })
    assert result["attempt_no"] == 2
    params = conn.executed[-1][1]
    assert params[:6] == ("att-1", "EPU_1", 1, 2, "repair", "pending")
    assert json.loads(params[-1])["attempt_id"] == "att-1"


def test_list_frame_decodes_payload():
    conn = FakeConnection()
    conn.rows = [{
        "ATTEMPT_ID": "att-1",
        "EPISODE_ID": "EPU_1",
        "FRAME_NO": 1,
        "ATTEMPT_NO": 1,
        "ATTEMPT_KIND": "original",
        "STATUS": "success",
        "PAYLOAD": '{"result":"success"}',
    }]
    rows = MySqlProductionAttemptRepository(conn).list_frame("EPU_1", 1)
    assert rows[0]["payload"]["result"] == "success"
    assert rows[0]["attempt_kind"] == "original"


def test_attempt_number_must_be_positive():
    conn = FakeConnection()
    try:
        MySqlProductionAttemptRepository(conn).upsert({
            "attempt_id": "att-1",
            "episode_id": "EPU_1",
            "frame_no": 1,
            "attempt_no": 0,
            "attempt_kind": "original",
            "status": "pending",
            "payload": {},
        })
    except ValueError as exc:
        assert "attempt_no" in str(exc)
    else:
        raise AssertionError("expected attempt_no failure")
