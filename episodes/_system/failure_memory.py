#!/usr/bin/env python3
"""Append-only Production Failure Memory shared by production and repair flows."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
import story_json

ROOT = Path(__file__).resolve().parents[2]
REL = Path("reports/production-failure-memory.json")
REQUIRED = ("failure_type", "frame_id", "prompt_issue", "visual_issue", "identity_issue", "repair_action", "final_result")
FAILURE_TYPES = (
    "identity_failure",
    "composition_failure",
    "story_failure",
    "technical_failure",
    "realism_failure",
)


def _failure_type_for_task(task: dict) -> str:
    """Map an existing repair task to a governed learning category."""
    category = str((task or {}).get("category") or "")
    if category == "identity":
        return "identity_failure"
    if category == "semantic":
        return "story_failure"
    if category == "asset_failure":
        return "realism_failure"
    return "technical_failure"

def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def load(root: Path = ROOT) -> dict:
    path = Path(root) / REL
    data = story_json.read_json(path, default={"schema_version": 1, "records": []}) or {}
    data.setdefault("schema_version", 1); data.setdefault("records", [])
    return data

def record(entry: dict, *, root: Path = ROOT) -> dict:
    missing = [k for k in REQUIRED if k not in entry]
    if missing: raise ValueError("failure memory missing: " + ", ".join(missing))
    if entry.get("failure_type") not in FAILURE_TYPES:
        raise ValueError("unsupported failure_type: " + str(entry.get("failure_type")))
    if not str(entry.get("final_result") or "").strip():
        raise ValueError("failure memory final_result is required")
    data = load(root); row = {k: entry.get(k) for k in REQUIRED}
    row.update({"recorded_at": now(), "source": entry.get("source", "runtime")})
    data["records"].append(row); story_json.write_json(Path(root) / REL, data)
    return row


def record_repair_outcome(task: dict, *, final_result: str, root: Path = ROOT,
                          prompt_issue: str = "", visual_issue: str = "",
                          identity_issue: str = "") -> dict:
    """Close a planned repair with its observed terminal result.

    Planning a repair must not create a successful learning record.  The runtime
    or human repair owner calls this only after the actual result is known.
    """
    task = task or {}
    return record({
        "failure_type": _failure_type_for_task(task),
        "frame_id": str(task.get("target") or "episode"),
        "prompt_issue": prompt_issue,
        "visual_issue": visual_issue or "; ".join(task.get("messages") or []),
        "identity_issue": identity_issue,
        "repair_action": str(task.get("action") or "manual_review"),
        "final_result": final_result,
        "source": "repair_engine_terminal_outcome",
    }, root=root)

def guidance(*, failure_type: str | None = None, root: Path = ROOT) -> list[dict]:
    rows = load(root).get("records") or []
    return [r for r in rows if not failure_type or r.get("failure_type") == failure_type][-10:]
