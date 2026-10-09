"""FileLock fail-closed handling of Windows lock sharing races."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
sys.path.insert(0, str(SYSTEM))

import runtime_atomic_store as store


def _denied() -> PermissionError:
    error = PermissionError(13, "Access is denied")
    error.winerror = 5
    return error


def test_permission_denial_without_proven_lock_never_retries(tmp_path):
    target = tmp_path / "not_writable.json"
    lock = store.FileLock(target, timeout=0.2)
    with patch.object(store.os, "open", side_effect=_denied()) as open_fn:
        with pytest.raises(PermissionError):
            lock.acquire()
    assert open_fn.call_count == 1
    assert lock.fd is None
    assert not lock.lock_path.exists()


def test_windows_lock_sharing_denial_retries_existing_owner(tmp_path):
    target = tmp_path / "already_locked.json"
    lock = store.FileLock(target, timeout=0.35, stale_seconds=3600)
    lock.lock_path.write_text("existing lock", encoding="utf-8")
    with patch.object(store.os, "open", side_effect=_denied()) as open_fn, \
            patch.object(store, "_win32_existing_lock_contention", return_value=True):
        with pytest.raises(TimeoutError, match="runtime lock timeout"):
            lock.acquire()
    assert open_fn.call_count >= 2
    assert lock.lock_path.read_text(encoding="utf-8") == "existing lock"


def test_windows_lock_denial_is_not_interpreted_as_free_lock(tmp_path):
    target = tmp_path / "permission_denied.json"
    lock = store.FileLock(target, timeout=0.2)
    lock.lock_path.write_text("existing lock", encoding="utf-8")
    with patch.object(store.os, "open", side_effect=_denied()), \
            patch.object(store, "_win32_existing_lock_contention", return_value=False):
        with pytest.raises(PermissionError):
            lock.acquire()
    assert lock.lock_path.exists()
    assert lock.fd is None
