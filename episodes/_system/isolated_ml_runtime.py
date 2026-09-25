#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run Torch-heavy local vision workers outside the repository-root import scope.

StoryOS intentionally has a top-level platform package. When Python starts
from the repository root, that package shadows the stdlib platform module
that PyTorch imports. Heavy ML workers therefore execute with cwd under the
git-ignored .storyos_cache tree and communicate through one JSON stdin/stdout
message. The StoryOS resident process remains free of Torch/Transformers state.
"""
from __future__ import annotations

import json
import os
import subprocess
import atexit
import queue
import threading
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKDIR = ROOT / ".storyos_cache" / "ml-runtime"
VENV_PYTHON = ROOT / ".storyos_cache" / "ml-venv" / "Scripts" / "python.exe"
ML_PYTHON_ENV = "STORY_OS_ML_PYTHON"

_WORKERS: dict[str, dict] = {}
_WORKERS_GUARD = threading.Lock()


def _clean_pythonpath(env: dict[str, str]) -> dict[str, str]:
    raw = env.get("PYTHONPATH", "")
    if not raw:
        return env
    kept = []
    for entry in raw.split(os.pathsep):
        if not entry:
            continue
        try:
            resolved = Path(entry).resolve()
        except Exception:
            kept.append(entry)
            continue
        if resolved == ROOT.resolve():
            continue
        kept.append(entry)
    env["PYTHONPATH"] = os.pathsep.join(kept)
    return env


def python_executable() -> Path:
    raw = os.environ.get(ML_PYTHON_ENV)
    if raw:
        path = Path(raw).resolve()
        if path.is_file():
            return path
    if VENV_PYTHON.is_file():
        return VENV_PYTHON.resolve()
    return Path(sys.executable).resolve()


def _start_worker(script: Path) -> dict:
    WORKDIR.mkdir(parents=True, exist_ok=True)
    env = _clean_pythonpath(dict(os.environ))
    process = subprocess.Popen(
        [str(python_executable()), str(script), "--isolated-server"],
        cwd=str(WORKDIR),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env,
    )
    return {"process": process, "lock": threading.Lock()}


def _worker(script: Path) -> dict:
    key = str(Path(script).resolve())
    with _WORKERS_GUARD:
        row = _WORKERS.get(key)
        if row is None or row["process"].poll() is not None:
            row = _start_worker(Path(key))
            _WORKERS[key] = row
        return row


def _readline_with_timeout(stream, timeout: int) -> str | None:
    result: queue.Queue[str] = queue.Queue(maxsize=1)
    thread = threading.Thread(target=lambda: result.put(stream.readline()), daemon=True)
    thread.start()
    try:
        return result.get(timeout=max(1, int(timeout)))
    except queue.Empty:
        return None


def call(script: Path, payload: dict, *, timeout: int = 180) -> dict:
    script = Path(script).resolve()
    if not script.is_file():
        return {"status": "FAILED", "diagnostic_only": True, "reason": "WORKER_SCRIPT_MISSING"}
    row = _worker(script)
    process = row["process"]
    with row["lock"]:
        try:
            if process.stdin is None or process.stdout is None:
                raise RuntimeError("isolated worker pipes unavailable")
            process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
            process.stdin.flush()
            line = _readline_with_timeout(process.stdout, timeout)
            if line is None:
                process.kill()
                with _WORKERS_GUARD:
                    _WORKERS.pop(str(script), None)
                return {"status": "FAILED", "diagnostic_only": True, "reason": "ISOLATED_WORKER_TIMEOUT"}
            if not line.strip():
                code = process.poll()
                return {
                    "status": "FAILED",
                    "diagnostic_only": True,
                    "reason": f"ISOLATED_WORKER_CLOSED rc={code}",
                }
            data = json.loads(line)
            if not isinstance(data, dict):
                raise ValueError("worker returned non-object JSON")
            return data
        except Exception as exc:
            return {
                "status": "FAILED",
                "diagnostic_only": True,
                "reason": f"ISOLATED_WORKER_ERROR: {type(exc).__name__}: {exc}",
            }


def serve(handler) -> None:
    """Serve newline-delimited JSON requests in an isolated provider process."""
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError("payload must be an object")
            result = handler(payload)
            if not isinstance(result, dict):
                raise ValueError("handler must return an object")
        except Exception as exc:
            result = {
                "status": "FAILED",
                "diagnostic_only": True,
                "reason": f"ISOLATED_HANDLER_ERROR: {type(exc).__name__}: {exc}",
            }
        print(json.dumps(result, ensure_ascii=False), flush=True)


def shutdown_all() -> None:
    with _WORKERS_GUARD:
        rows = list(_WORKERS.values())
        _WORKERS.clear()
    for row in rows:
        process = row.get("process")
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except Exception:
                pass


atexit.register(shutdown_all)
