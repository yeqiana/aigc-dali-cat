"""Process-local cache for Episode state authority documents.

The cache is intentionally scoped to one Python process.  It removes repeated
reads of the same authority document during a single runtime step while keeping
the existing MySQL/file authority semantics unchanged.  Writers must invalidate
the Episode after a successful (or partially completed) write.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import threading


_CACHE: dict[tuple[str, str], tuple[object, str, object]] = {}
_LOCK = threading.RLock()


def _key(ep: str | Path, mode: str) -> tuple[str, str]:
    return (str(Path(ep).resolve()), str(mode or "").strip().lower())


def get(ep: str | Path, mode: str, stamp=None) -> tuple[object, str] | None:
    """Return a deep-copied cached ``(data, source)`` pair, if present.

    ``stamp`` is the caller's current file stamp.  Entries stored with a stamp
    (file-backed reads) are ignored once the file no longer matches, so an
    external write is visible without an explicit ``invalidate()``.  Entries
    stored without one (MySQL authority reads) keep the documented
    single-process staleness boundary.
    """
    key = _key(ep, mode)
    with _LOCK:
        row = _CACHE.get(key)
        if row is None:
            return None
        data, source, stored_stamp = row
        if stored_stamp is not None and stamp != stored_stamp:
            return None
        return deepcopy(data), str(source)


def put(ep: str | Path, mode: str, data: object, source: str, stamp=None) -> None:
    """Store a deep copy of one authority result.

    ``stamp`` records which file revision produced a file-backed result.  Pass
    ``None`` for MySQL authority results, whose cross-process freshness is
    outside this cache's scope.
    """
    key = _key(ep, mode)
    with _LOCK:
        _CACHE[key] = (deepcopy(data), str(source), stamp)


def invalidate(ep: str | Path) -> None:
    """Invalidate every mode-specific entry for one resolved Episode."""
    episode = str(Path(ep).resolve())
    with _LOCK:
        for key in [item for item in _CACHE if item[0] == episode]:
            _CACHE.pop(key, None)


def clear() -> None:
    """Clear all cached Episode documents."""
    with _LOCK:
        _CACHE.clear()


def reset() -> None:
    """Alias for explicit test/step teardown."""
    clear()


def cached_entry_count() -> int:
    with _LOCK:
        return len(_CACHE)
