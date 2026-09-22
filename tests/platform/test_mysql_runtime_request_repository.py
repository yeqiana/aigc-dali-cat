from platform.repository.mysql.mysql_runtime_request_repository import (
    MySqlRuntimeRequestRepository,
)


class FakeConnection:
    def __init__(self):
        self.executed = []
        self.one = None

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return 1

    def query_one(self, sql, params=None):
        return self.one


def test_runtime_request_repository_upsert_and_decode_inline_payload():
    conn = FakeConnection()
    repo = MySqlRuntimeRequestRepository(conn)
    payload = {
        "schema_version": 1,
        "request_id": "req-1",
        "mode": "full_auto",
        "topic": {"title": "test"},
    }

    saved = repo.upsert({
        "runtime_request_id": "req-1",
        "episode_id": "EPU_test",
        "request_type": "full_auto",
        "status": "BOUND",
        "fingerprint": "a" * 64,
        "payload": payload,
    })

    assert saved["runtime_request_id"] == "req-1"
    assert saved["episode_id"] == "EPU_test"
    assert conn.executed
    encoded = conn.executed[-1][1][-1]
    assert '"request_id":"req-1"' in encoded

    conn.one = {
        "RUNTIME_REQUEST_ID": "req-1",
        "EPISODE_ID": "EPU_test",
        "REQUEST_TYPE": "full_auto",
        "STATUS": "BOUND",
        "FINGERPRINT": "a" * 64,
        "PAYLOAD": encoded,
    }
    row = repo.get_by_id("req-1")
    assert row["payload"]["topic"]["title"] == "test"
    assert row["fingerprint"] == "a" * 64


def test_runtime_request_repository_uses_projection_when_document_ref_is_present():
    conn = FakeConnection()
    repo = MySqlRuntimeRequestRepository(conn)
    payload = {
        "schema_version": 1,
        "request_id": "req-large",
        "mode": "full_auto",
        "created_at": "2026-09-18T00:00:00+00:00",
        "story_input": {"mode": "user_seed", "raw": "x" * 20000},
        "image": {"model": "gpt-image-test", "quality": "high"},
        "user_intent": {"full_auto_authorized": True},
    }
    ref = {
        "rel": "meta/runtime/requests/req-large.json",
        "sha256": "b" * 64,
        "bytes": 20000,
    }

    repo.upsert({
        "runtime_request_id": "req-large",
        "episode_id": "EPU_test",
        "request_type": "full_auto",
        "status": "BOUND",
        "fingerprint": "c" * 64,
        "payload": payload,
        "payload_ref": ref,
    })

    encoded = conn.executed[-1][1][-1]
    assert '"projection_type":"RUNTIME_REQUEST_REF"' in encoded
    assert '"document"' in encoded
    assert "x" * 1000 not in encoded
