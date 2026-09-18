#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Episode-local fail-fast circuit breaker for expensive repeated runtime failures."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import runtime_atomic_store as atomic
import hot_state_bridge

REL = Path("meta/runtime/circuit-breaker.json")
HARD_CODES = {
    "MODEL_UNAVAILABLE", "MODEL_REQUIRED_UNAVAILABLE", "AUTH_401",
    "WINDOWS_1385", "SANDBOX_DENIED", "IMAGE_TOOL_UNAVAILABLE",
}

def now_dt():
    return dt.datetime.now(dt.timezone.utc).astimezone()

def now():
    return now_dt().isoformat(timespec="seconds")

def default_state():
    return {"schema_version": 1, "module_version": "2.6.0", "circuits": {}, "updated_at": now()}

def _key(route: str, code: str) -> str:
    return f"{route}:{code}"


def _load_state(ep: Path) -> dict:
    ep = Path(ep).resolve()
    hot = hot_state_bridge.read(ep, "CIRCUIT_BREAKER")
    data = hot_state_bridge.value_or_fallback(
        hot,
        lambda: atomic.read_json(ep / REL, default_state()),
        default=None,
    )
    return data if isinstance(data, dict) else default_state()


def _save_state(ep: Path, data: dict) -> None:
    atomic.atomic_write_json(Path(ep) / REL, data)
    hot_state_bridge.mirror(Path(ep), "CIRCUIT_BREAKER", data)

def record_failure(ep, route: str, code: str, *, threshold: int = 2, cooldown_seconds: int = 900) -> dict:
    ep = Path(ep).resolve()
    code = str(code or "UNKNOWN")
    with atomic.FileLock(ep / REL):
        data = _load_state(ep)
        data.setdefault("circuits", {})
        key = _key(route, code)
        row = data["circuits"].setdefault(key, {"failures": 0, "state": "CLOSED"})
        row["failures"] = int(row.get("failures") or 0) + 1
        row["last_failure_at"] = now()
        row["code"] = code
        row["route"] = route
        if code in HARD_CODES and row["failures"] >= threshold:
            until = now_dt() + dt.timedelta(seconds=cooldown_seconds)
            row["state"] = "OPEN"
            row["open_until"] = until.isoformat(timespec="seconds")
        data["updated_at"] = now()
        _save_state(ep, data)
        return dict(row)

def record_success(ep, route: str) -> None:
    ep = Path(ep).resolve()
    with atomic.FileLock(ep / REL):
        data = _load_state(ep)
        for row in (data.get("circuits") or {}).values():
            if row.get("route") == route:
                row["failures"] = 0
                row["state"] = "CLOSED"
                row["open_until"] = None
        data["updated_at"] = now()
        _save_state(ep, data)

def blocking(ep, route: str) -> dict | None:
    ep = Path(ep).resolve()
    d = _load_state(ep)
    for row in (d.get("circuits") or {}).values():
        if row.get("route") != route or row.get("state") != "OPEN":
            continue
        raw = row.get("open_until")
        try:
            until = dt.datetime.fromisoformat(str(raw))
            if until.tzinfo is None:
                until = until.replace(tzinfo=dt.timezone.utc)
            if now_dt() < until:
                return row
        except Exception:
            return row
    return None

def classify_text(text: str) -> str | None:
    low = str(text or "").lower()
    if "1385" in low: return "WINDOWS_1385"
    if "401" in low or "unauthorized" in low: return "AUTH_401"
    if "model_unavailable" in low or "model unavailable" in low: return "MODEL_UNAVAILABLE"
    if "image tool" in low and ("unavailable" in low or "not available" in low): return "IMAGE_TOOL_UNAVAILABLE"
    if "sandbox" in low and ("denied" in low or "forbidden" in low): return "SANDBOX_DENIED"
    if "network_error" in low or "network error" in low or "error sending request" in low: return "NETWORK_ERROR"
    return None

def self_test():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        assert blocking(ep, "image") is None
        record_failure(ep, "image", "WINDOWS_1385")
        assert blocking(ep, "image") is None
        record_failure(ep, "image", "WINDOWS_1385")
        assert blocking(ep, "image") is not None
        record_success(ep, "image")
        assert blocking(ep, "image") is None
        assert classify_text("NETWORK_ERROR: error sending request") == "NETWORK_ERROR"
    print("RUNTIME CIRCUIT BREAKER V2.6.0 SELF-TEST PASS")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("show"); p.add_argument("episode_dir")
    sub.add_parser("self-test")
    a = ap.parse_args()
    if a.cmd == "self-test": self_test(); return 0
    p = Path(a.episode_dir).resolve() / REL
    print(p.read_text(encoding="utf-8-sig") if p.is_file() else "{}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
