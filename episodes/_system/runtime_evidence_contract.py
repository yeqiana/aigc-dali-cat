#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Runtime evidence completeness contract for modern Story OS production runs.

The contract is armed by the resident Runner. Historical Episodes are never
backfilled or fabricated: an Episode is subject to this gate only after it has
actually entered the current Runner and received the marker below.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import story_json
import runtime_observability
import runtime_portability

REL = Path("meta/runtime/runtime-evidence-contract.json")
SCHEMA_VERSION = 1
REQUIRED_SINKS = (
    runtime_observability.EPISODE_PERFORMANCE_REL.as_posix(),
    runtime_observability.TRACE_EVENTS_REL.as_posix(),
    "meta/runtime/node-execution.jsonl",
    "meta/runtime/authority-commit.jsonl",
)
JSONL_SINKS = frozenset(path for path in REQUIRED_SINKS if path.endswith(".jsonl"))


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def arm(ep: Path, *, source: str = "episode_runner") -> dict:
    """Persist the requirement without claiming that any sink already exists."""
    ep = Path(ep).resolve()
    runtime_portability.assert_episode_directory(ep)
    path = ep / REL
    current = story_json.read_json(path, default={}) or {}
    row = {
        "schema_version": SCHEMA_VERSION,
        "contract": "runtime_evidence_complete_before_production_pass",
        "required_sinks": list(REQUIRED_SINKS),
        "armed_at": current.get("armed_at") or now(),
        "last_seen_at": now(),
        "source": str(current.get("source") or source),
        "historical_backfill_allowed": False,
        "gate_pass": None,
        "episode_state_mutated": False,
    }
    story_json.write_json(path, row)
    return row


def required(ep: Path) -> bool:
    return (Path(ep) / REL).is_file()


def _jsonl_valid(path: Path) -> bool:
    rows = [line for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if not rows:
        return False
    try:
        for line in rows:
            value = json.loads(line)
            if not isinstance(value, dict):
                return False
    except (json.JSONDecodeError, OSError, UnicodeError):
        return False
    return True


def verify(ep: Path) -> list[str]:
    """Return missing/invalid sink errors for an armed Episode, else legacy PASS."""
    ep = Path(ep).resolve()
    marker = ep / REL
    if not marker.is_file():
        return []
    try:
        contract = story_json.read_json(marker)
    except Exception as exc:
        return [f"RUNTIME_EVIDENCE_CONTRACT_INVALID:{exc}"]
    if contract.get("historical_backfill_allowed") is not False:
        return ["RUNTIME_EVIDENCE_CONTRACT_BACKFILL_POLICY_INVALID"]
    declared = tuple(contract.get("required_sinks") or ())
    if declared != REQUIRED_SINKS:
        return ["RUNTIME_EVIDENCE_CONTRACT_SINK_SET_DRIFT"]
    errors: list[str] = []
    for rel in REQUIRED_SINKS:
        path = ep / rel
        if not path.is_file() or path.stat().st_size <= 0:
            errors.append(f"RUNTIME_EVIDENCE_MISSING:{rel}")
            continue
        if rel in JSONL_SINKS and not _jsonl_valid(path):
            errors.append(f"RUNTIME_EVIDENCE_INVALID_JSONL:{rel}")
        elif rel.endswith(".json"):
            try:
                value = story_json.read_json(path)
                if not isinstance(value, dict):
                    errors.append(f"RUNTIME_EVIDENCE_INVALID_JSON:{rel}")
            except Exception:
                errors.append(f"RUNTIME_EVIDENCE_INVALID_JSON:{rel}")
    return errors
