"""Process-local bounded PyMySQL pools shared by MySqlConnection adapters."""
from __future__ import annotations

import hashlib
import os
import threading
from typing import Any

_ROLE_BUDGETS = {
    "scheduler": 6,
    "runner": 5,
    "api": 4,
    "cli": 3,
}
_CACHE: dict[str, Any] = {}
_LOCK = threading.RLock()
_ROLE_LOCK = threading.RLock()
_PROCESS_ROLE: str | None = None


def set_process_role(role: str) -> None:
    """Set the process's static MySQL connection budget role."""
    value = str(role or "").strip().lower()
    if value not in _ROLE_BUDGETS:
        raise ValueError(f"unknown StoryOS MySQL pool role: {role!r}")
    global _PROCESS_ROLE
    with _ROLE_LOCK:
        _PROCESS_ROLE = value


def process_role() -> str:
    with _ROLE_LOCK:
        role = _PROCESS_ROLE or os.environ.get("STORYOS_MYSQL_POOL_ROLE", "cli").strip().lower()
    return role if role in _ROLE_BUDGETS else "cli"


def process_budget() -> int:
    return _ROLE_BUDGETS[process_role()]


def _pool_key(kwargs: dict[str, Any], maxconnections: int) -> str:
    material = "\x1f".join(
        f"{key}={value}" for key, value in sorted((kwargs or {}).items())
    ) + f"\x1fmaxconnections={int(maxconnections)}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def shared_pool(kwargs: dict[str, Any] | None = None, *, maxconnections: int | None = None):
    """Return one bounded DBUtils PooledDB per connection identity and budget."""
    import pymysql
    from dbutils.pooled_db import PooledDB

    options = dict(kwargs or {})
    limit = int(maxconnections or process_budget())
    if limit < 1:
        raise ValueError("MySQL pool maxconnections must be positive")
    key = _pool_key(options, limit)
    pool = _CACHE.get(key)
    if pool is not None:
        return pool
    with _LOCK:
        pool = _CACHE.get(key)
        if pool is None:
            pool = PooledDB(
                creator=pymysql,
                maxconnections=limit,
                mincached=0,
                maxcached=limit,
                maxshared=0,
                blocking=True,
                ping=1,
                **options,
            )
            _CACHE[key] = pool
    return pool


def cached_pool_count() -> int:
    with _LOCK:
        return len(_CACHE)


def reset() -> None:
    """Close all cached pools. Intended for tests and explicit process teardown."""
    with _LOCK:
        pools = list(_CACHE.values())
        _CACHE.clear()
    for pool in pools:
        try:
            pool.close()
        except Exception:
            pass


def role_budgets() -> dict[str, int]:
    return dict(_ROLE_BUDGETS)
