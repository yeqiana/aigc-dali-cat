#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Portable atomic JSON store for Story OS runtime state.

No shell, no PowerShell, no heredoc. Cross-thread/process coordination is done
with an O_EXCL lock file and same-directory os.replace atomic commits.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable, TypeVar

T = TypeVar("T")
_LOCAL_GUARDS: dict[str, threading.RLock] = {}
_LOCAL_GUARDS_LOCK = threading.Lock()

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def _guard(path: Path) -> threading.RLock:
    key = str(path.resolve())
    with _LOCAL_GUARDS_LOCK:
        lock = _LOCAL_GUARDS.get(key)
        if lock is None:
            lock = threading.RLock()
            _LOCAL_GUARDS[key] = lock
        return lock

class FileLock:
    def __init__(self, target: Path, timeout: float = 15.0, stale_seconds: float = 120.0):
        self.target = Path(target)
        self.lock_path = self.target.with_name(self.target.name + ".lock")
        self.timeout = float(timeout)
        self.stale_seconds = float(stale_seconds)
        self.fd: int | None = None

    def acquire(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self.fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                payload = json.dumps({"pid": os.getpid(), "created_at": now()}, ensure_ascii=False).encode("utf-8")
                os.write(self.fd, payload)
                os.fsync(self.fd)
                return
            except FileExistsError:
                try:
                    age = time.time() - self.lock_path.stat().st_mtime
                    if age > self.stale_seconds:
                        self.lock_path.unlink(missing_ok=True)
                        continue
                except OSError:
                    pass
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"runtime lock timeout: {self.lock_path}")
                time.sleep(0.03)

    def release(self) -> None:
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None
        try:
            self.lock_path.unlink(missing_ok=True)
        except OSError:
            pass

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False

def read_json(path: Path, default: T) -> T:
    path = Path(path)
    if not path.is_file():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data
    except Exception:
        return default

def atomic_write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_tmp = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".tmp", dir=str(path.parent))
    tmp = Path(raw_tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(tmp), str(path))
    finally:
        tmp.unlink(missing_ok=True)

def atomic_write_json(path: Path, data: object) -> None:
    atomic_write_text(Path(path), json.dumps(data, ensure_ascii=False, indent=2) + "\n")

def update_json(path: Path, default_factory: Callable[[], dict], mutator: Callable[[dict], T],
                timeout: float = 15.0) -> T:
    path = Path(path)
    local = _guard(path)
    with local:
        with FileLock(path, timeout=timeout):
            current = read_json(path, default_factory())
            if not isinstance(current, dict):
                current = default_factory()
            result = mutator(current)
            atomic_write_json(path, current)
            return result

def self_test() -> None:
    import tempfile as _tmp
    with _tmp.TemporaryDirectory(prefix="story os 原子 测试 ") as td:
        p = Path(td) / "runtime state.json"
        def bump():
            def mutate(d):
                d["n"] = int(d.get("n") or 0) + 1
                return d["n"]
            update_json(p, lambda: {"n": 0}, mutate)
        threads = [threading.Thread(target=lambda: [bump() for _ in range(50)]) for _ in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()
        assert read_json(p, {}).get("n") == 250
        assert not p.with_name(p.name + ".lock").exists()
    print("RUNTIME ATOMIC STORE V2.6.0 SELF-TEST PASS")

def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test()
        return 0
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
