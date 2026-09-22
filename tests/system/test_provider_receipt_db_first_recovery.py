from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import provider_receipt_persistence as persistence  # noqa: E402


def test_json_mode_reads_compatibility_receipt(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    path = ep / "meta/provider-receipts/r.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"frame":"01","provider":"x"}', encoding="utf-8")
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "json"},
    )
    loaded = persistence.load_by_path(ep, path)
    assert loaded is not None
    assert loaded["source"] == "json"


def test_dual_mode_falls_back_to_json_when_mysql_unavailable(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    path = ep / "meta/provider-receipts/r.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"frame":"01","provider":"x"}', encoding="utf-8")
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "dual"},
    )
    monkeypatch.setattr(
        persistence.storage_config,
        "mysql_connection_kwargs",
        lambda *_args, **_kwargs: {"host": "invalid"},
    )

    class BrokenConnection:
        def __init__(self, **_kwargs):
            raise RuntimeError("offline")

    import platform.repository.mysql.mysql_connection as mysql_connection

    monkeypatch.setattr(mysql_connection, "MySqlConnection", BrokenConnection)
    loaded = persistence.load_by_path(ep, path)
    assert loaded is not None
    assert loaded["source"] == "json"
