from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import production_ledger  # noqa: E402
import production_ledger_persistence as persistence  # noqa: E402


def _mode(monkeypatch, value: str) -> None:
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": value},
    )


def test_facade_exports_canonical_authority_helpers_after_bootstrap():
    assert production_ledger.load_authority is not None
    assert production_ledger.authority_exists is not None
    assert production_ledger.authority_sha256 is not None


def test_json_authority_reads_complete_document(monkeypatch, tmp_path):
    _mode(monkeypatch, "json")
    meta = tmp_path / "meta"
    meta.mkdir()
    payload = {"frames": {"01": {"status": "LOCKED"}}, "policy": {"x": 1}}
    (meta / "production-ledger.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    assert production_ledger.load_authority(tmp_path) == payload
    assert production_ledger.authority_exists(tmp_path) is True
    assert production_ledger.authority_sha256(tmp_path)


def test_dual_authority_keeps_complete_document(monkeypatch, tmp_path):
    _mode(monkeypatch, "dual")
    meta = tmp_path / "meta"
    meta.mkdir()
    payload = {"frames": {"01": {"reviews": [{"decision": "pass"}]}}}
    (meta / "production-ledger.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    assert production_ledger.load_authority(tmp_path) == payload


def test_mysql_authority_operation_cache_reads_once_and_returns_deep_copy(monkeypatch, tmp_path):
    _mode(monkeypatch, "mysql")

    class Connection:
        def close(self):
            pass

    class AuthorityRepo:
        def __init__(self):
            self.reads = 0
            self.document = {"frames": {"01": {"status": "LOCKED"}}}

        def get(self, _episode_id):
            self.reads += 1
            return {"document": self.document}

    repo = AuthorityRepo()
    monkeypatch.setattr(persistence.episode_identity, "storage_episode_id", lambda _ep: "EPU_TEST")
    monkeypatch.setattr(persistence, "_repositories", lambda: (Connection(), repo, object(), object()))

    with persistence.operation_scope():
        first = persistence.load_authority(tmp_path)
        first["frames"]["01"]["status"] = "MUTATED_COPY"
        second = persistence.load_authority(tmp_path)
        assert second["frames"]["01"]["status"] == "LOCKED"
        repo.document = {"frames": {"01": {"status": "UPDATED"}}}
        persistence.invalidate(tmp_path)
        third = persistence.load_authority(tmp_path)

    assert repo.reads == 2
    assert third["frames"]["01"]["status"] == "UPDATED"


def test_mysql_authority_ignores_stale_file_and_reads_database(monkeypatch, tmp_path):
    _mode(monkeypatch, "mysql")
    meta = tmp_path / "meta"
    meta.mkdir()
    (meta / "production-ledger.json").write_text(
        '{"frames":{"01":{"status":"STALE_FILE"}}}', encoding="utf-8"
    )
    mysql_document = {"frames": {"01": {"status": "LOCKED"}}, "policy": {"x": 1}}
    monkeypatch.setattr(
        persistence, "load_authority", lambda _ep: mysql_document
    )
    loaded = production_ledger.load_authority(tmp_path)
    assert loaded == mysql_document
    assert loaded["frames"]["01"]["status"] == "LOCKED"
    assert production_ledger.authority_exists(tmp_path) is True
    assert production_ledger.authority_sha256(tmp_path)


def test_mysql_get_ledger_uses_database_not_stale_compatibility_file(monkeypatch, tmp_path):
    _mode(monkeypatch, "mysql")
    meta = tmp_path / "meta"
    meta.mkdir()
    ledger_path = meta / "production-ledger.json"
    ledger_path.write_text(
        '{"frames":{"01":{"status":"PENDING","attempts":[]}}}', encoding="utf-8"
    )
    mysql_document = {
        "frames": {
            "01": {
                "status": "GENERATING",
                "attempts": [{"attempt_id": "mysql-attempt", "result": "pending"}],
            }
        }
    }
    monkeypatch.setattr(persistence, "load_authority", lambda _ep: mysql_document)

    path, loaded = production_ledger.get_ledger(tmp_path)

    assert path == ledger_path
    assert loaded == mysql_document
    assert loaded["frames"]["01"]["attempts"][0]["attempt_id"] == "mysql-attempt"
