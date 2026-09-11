#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Episode Observation Ledger.

One append-only JSONL row per observation snapshot. The ledger records the
Shadow Observation lifecycle of a single advisor run:

    OBSERVED -> FEEDBACK_PENDING -> COMPLETED

A transition appends a new full snapshot; the latest row per ``observation_id``
wins, so the full history stays readable and nothing is ever rewritten.

Frozen boundaries:
- derived, never authority: it never grants PASS and never replaces
  ``meta/episode-state.json`` or ``meta/story-gates.json``;
- written only when a human runs the observation runner or the feedback entry,
  never by the production Runtime;
- no score of any kind: status, references and free text only;
- a broken row is reported by ``scan_ledger`` and never raises.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .schema import (
    AUTHORITY,
    OBSERVATION_STATUSES,
    OBSERVATION_STATUS_COMPLETED,
    OBSERVATION_STATUS_FEEDBACK_PENDING,
    OBSERVATION_STATUS_OBSERVED,
    require_valid,
    validate_observation_record,
)

DEFAULT_LEDGER_PATH = Path("reports") / "pre-production" / "observation-ledger.jsonl"
STATUS_ORDER = {status: index for index, status in enumerate(OBSERVATION_STATUSES)}
_SNAPSHOT_FIELDS = ("observation_status", "creator_feedback_reference",
                    "production_outcome", "learning_summary")


def _stamp(stamp: str | None = None) -> str:
    return stamp or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _digest(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def observation_id(episode_id: str, advisor_report_reference: str) -> str:
    """Stable id for one observed advisor run: episode + advisor report revision."""
    return "OBS-" + (str(episode_id) or "unknown") + "-" + _digest(advisor_report_reference)[:8]


def build_observation(episode_id: str, *, story_dna_reference: str = "",
                      advisor_report_reference: str = "",
                      observation_status: str = OBSERVATION_STATUS_OBSERVED,
                      creator_feedback_reference=None, production_outcome=None,
                      learning_summary: str = "", created_at=None) -> dict:
    """Build one Episode Observation Record (default status OBSERVED)."""
    stamp = _stamp(created_at)
    return {
        "schema": "episode_observation",
        "schema_version": 1,
        "observation_id": observation_id(episode_id, advisor_report_reference),
        "episode_id": str(episode_id or ""),
        "story_dna_reference": str(story_dna_reference or ""),
        "advisor_report_reference": str(advisor_report_reference or ""),
        "observation_status": observation_status,
        "creator_feedback_reference": creator_feedback_reference,
        "production_outcome": production_outcome,
        "learning_summary": str(learning_summary or ""),
        "created_time": stamp,
        "updated_time": stamp,
        "advisory_only": True,
        "blocks_production": False,
        "authority": AUTHORITY,
    }


def scan_ledger(path) -> tuple:
    """Return (raw rows, malformed line reports). Never raises."""
    file_path = Path(path)
    if not file_path.is_file():
        return [], []
    rows: list = []
    malformed: list = []
    for number, raw in enumerate(file_path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception as exc:
            malformed.append({"line": number, "error": type(exc).__name__})
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            malformed.append({"line": number, "error": "not_an_object"})
    return rows, malformed


def collapse_latest(rows) -> dict:
    """Latest snapshot per observation_id, keyed by observation_id."""
    latest: dict = {}
    for row in rows:
        oid = str(row.get("observation_id") or "")
        if oid:
            latest[oid] = row
    return latest


def read_records(path) -> list:
    """Latest snapshot per observation_id, ordered by episode then id."""
    latest = collapse_latest(scan_ledger(path)[0])
    return sorted(latest.values(), key=lambda row: (str(row.get("episode_id") or ""),
                                                    str(row.get("observation_id") or "")))


def find_record(path, oid: str) -> dict | None:
    return collapse_latest(scan_ledger(path)[0]).get(str(oid))


def _write(path, record: dict) -> dict:
    require_valid(validate_observation_record(record), "episode_observation")
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    rows, _ = scan_ledger(file_path)
    return {"status": "APPENDED", "record": record, "path": str(file_path), "rows": len(rows)}


def _unchanged(previous: dict | None, record: dict) -> bool:
    if previous is None:
        return False
    return all(previous.get(field) == record.get(field) for field in _SNAPSHOT_FIELDS)


def append_record(path, record: dict) -> dict:
    """Append one observation snapshot, skipping a no-op repeat of the latest one."""
    previous = find_record(path, record.get("observation_id"))
    if _unchanged(previous, record):
        return {"status": "REUSED", "record": previous, "path": str(Path(path)),
                "rows": len(scan_ledger(path)[0])}
    return _write(path, record)


def transition(path, oid: str, status: str, *, creator_feedback_reference=...,
               production_outcome=..., learning_summary=..., updated_at=None) -> dict:
    """Append a new lifecycle snapshot for an existing observation.

    Forward-only: the status may stay or move to a later stage, never backwards.
    Pass ``...`` (the default) to keep a field unchanged; pass ``None`` to clear it.
    """
    if status not in OBSERVATION_STATUSES:
        raise ValueError("unknown observation_status: " + str(status))
    current = find_record(path, oid)
    if current is None:
        raise ValueError("unknown observation_id: " + str(oid))
    if STATUS_ORDER[status] < STATUS_ORDER[str(current.get("observation_status"))]:
        raise ValueError("cannot move observation backwards to " + str(status))

    updated = dict(current)
    updated["observation_status"] = status
    if creator_feedback_reference is not ...:
        updated["creator_feedback_reference"] = creator_feedback_reference
    if production_outcome is not ...:
        updated["production_outcome"] = production_outcome
    if learning_summary is not ...:
        updated["learning_summary"] = str(learning_summary or "")
    updated["updated_time"] = _stamp(updated_at)
    return append_record(path, updated)


def mark_feedback_pending(path, oid: str, **changes) -> dict:
    """Move an observation to FEEDBACK_PENDING (waiting for a human)."""
    return transition(path, oid, OBSERVATION_STATUS_FEEDBACK_PENDING, **changes)


def complete_observation(path, oid: str, *, creator_feedback_reference=None,
                         production_outcome=None, learning_summary=None, updated_at=None) -> dict:
    """Close an observation once a human judgement (and outcome) is recorded."""
    return transition(path, oid, OBSERVATION_STATUS_COMPLETED,
                      creator_feedback_reference=creator_feedback_reference,
                      production_outcome=production_outcome,
                      learning_summary=learning_summary if learning_summary is not None else "",
                      updated_at=updated_at)


def index_by_episode(records) -> dict:
    out: dict = {}
    for record in records:
        out.setdefault(str(record.get("episode_id") or ""), []).append(record)
    return out


def summarize(records) -> dict:
    """Real counts over recorded observations; no score of any kind."""
    by_status: dict = {}
    for record in records:
        status = str(record.get("observation_status"))
        by_status[status] = by_status.get(status, 0) + 1
    stamps = sorted(str(record.get("updated_time") or "") for record in records if record.get("updated_time"))
    return {
        "observations": len(records),
        "episodes": len({str(record.get("episode_id") or "") for record in records}),
        "with_feedback": len([r for r in records if r.get("creator_feedback_reference")]),
        "by_status": by_status,
        "latest_updated_at": stamps[-1] if stamps else None,
        "authority": AUTHORITY,
    }


__all__ = [
    "DEFAULT_LEDGER_PATH",
    "STATUS_ORDER",
    "append_record",
    "build_observation",
    "collapse_latest",
    "complete_observation",
    "find_record",
    "index_by_episode",
    "mark_feedback_pending",
    "observation_id",
    "read_records",
    "scan_ledger",
    "summarize",
    "transition",
]

