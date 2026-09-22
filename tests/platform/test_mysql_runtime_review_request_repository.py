from platform.repository.mysql.mysql_runtime_review_request_repository import (
    MySqlRuntimeReviewRequestRepository,
    runtime_review_record_id,
)


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.one = None
        self.all = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def query_one(self, sql, params=None):
        return self.one

    def query_all(self, sql, params=None):
        return self.all


def test_runtime_review_record_id_separates_current_and_attempt():
    current = runtime_review_record_id("EPU_x", "story-semantic", "CURRENT")
    attempt = runtime_review_record_id("EPU_x", "story-semantic", "ATTEMPT:1")
    assert current != attempt


def test_runtime_review_repository_upsert_and_decode():
    conn = FakeConnection()
    repo = MySqlRuntimeReviewRequestRepository(conn)
    saved = repo.upsert({
        "episode_id": "EPU_x",
        "review_kind": "story-semantic",
        "record_key": "ATTEMPT:1",
        "attempt_no": 1,
        "request_id": "req-1",
        "request_fingerprint": "a" * 64,
        "status": "FINALIZED",
        "payload": {"request_id": "req-1", "attempt": 1},
    })
    assert saved["record_key"] == "ATTEMPT:1"
    assert conn.executed
    conn.one = {
        "RUNTIME_REVIEW_RECORD_ID": saved["runtime_review_record_id"],
        "EPISODE_ID": "EPU_x",
        "REVIEW_KIND": "story-semantic",
        "RECORD_KEY": "ATTEMPT:1",
        "ATTEMPT_NO": 1,
        "REQUEST_ID": "req-1",
        "REQUEST_FINGERPRINT": "a" * 64,
        "STATUS": "FINALIZED",
        "PAYLOAD": '{"request_id":"req-1","attempt":1}',
    }
    assert repo.get("EPU_x", "story-semantic", "ATTEMPT:1")["payload"]["attempt"] == 1
