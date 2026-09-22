from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_request  # noqa: E402
import runtime_request_persistence as persistence  # noqa: E402


class FakeConnection:
    def close(self):
        pass


class FakeRepository:
    def __init__(self, row=None, error=None):
        self.row = row
        self.error = error
        self.saved = []

    def get_latest(self, _episode_id):
        if self.error:
            raise self.error
        return self.row

    def get_by_id(self, _request_id):
        if self.error:
            raise self.error
        return self.row

    def upsert(self, record):
        self.saved.append(record)
        return {
            "runtime_request_id": record["runtime_request_id"],
            "episode_id": record["episode_id"],
            "request_type": record["request_type"],
            "status": record["status"],
        }


def _valid_request():
    return runtime_request.compile_request("全自动做一篇「Runtime Request Authority Test」。")


def test_mysql_missing_row_ignores_stale_compatibility_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    legacy = ep / persistence.REL
    legacy.parent.mkdir(parents=True)
    legacy.write_text('{"request_id":"stale-file"}', encoding="utf-8")

    repo = FakeRepository(row=None)
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(persistence, "_repository", lambda _ep: (FakeConnection(), repo))
    monkeypatch.setattr(persistence, "_episode_id", lambda _ep: "EPU_test")

    assert persistence.load(ep) is None


def test_mysql_repository_failure_propagates_instead_of_file_fallback(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    legacy = ep / persistence.REL
    legacy.parent.mkdir(parents=True)
    legacy.write_text('{"request_id":"stale-file"}', encoding="utf-8")

    repo = FakeRepository(error=RuntimeError("mysql unavailable"))
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(persistence, "_repository", lambda _ep: (FakeConnection(), repo))
    monkeypatch.setattr(persistence, "_episode_id", lambda _ep: "EPU_test")

    with pytest.raises(RuntimeError, match="mysql unavailable"):
        persistence.load(ep)


def test_bind_data_mysql_mode_does_not_materialize_compatibility_json(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime_request, "ROOT", tmp_path)
    ep = tmp_path / "episodes" / "authority-test"
    (ep / "meta").mkdir(parents=True)
    request = _valid_request()
    persisted = []

    monkeypatch.setattr(
        runtime_request.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(
        runtime_request,
        "authority_for_episode",
        lambda _ep: None,
    )
    monkeypatch.setattr(
        runtime_request.runtime_request_persistence,
        "persist",
        lambda _ep, payload: persisted.append(dict(payload)) or {
            "mode": "mysql", "mysql_written": True
        },
    )

    target = runtime_request.bind_data(request, ep)

    assert target == ep / runtime_request.EPISODE_REL
    assert not target.exists()
    assert persisted[-1]["request_id"] == request["request_id"]


def test_mysql_projection_resolves_authority_document_with_sha(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    request = _valid_request()
    rel = Path("meta/runtime/requests/req.json")
    document = persistence.runtime_workspace.write_json(ep, rel, request)
    ref = persistence.document_reference(
        request, rel.as_posix(), bytes_size=document.stat().st_size
    )
    row = {
        "runtime_request_id": request["request_id"],
        "episode_id": "EPU_test",
        "payload": {
            "projection_type": "RUNTIME_REQUEST_REF",
            "document": ref,
        },
    }
    repo = FakeRepository(row=row)

    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(persistence, "_repository", lambda _ep: (FakeConnection(), repo))
    monkeypatch.setattr(persistence, "_episode_id", lambda _ep: "EPU_test")

    loaded = persistence.load(ep)
    assert loaded["request_id"] == request["request_id"]

    document.write_text('{"tampered":true}', encoding="utf-8")
    with pytest.raises(ValueError, match="sha256 mismatch"):
        persistence.load(ep)
