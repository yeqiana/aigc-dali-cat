from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import hot_state_bridge  # noqa: E402
import redis_connection_cache  # noqa: E402


class FakeRedisClient:
    def __init__(self):
        self.values = {}

    def set(self, key, value, ex=None):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def delete(self, key):
        self.values.pop(key, None)


class FakeConnection:
    created = []

    def __init__(self, **kwargs):
        self.client = FakeRedisClient()
        self.close_calls = 0
        self.__class__.created.append(self)

    def close(self):
        self.close_calls += 1


def test_hot_state_bridge_reuses_cached_connection(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    ep.mkdir()
    FakeConnection.created = []
    redis_connection_cache.reset()
    monkeypatch.setattr(redis_connection_cache, "RedisConnection", FakeConnection)
    monkeypatch.setattr(
        hot_state_bridge.storage_config,
        "hot_state_config",
        lambda: {"mode": "dual"},
    )
    monkeypatch.setattr(
        hot_state_bridge.storage_config,
        "redis_connection_kwargs",
        lambda: {"host": "fake", "port": 6379},
    )
    monkeypatch.setattr(hot_state_bridge, "_episode_id", lambda _ep: "EPU_TEST")

    assert hot_state_bridge.mirror(ep, "NEXT_ACTION", {"action": "STORYBOARD"})[
        "redis_written"
    ]
    assert hot_state_bridge.read(ep, "NEXT_ACTION")["value"] == {
        "action": "STORYBOARD"
    }
    assert hot_state_bridge.delete(ep, "NEXT_ACTION")["redis_deleted"]
    assert len(FakeConnection.created) == 1
    assert FakeConnection.created[0].close_calls == 0

    redis_connection_cache.reset()
    assert FakeConnection.created[0].close_calls == 1
