from __future__ import annotations

from pathlib import Path

import storage_config
import story_json
import episode_identity
import redis_connection_cache


class HotStateAuthorityError(RuntimeError):
    """Redis authority is unavailable in redis-only mode."""


def compatibility_write_allowed() -> bool:
    """Legacy file/workspace shadows stop once Redis is authoritative."""
    return storage_config.hot_state_config()["mode"] != "redis"


def file_fallback_allowed(result: dict) -> bool:
    """Compatibility files are readable only before Redis becomes authority."""
    return str((result or {}).get("mode") or "") != "redis"


def value_or_fallback(result: dict, fallback, *, default=None):
    """Return Redis value, otherwise compatibility fallback only outside redis mode."""
    value = (result or {}).get("value")
    if isinstance(value, dict):
        return value
    if file_fallback_allowed(result):
        return fallback()
    return default


def _episode_id(ep: Path) -> str:
    return episode_identity.storage_episode_id(ep)


def mirror(ep: Path, kind: str, value: dict) -> dict:
    """Best-effort Redis mirror for rebuildable Runtime hot state.

    MySQL/file facts must never fail because Redis is unavailable. Therefore
    ``dual`` writes are fail-soft and report the error to the caller instead of
    raising. Default ``file`` mode performs no network access at all.
    """
    mode = storage_config.hot_state_config()["mode"]
    if mode == "file":
        return {"mode": mode, "redis_written": False}

    from platform.state.redis_runtime_state_store import RedisRuntimeStateStore
    from platform.state.storyos_hot_state import EpisodeHotStateStore

    try:
        connection = redis_connection_cache.shared_connection(
            storage_config.redis_connection_kwargs()
        )
        store = EpisodeHotStateStore(RedisRuntimeStateStore(connection.client))
        store.put(_episode_id(Path(ep).resolve()), kind, value)
        return {"mode": mode, "redis_written": True}
    except Exception as exc:
        if mode == "redis":
            raise HotStateAuthorityError(
                f"REDIS_HOT_STATE_WRITE_FAILED kind={kind}: {type(exc).__name__}: {exc}"
            ) from exc
        return {
            "mode": mode,
            "redis_written": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def read(ep: Path, kind: str) -> dict:
    """Best-effort Redis read for a rebuildable hot-state projection.

    ``file`` mode never touches Redis. ``dual`` may return a Redis value, but
    callers must retain their file/runtime-workspace fallback whenever Redis is
    absent or unavailable.
    """
    mode = storage_config.hot_state_config()["mode"]
    if mode == "file":
        return {"mode": mode, "redis_read": False, "value": None}

    from platform.state.redis_runtime_state_store import RedisRuntimeStateStore
    from platform.state.storyos_hot_state import EpisodeHotStateStore

    try:
        connection = redis_connection_cache.shared_connection(
            storage_config.redis_connection_kwargs()
        )
        store = EpisodeHotStateStore(RedisRuntimeStateStore(connection.client))
        value = store.get(_episode_id(Path(ep).resolve()), kind)
        return {
            "mode": mode,
            "redis_read": isinstance(value, dict),
            "value": value if isinstance(value, dict) else None,
            "authoritative_missing": mode == "redis" and not isinstance(value, dict),
        }
    except Exception as exc:
        if mode == "redis":
            raise HotStateAuthorityError(
                f"REDIS_HOT_STATE_READ_FAILED kind={kind}: {type(exc).__name__}: {exc}"
            ) from exc
        return {
            "mode": mode,
            "redis_read": False,
            "value": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def delete(ep: Path, kind: str) -> dict:
    """Best-effort removal of one rebuildable Redis hot-state projection."""
    mode = storage_config.hot_state_config()["mode"]
    if mode == "file":
        return {"mode": mode, "redis_deleted": False}

    from platform.state.redis_runtime_state_store import RedisRuntimeStateStore
    from platform.state.storyos_hot_state import EpisodeHotStateStore

    try:
        connection = redis_connection_cache.shared_connection(
            storage_config.redis_connection_kwargs()
        )
        store = EpisodeHotStateStore(RedisRuntimeStateStore(connection.client))
        store.delete(_episode_id(Path(ep).resolve()), kind)
        return {"mode": mode, "redis_deleted": True}
    except Exception as exc:
        if mode == "redis":
            raise HotStateAuthorityError(
                f"REDIS_HOT_STATE_DELETE_FAILED kind={kind}: {type(exc).__name__}: {exc}"
            ) from exc
        return {
            "mode": mode,
            "redis_deleted": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
