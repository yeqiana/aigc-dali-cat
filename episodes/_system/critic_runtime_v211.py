#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1.1 critic infrastructure status + circuit breaker.

Technical availability is isolated from content judgment. Speculative production is
allowed only when the latest technical event belongs to the latest Visual Lock run.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
from pathlib import Path

REL = Path("meta/visual-critic-runtime.json")
EP_PERF_REL = Path("meta/episode-performance-ledger.json")
TECHNICAL_CODES = {
    "INPUT_IMAGES_UNAVAILABLE",
    "CRITIC_PROCESS_ERROR",
    "CRITIC_OUTPUT_MISSING",
    "CRITIC_TIMEOUT",
    "WINDOWS_SANDBOX_1385",
    "VISION_ATTACHMENT_UNAVAILABLE",
    "CRITIC_BACKEND_UNAVAILABLE",
}
OPEN_AFTER = 2


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(path)


def load(ep: Path) -> dict:
    p = Path(ep).resolve() / REL
    if not p.is_file():
        return {
            "schema_version": 2,
            "status": "UNKNOWN",
            "consecutive_technical_failures": 0,
            "last_fingerprint": None,
            "events": [],
            "speculative_production_allowed": False,
        }
    return read_json(p)


def latest_visual_lock_run(ep: Path) -> dict | None:
    p = Path(ep).resolve() / EP_PERF_REL
    if not p.is_file():
        return None
    try:
        d = read_json(p)
    except Exception:
        return None
    runs = (((d.get("stages") or {}).get("VISUAL_LOCK") or {}).get("runs") or [])
    if not runs:
        return None
    row = runs[-1]
    return row if isinstance(row, dict) else None


def current_visual_lock_run_id(ep: Path) -> str | None:
    row = latest_visual_lock_run(ep)
    return str(row.get("run_id")) if row and row.get("run_id") else None


def classify_issue_codes(codes) -> list[str]:
    out = []
    for raw in codes or []:
        code = str(raw or "").strip().upper()
        if not code:
            continue
        if code in TECHNICAL_CODES or any(token in code for token in (
            "INPUT_IMAGE", "ATTACHMENT_UNAVAILABLE", "SANDBOX", "BACKEND_UNAVAILABLE",
            "CRITIC_TIMEOUT", "VISION_UNAVAILABLE"
        )):
            out.append(code)
    return sorted(set(out))


def classify_log_text(text: str) -> list[str]:
    low = str(text or "").lower()
    codes = []
    if "input_images_unavailable" in low or "input images unavailable" in low:
        codes.append("INPUT_IMAGES_UNAVAILABLE")
    if "createprocesswithlogonw" in low or "failed: 1385" in low or "error 1385" in low:
        codes.append("WINDOWS_SANDBOX_1385")
    if "attachment" in low and ("unavailable" in low or "cannot" in low or "can't" in low):
        codes.append("VISION_ATTACHMENT_UNAVAILABLE")
    if "timed out" in low or "timeout" in low:
        codes.append("CRITIC_TIMEOUT")
    return sorted(set(codes))


def _fingerprint(codes: list[str]) -> str:
    raw = "|".join(sorted(set(codes))).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _run_binding(ep: Path) -> dict:
    row = latest_visual_lock_run(ep) or {}
    return {
        "visual_lock_run_id": row.get("run_id"),
        "visual_lock_started_at": row.get("started_at"),
    }


def record_technical_failure(ep: Path, *, issue_codes, attempt: int,
                             log: str | None = None, source: str = "visual_lock_critic") -> dict:
    ep = Path(ep).resolve()
    codes = classify_issue_codes(issue_codes)
    if not codes:
        codes = ["CRITIC_BACKEND_UNAVAILABLE"]
    fp = _fingerprint(codes)
    binding = _run_binding(ep)
    data = load(ep)
    prev_fp = data.get("last_fingerprint")
    prev_run = data.get("last_visual_lock_run_id")
    same_run = prev_run == binding.get("visual_lock_run_id") and prev_run is not None
    consecutive = int(data.get("consecutive_technical_failures") or 0)
    consecutive = consecutive + 1 if same_run and prev_fp == fp else 1
    status = "CIRCUIT_OPEN" if consecutive >= OPEN_AFTER else "TECHNICAL_BLOCKED"
    event = {
        "at": now(), "source": source, "attempt": int(attempt or 1),
        "issue_codes": codes, "fingerprint": fp, "status": status, "log": log,
        **binding,
    }
    events = list(data.get("events") or [])
    events.append(event)
    data.update({
        "schema_version": 2,
        "status": status,
        "consecutive_technical_failures": consecutive,
        "last_fingerprint": fp,
        "last_issue_codes": codes,
        "last_event_at": event["at"],
        "last_visual_lock_run_id": binding.get("visual_lock_run_id"),
        "speculative_production_allowed": True,
        "events": events[-20:],
    })
    write_json(ep / REL, data)
    return data


def record_content_result(ep: Path, *, passed: bool, attempt: int,
                          issue_codes=None, log: str | None = None) -> dict:
    ep = Path(ep).resolve()
    binding = _run_binding(ep)
    data = load(ep)
    event = {
        "at": now(), "source": "visual_lock_critic", "attempt": int(attempt or 1),
        "issue_codes": list(issue_codes or []),
        "status": "AVAILABLE_PASS" if passed else "AVAILABLE_CONTENT_FAIL", "log": log,
        **binding,
    }
    events = list(data.get("events") or [])
    events.append(event)
    data.update({
        "schema_version": 2,
        "status": event["status"],
        "consecutive_technical_failures": 0,
        "last_fingerprint": None,
        "last_issue_codes": list(issue_codes or []),
        "last_event_at": event["at"],
        "last_visual_lock_run_id": binding.get("visual_lock_run_id"),
        "speculative_production_allowed": False,
        "events": events[-20:],
    })
    write_json(ep / REL, data)
    return data


def speculative_allowed(ep: Path, *, require_current_run: bool = True) -> bool:
    ep = Path(ep).resolve()
    d = load(ep)
    base = d.get("status") in {"TECHNICAL_BLOCKED", "CIRCUIT_OPEN"} and d.get("speculative_production_allowed") is True
    if not base:
        return False
    if not require_current_run:
        return True
    current = current_visual_lock_run_id(ep)
    recorded = d.get("last_visual_lock_run_id")
    return bool(current and recorded and current == recorded)


def self_test() -> None:
    assert classify_issue_codes(["INPUT_IMAGES_UNAVAILABLE"]) == ["INPUT_IMAGES_UNAVAILABLE"]
    assert "WINDOWS_SANDBOX_1385" in classify_log_text("CreateProcessWithLogonW failed: 1385")
    print("CRITIC RUNTIME V2.1.1 R2 SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
