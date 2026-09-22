from platform.repository.mysql.mysql_review_record_repository import MySqlReviewRecordRepository


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.row = None
        self.queries = []

    def execute(self, sql, params=()):
        self.executed.append((sql, params))
        return 1

    def query_one(self, sql, params=()):
        self.queries.append((sql, params))
        return self.row


def test_review_record_upsert_and_load():
    conn = FakeConnection()
    repo = MySqlReviewRecordRepository(conn)
    saved = repo.upsert({
        "episode_id": "EPU_test",
        "review_type": "VALIDATION_BOOTSTRAP",
        "decision": "PASS",
        "source_sha256": "a" * 64,
        "reviewer_type": "POLICY",
        "payload": {"status": "BOOTSTRAP_VALIDATE_PASS"},
    })
    assert saved["review_id"].startswith("RV_")
    conn.row = {
        "REVIEW_ID": saved["review_id"], "EPISODE_ID": "EPU_test",
        "REVIEW_TYPE": "VALIDATION_BOOTSTRAP", "ATTEMPT_NO": 1,
        "DECISION": "PASS", "SOURCE_SHA256": "a" * 64,
        "REVIEWER_TYPE": "POLICY", "PAYLOAD": '{"status":"BOOTSTRAP_VALIDATE_PASS"}',
    }
    loaded = repo.get_by_id(saved["review_id"])
    assert conn.queries[-1][1] == (saved["review_id"],)
    assert loaded["payload"] == {"status": "BOOTSTRAP_VALIDATE_PASS"}


def test_review_record_rejects_invalid_attempt():
    import pytest

    with pytest.raises(ValueError, match="attempt_no"):
        MySqlReviewRecordRepository(FakeConnection()).upsert({
            "episode_id": "EPU_test", "review_type": "VALIDATION_BOOTSTRAP",
            "attempt_no": 0, "decision": "PASS", "payload": {},
        })
