"""Process-local RedisConnection reuse for StoryOS hot-state access."""
from __future__ import annotations

import hashlib
import threading
from typing import Any

from platform.state.redis_connection import RedisConnection


_CACHE: dict[str, Any] = {}
_LOCK = threading.Lock()


def _key(kwargs: dict | None) -> str:
    material = "\x1f".join(
        f"{key}={value}" for key, value in sorted((kwargs or {}).items())
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def shared_connection(kwargs: dict | None) -> Any:
    """Return a cached RedisConnection for these connection parameters."""
    key = _key(kwargs)
    connection = _CACHE.get(key)
    if connection is not None:
        return connection
    with _LOCK:
        connection = _CACHE.get(key)
        if connection is None:
            connection = RedisConnection(**(kwargs or {}))
            _CACHE[key] = connection
    return connection


def cached_connection_count() -> int:
    return len(_CACHE)


def reset() -> None:
    """Close and remove all cached connections."""
    with _LOCK:
        connections = list(_CACHE.values())
        _CACHE.clear()
    for connection in connections:
        try:
            connection.close()
        except Exception:
            pass
