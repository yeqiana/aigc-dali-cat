from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import hot_state_bridge  # noqa: E402
import storage_config  # noqa: E402


class _FakeRedis:
    def __init__(self):
        self.data = {}

    def set(self, key, value, ex=None, nx=False):
        if nx and key in self.data:
            return False
        self.data[key] = value
        return True

    def get(self, key):
        return self.data.get(key)

    def delete(self, key):
        self.data.pop(key, None)


class _FakeConnection:
    client = _FakeRedis()

    def __init__(self, **_kwargs):
        self.client = type(self).client

    def close(self):
        pass


def test_extended_hot_state_bridge_round_trips_without_file_cleanup(monkeypatch, tmp_path):
    monkeypatch.setattr(storage_config, "hot_state_config", lambda: {"mode": "dual"})
    monkeypatch.setattr(storage_config, "redis_connection_kwargs", lambda: {})
    monkeypatch.setattr(
        "platform.state.redis_connection.RedisConnection", _FakeConnection
    )
    _FakeConnection.client.data.clear()
    ep = tmp_path / "episode"
    ep.mkdir()
    value = {"schema_version": 1, "state": "RUNNING"}
    kinds = (
        "RUNTIME_ROUTE",
        "RESUME_TOKEN",
        "RESUME_CAPSULE",
        "FAST_PATH",
        "FULL_AUTO_STATUS",
        "TRACE_CURRENT",
        "TRANSPORT_STATE",
        "BATCH_CAPABILITY",
        "CODEX_BATCH_CAPABILITY",
    )

    for kind in kinds:
        written = hot_state_bridge.mirror(ep, kind, value)
        assert written["redis_written"] is True
        loaded = hot_state_bridge.read(ep, kind)
        assert loaded["redis_read"] is True
        assert loaded["value"] == value

    assert not (ep / "meta").exists()


def test_hot_state_bridge_delete_is_scoped_to_redis(monkeypatch, tmp_path):
    monkeypatch.setattr(storage_config, "hot_state_config", lambda: {"mode": "dual"})
    monkeypatch.setattr(storage_config, "redis_connection_kwargs", lambda: {})
    monkeypatch.setattr(
        "platform.state.redis_connection.RedisConnection", _FakeConnection
    )
    _FakeConnection.client.data.clear()
    ep = tmp_path / "episode"
    ep.mkdir()
    hot_state_bridge.mirror(ep, "RUNTIME_ROUTE", {"route": "resume"})
    result = hot_state_bridge.delete(ep, "RUNTIME_ROUTE")
    assert result["redis_deleted"] is True
    assert hot_state_bridge.read(ep, "RUNTIME_ROUTE")["value"] is None
