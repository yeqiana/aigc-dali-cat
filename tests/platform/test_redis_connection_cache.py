from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import redis_connection_cache as cache  # noqa: E402


class FakeConnection:
    created = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.close_calls = 0
        self.__class__.created.append(self)

    def close(self):
        self.close_calls += 1


def test_shared_connection_reuses_by_connection_parameters(monkeypatch):
    cache.reset()
    FakeConnection.created = []
    monkeypatch.setattr(cache, "RedisConnection", FakeConnection)

    first = cache.shared_connection({"host": "127.0.0.1", "port": 6379})
    second = cache.shared_connection({"port": 6379, "host": "127.0.0.1"})
    other = cache.shared_connection({"host": "127.0.0.1", "port": 6380})

    assert first is second
    assert other is not first
    assert len(FakeConnection.created) == 2
    assert cache.cached_connection_count() == 2

    cache.reset()
    assert first.close_calls == 1
    assert other.close_calls == 1
