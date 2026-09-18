from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import effective_config  # noqa: E402


def test_write_mirrors_effective_config(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    row = {"schema_version": 1, "sources": {}}
    calls = []
    monkeypatch.setattr(effective_config.runtime_portability, "assert_episode_directory", lambda _ep: None)
    monkeypatch.setattr(effective_config, "snapshot", lambda: row)
    monkeypatch.setattr(effective_config.runtime_workspace, "write_json", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        effective_config.hot_state_bridge,
        "mirror",
        lambda episode, kind, value: calls.append((Path(episode), kind, dict(value))) or {"redis_written": True},
    )
    assert effective_config.write(ep) == row
    assert calls == [(ep, "EFFECTIVE_CONFIG", row)]


def test_load_prefers_redis(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    monkeypatch.setattr(
        effective_config.hot_state_bridge,
        "read",
        lambda *_args, **_kwargs: {"redis_read": True, "value": {"source": "redis"}},
    )
    assert effective_config.load(ep) == {"source": "redis"}


def test_load_falls_back_to_runtime_workspace(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    monkeypatch.setattr(
        effective_config.hot_state_bridge,
        "read",
        lambda *_args, **_kwargs: {"redis_read": False, "value": None},
    )
    monkeypatch.setattr(
        effective_config.runtime_workspace,
        "read_json",
        lambda *_args, **_kwargs: {"source": "file"},
    )
    assert effective_config.load(ep) == {"source": "file"}
