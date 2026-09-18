from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import host_request_persistence as persistence  # noqa: E402


def test_json_mode_round_trip(monkeypatch, tmp_path):
    ep = tmp_path / "episodes" / "s" / "e"
    ep.mkdir(parents=True)
    monkeypatch.setattr(persistence.runtime_workspace, "EPISODES_ROOT", tmp_path / "episodes")
    monkeypatch.setattr(persistence.runtime_workspace, "DEFAULT_ROOT", tmp_path / "runtime")
    monkeypatch.setattr(persistence.storage_config, "episode_meta_store_config", lambda: {"mode": "json"})
    data = {"request_id": "preimage-1", "status": "HOST_ACTION_REQUIRED", "next_step": "PREIMAGE_WORLD"}
    persistence.save(ep, data)
    assert persistence.load(ep, "preimage-1") == data


def test_mysql_mode_loads_without_physical_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"; ep.mkdir()
    monkeypatch.setattr(persistence.storage_config, "episode_meta_store_config", lambda: {"mode": "mysql"})
    monkeypatch.setattr(persistence.storage_config, "mysql_connection_kwargs", lambda *_a, **_k: {})
    monkeypatch.setattr(persistence.episode_identity, "storage_episode_id", lambda _ep: "EPU_test")
    import platform.repository.mysql.mysql_connection as mysql_connection
    import platform.repository.mysql.mysql_host_request_repository as host_repo

    class FakeConnection:
        def __init__(self, **_kwargs): pass
        def close(self): pass

    monkeypatch.setattr(mysql_connection, "MySqlConnection", FakeConnection)
    monkeypatch.setattr(host_repo.MySqlHostRequestRepository, "get_by_id", lambda self, request_id: {
        "payload": {"request_id": request_id, "status": "FINALIZED"}
    })
    assert persistence.load(ep, "preimage-1")["status"] == "FINALIZED"
