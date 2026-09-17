from __future__ import annotations

from pathlib import Path

import storage_config
import story_json


def _episode_id(ep: Path) -> str:
    state = story_json.read_json(Path(ep) / "meta/episode-state.json", default={})
    return str((state or {}).get("episode_id") or Path(ep).name)


def mirror(ep: Path, kind: str, value: dict) -> dict:
    """Best-effort Redis mirror for rebuildable Runtime hot state.

    MySQL/file facts must never fail because Redis is unavailable. Therefore
    ``dual`` writes are fail-soft and report the error to the caller instead of
    raising. Default ``file`` mode performs no network access at all.
    """
    mode = storage_config.hot_state_config()["mode"]
    if mode == "file":
        return {"mode": mode, "redis_written": False}

    from platform.state.redis_connection import RedisConnection
    from platform.state.redis_runtime_state_store import RedisRuntimeStateStore
    from platform.state.storyos_hot_state import EpisodeHotStateStore

    connection = RedisConnection(**storage_config.redis_connection_kwargs())
    try:
        store = EpisodeHotStateStore(RedisRuntimeStateStore(connection.client))
        store.put(_episode_id(Path(ep).resolve()), kind, value)
        return {"mode": mode, "redis_written": True}
    except Exception as exc:  # Redis is an accelerator, not a fact authority.
        return {
            "mode": mode,
            "redis_written": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        connection.close()


def read(ep: Path, kind: str) -> dict:
    """Best-effort Redis read for a rebuildable hot-state projection.

    ``file`` mode never touches Redis. ``dual`` may return a Redis value, but
    callers must retain their file/runtime-workspace fallback whenever Redis is
    absent or unavailable.
    """
    mode = storage_config.hot_state_config()["mode"]
    if mode == "file":
        return {"mode": mode, "redis_read": False, "value": None}

    from platform.state.redis_connection import RedisConnection
    from platform.state.redis_runtime_state_store import RedisRuntimeStateStore
    from platform.state.storyos_hot_state import EpisodeHotStateStore

    connection = RedisConnection(**storage_config.redis_connection_kwargs())
    try:
        store = EpisodeHotStateStore(RedisRuntimeStateStore(connection.client))
        value = store.get(_episode_id(Path(ep).resolve()), kind)
        return {
            "mode": mode,
            "redis_read": value is not None,
            "value": value if isinstance(value, dict) else None,
        }
    except Exception as exc:  # Redis remains a rebuildable accelerator.
        return {
            "mode": mode,
            "redis_read": False,
            "value": None,
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        connection.close()

