"""Typed Redis hot-state facade for Story OS Episode runtime projections.

Everything stored here is rebuildable.  Historical facts belong in MySQL.
"""
from __future__ import annotations

from dataclasses import dataclass


PREFIX = "STORYOS:EP"
LOCK_PREFIX = "STORYOS:LOCK:EP"


@dataclass(frozen=True)
class HotStateSpec:
    suffix: str
    ttl_seconds: int


SPECS = {
    "NEXT_ACTION": HotStateSpec("NEXT_ACTION", 900),
    "DRIVER_STATE": HotStateSpec("DRIVER_STATE", 180),
    "DRIVER_HEARTBEAT": HotStateSpec("DRIVER_HEARTBEAT", 90),
    "CIRCUIT_BREAKER": HotStateSpec("CIRCUIT_BREAKER", 300),
    "INFLIGHT": HotStateSpec("INFLIGHT", 600),
    "HOST_REQUEST_CURRENT": HotStateSpec("HOST_REQUEST_CURRENT", 900),
    "QUEUE": HotStateSpec("QUEUE", 1800),
    "COUNTERS": HotStateSpec("COUNTERS", 600),
    "EFFECTIVE_CONFIG": HotStateSpec("EFFECTIVE_CONFIG", 3600),
    "RUNTIME_CAPABILITIES": HotStateSpec("RUNTIME_CAPABILITIES", 300),
    "RUNNER_STATE": HotStateSpec("RUNNER_STATE", 120),
}


def episode_key(episode_id: str, kind: str) -> str:
    episode_id = str(episode_id or "").strip()
    kind = str(kind or "").strip().upper()
    if not episode_id:
        raise ValueError("episode_id is required")
    if kind not in SPECS:
        raise ValueError(f"unsupported hot-state kind: {kind}")
    return f"{PREFIX}:{episode_id}:{SPECS[kind].suffix}"


def lock_key(episode_id: str, scope: str) -> str:
    episode_id = str(episode_id or "").strip()
    scope = str(scope or "").strip().upper()
    if not episode_id or not scope:
        raise ValueError("episode_id and scope are required")
    return f"{LOCK_PREFIX}:{episode_id}:{scope}"


class EpisodeHotStateStore:
    """Small typed facade over RuntimeStateStore / RedisRuntimeStateStore."""

    def __init__(self, store):
        self.store = store

    def put(self, episode_id: str, kind: str, value, *, ttl_seconds: int | None = None) -> None:
        spec = SPECS[str(kind).upper()]
        self.store.set_state(
            episode_key(episode_id, kind),
            value,
            expire_seconds=spec.ttl_seconds if ttl_seconds is None else int(ttl_seconds),
        )

    def get(self, episode_id: str, kind: str):
        return self.store.get_state(episode_key(episode_id, kind))

    def delete(self, episode_id: str, kind: str) -> None:
        self.store.delete_state(episode_key(episode_id, kind))

