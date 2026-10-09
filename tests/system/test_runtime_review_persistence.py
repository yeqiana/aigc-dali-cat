import sys
from pathlib import Path


SYSTEM = Path(__file__).resolve().parents[2] / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_review_persistence


def test_parse_current_and_attempt_request_paths(tmp_path):
    ep = tmp_path / "episodes" / "demo"
    current = ep / "meta/runtime/reviews/story-semantic-request.json"
    attempt = ep / "meta/runtime/reviews/story-semantic-attempt-2-request.json"
    c = runtime_review_persistence.parse_request_path(current)
    a = runtime_review_persistence.parse_request_path(attempt)
    assert c["review_kind"] == "story-semantic"
    assert c["record_key"] == "CURRENT"
    assert a["record_key"] == "ATTEMPT:2"
    assert a["attempt"] == 2

def _projection_case():
    import hashlib
    original = {
        "review_kind": "story-semantic-critic-shadow",
        "request_id": "shadow-a1",
        "status": "AWAITING_PRODUCT_REVIEW",
        "attempt": 1,
        "created_at": "2026-10-02T23:14:02+08:00",
        "deadline_at": "2026-10-02T23:29:02+08:00",
        "candidate_path": "meta/runtime/agent-shadow/story-decision.json",
    }
    ref = {
        "projection_type": "RUNTIME_REVIEW_REQUEST_REF",
        "document": {
            "rel": "meta/runtime/review-documents/sha-bound.json",
            "sha256": runtime_review_persistence.payload_sha256(original),
        },
        "review_kind": original["review_kind"],
        "status": original["status"],
        "request_id": original["request_id"],
        "attempt": 1,
    }
    row = {
        "review_kind": original["review_kind"],
        "request_id": original["request_id"],
        "status": original["status"],
        "attempt_no": 1,
        "payload": ref,
    }
    return original, row


def _fake_repository(monkeypatch, rows, *, method):
    class FakeConnection:
        def __init__(self):
            self.closed = False
        def close(self):
            self.closed = True
    connection = FakeConnection()
    class FakeRepository:
        def list_current(self, episode_id):
            assert episode_id
            return rows if method == "current" else []
        def list_attempts(self, episode_id, kind):
            assert episode_id and kind
            return rows if method == "attempts" else []
    monkeypatch.setattr(runtime_review_persistence, "_mode", lambda: "mysql")
    monkeypatch.setattr(runtime_review_persistence, "_repository",
                        lambda _ep: (connection, FakeRepository()))
    return connection


def test_mysql_review_list_current_rehydrates_sha_bound_doc(monkeypatch, tmp_path):
    original, row = _projection_case()
    connection = _fake_repository(monkeypatch, [row], method="current")
    monkeypatch.setattr(runtime_review_persistence.runtime_workspace, "read_json",
                        lambda ep, rel, default=None: dict(original))
    rows = runtime_review_persistence.list_current(tmp_path / "ep")
    assert len(rows) == 1
    assert rows[0]["payload"]["deadline_at"] == original["deadline_at"]
    assert rows[0]["payload"]["candidate_path"] == original["candidate_path"]
    assert connection.closed


def test_mysql_review_list_attempts_rehydrates_sha_bound_doc(monkeypatch, tmp_path):
    original, row = _projection_case()
    connection = _fake_repository(monkeypatch, [row], method="attempts")
    monkeypatch.setattr(runtime_review_persistence.runtime_workspace, "read_json",
                        lambda ep, rel, default=None: dict(original))
    rows = runtime_review_persistence.list_attempts(tmp_path / "ep", original["review_kind"])
    assert len(rows) == 1
    assert rows[0]["payload"]["created_at"] == original["created_at"]
    assert connection.closed


def test_mysql_review_list_refuses_mismatched_document_sha(monkeypatch, tmp_path):
    import pytest
    original, row = _projection_case()
    connection = _fake_repository(monkeypatch, [row], method="current")
    monkeypatch.setattr(runtime_review_persistence.runtime_workspace, "read_json",
                        lambda ep, rel, default=None: {**original, "deadline_at": "tampered"})
    with pytest.raises(ValueError, match="DOCUMENT_SHA_MISMATCH"):
        runtime_review_persistence.list_current(tmp_path / "ep")
    assert connection.closed


def test_mysql_review_list_refuses_wrong_identity_even_with_valid_sha(monkeypatch, tmp_path):
    import pytest
    original, row = _projection_case()
    different = {**original, "request_id": "other-request"}
    row["payload"]["document"]["sha256"] = runtime_review_persistence.payload_sha256(different)
    connection = _fake_repository(monkeypatch, [row], method="current")
    monkeypatch.setattr(runtime_review_persistence.runtime_workspace, "read_json",
                        lambda ep, rel, default=None: different)
    with pytest.raises(ValueError, match="DOCUMENT_IDENTITY_MISMATCH"):
        runtime_review_persistence.list_current(tmp_path / "ep")
    assert connection.closed
