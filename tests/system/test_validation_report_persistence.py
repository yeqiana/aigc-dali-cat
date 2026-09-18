import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import validation_report_persistence as persistence  # noqa: E402


def _result():
    return {
        "story_os_validation_version": "2.2.3",
        "stage": "preproduction",
        "status": "PREPRODUCTION_VALIDATE_PASS",
        "next_state": "READY_FOR_SMOKE_TEST",
        "episode_dir": "ignored-by-projection",
        "checks": [{"name": "asset_sha_or_digest", "status": "PASS", "detail": "2 SHA/digest value(s)"}],
    }


def test_structured_payload_excludes_scan_context():
    payload = persistence.structured_payload(_result())
    assert payload["review_type"] == "VALIDATION_PREPRODUCTION"
    check = payload["checks"][0]
    assert check["name"] == "asset_sha_or_digest"
    assert check["status"] == "PASS"
    assert check["path"] is None
    assert check["detail"] == "2 SHA/digest value(s)"
    assert check["detail_bytes"] == len("2 SHA/digest value(s)".encode("utf-8"))
    assert check["detail_sha256"]
    assert "episode_dir" not in payload


def test_json_mode_is_noop_for_database(monkeypatch, tmp_path):
    monkeypatch.setattr(persistence.storage_config, "episode_meta_store_config", lambda: {"mode": "json"})
    saved = persistence.persist(tmp_path, _result())
    assert saved["mysql_written"] is False
    assert saved["payload"]["status"] == "PREPRODUCTION_VALIDATE_PASS"


def test_structured_payload_rejects_unknown_stage():
    with pytest.raises(ValueError, match="unsupported validation stage"):
        persistence.structured_payload({**_result(), "stage": "other"})


def test_large_check_detail_is_hashed_instead_of_stored():
    detail = "诊断正文=" + ("x" * 10000)
    payload = persistence.structured_payload({**_result(), "checks": [{
        "name": "large-diagnostic", "status": "FAIL", "detail": detail,
    }]})
    check = payload["checks"][0]
    assert "detail" not in check
    assert check["detail_bytes"] == len(detail.encode("utf-8"))
    assert check["detail_sha256"]
    assert check["detail_preview"].startswith("诊断正文=")
    assert persistence.payload_bytes(payload) <= persistence.MAX_INLINE_PAYLOAD_BYTES


def test_many_checks_fall_back_to_bounded_summary():
    checks = [{"name": f"check-{i}", "status": "PASS", "path": f"meta/{i}.json"} for i in range(1000)]
    payload = persistence.structured_payload({**_result(), "checks": checks})
    assert "checks" not in payload
    assert payload["check_count"] == 1000
    assert payload["pass_count"] == 1000
    assert payload["fail_count"] == 0
    assert persistence.payload_bytes(payload) <= persistence.MAX_INLINE_PAYLOAD_BYTES


def test_mysql_persist_only_sends_bounded_projection(monkeypatch, tmp_path):
    captured = {}

    class Connection:
        def close(self):
            pass

    class Repository:
        def upsert(self, row):
            captured.update(row)
            return {"review_id": "RV-test"}

    monkeypatch.setattr(persistence.storage_config, "episode_meta_store_config", lambda: {"mode": "mysql"})
    monkeypatch.setattr(persistence.episode_identity, "storage_episode_id", lambda _ep: "EPU_TEST")
    monkeypatch.setattr(persistence, "_repository", lambda _ep: (Connection(), Repository()))
    saved = persistence.persist(tmp_path, {**_result(), "checks": [{
        "name": "long", "status": "FAIL", "detail": "x" * 100000,
    }]})
    assert saved["mysql_written"] is True
    assert persistence.payload_bytes(captured["payload"]) <= persistence.MAX_INLINE_PAYLOAD_BYTES
    assert "detail" not in captured["payload"]["checks"][0]
