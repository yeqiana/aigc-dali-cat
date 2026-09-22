#!/usr/bin/env python3
"""Process-level MySqlConnection reuse for Episode runtime persistence.

Every Episode persistence read used to construct a fresh MySqlConnection and
close it in a finally block.  MySqlConnection is already a per-thread connection
holder with reconnect-on-drop, so building one per call turned each contract /
episode-state read into a brand new TCP handshake against the remote Story OS
runtime MySQL (STORYOS_MYSQL_HOST).

frame_contract.verify_all walks every frame, and each frame reads the character
contract, character visual contract, world identity, appearance anchor and
Episode state several times.  With one handshake per read a single next-action
derivation cost hundreds of handshakes and pinned the resident Driver for
minutes: ~96% of that wall time was blocked in pymysql connect / read while the
process CPU counter barely moved.

Cached connections are deliberately not closed by callers, because closing them
is exactly what made the cache useless.  Process exit, or reset(), releases them.

The cache key is the fully resolved connection kwargs, so a run pointed at a
different database still gets its own connection instead of silently reusing one
bound elsewhere.  The key is hashed so the password never sits in a repr-able
structure.
"""
from __future__ import annotations

import hashlib
import threading
from typing import Any

_CACHE: dict[str, Any] = {}
_LOCK = threading.Lock()


def _key(kwargs: dict) -> str:
    material = "\x1f".join(
        f"{key}={value}" for key, value in sorted((kwargs or {}).items())
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def shared_connection(kwargs: dict) -> Any:
    """Return the cached MySqlConnection for these connection kwargs.

    The caller must not close the returned connection; the cache owns it.
    """
    key = _key(kwargs)
    connection = _CACHE.get(key)
    if connection is not None:
        return connection
    from platform.repository.mysql.mysql_connection import MySqlConnection

    with _LOCK:
        connection = _CACHE.get(key)
        if connection is None:
            connection = MySqlConnection(**(kwargs or {}))
            _CACHE[key] = connection
    return connection


def cached_connection_count() -> int:
    return len(_CACHE)


def reset() -> None:
    """Drop and close every cached connection (tests / explicit teardown)."""
    with _LOCK:
        connections = list(_CACHE.values())
        _CACHE.clear()
    for connection in connections:
        try:
            connection.close()
        except Exception:
            pass
