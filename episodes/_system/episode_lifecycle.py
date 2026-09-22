#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Orthogonal Episode disposition lifecycle stored in episode-state.json.

Canonical production stage remains ``current_state``.  ``disposition`` only
answers whether the Episode is still writable/eligible for execution.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import story_json
import episode_state_persistence

STATE_REL = Path("meta/episode-state.json")
ACTIVE = "ACTIVE"
TERMINAL = frozenset({"VOIDED", "ABANDONED"})
VALID = frozenset({ACTIVE, *TERMINAL})


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def state(ep: Path) -> dict:
    return episode_state_persistence.load(Path(ep).resolve()) or {}


def disposition(ep: Path) -> str:
    raw = str(state(ep).get("disposition") or ACTIVE).upper()
    return raw if raw in VALID else raw


def is_terminal(ep: Path) -> bool:
    return disposition(ep) in TERMINAL


def assert_writable(ep: Path, operation: str = "write") -> None:
    current = disposition(ep)
    if current in TERMINAL:
        raise RuntimeError(f"EPISODE_TERMINATED: disposition={current}; operation={operation}")
    if current != ACTIVE:
        raise RuntimeError(f"EPISODE_DISPOSITION_INVALID: {current}")


def terminate(ep: Path, *, target: str, source: str, reason: str) -> dict:
    ep = Path(ep).resolve()
    target = str(target or "").upper().strip()
    source = str(source or "").strip()
    reason = str(reason or "").strip()
    if target not in TERMINAL:
        raise ValueError(f"terminal disposition must be one of {sorted(TERMINAL)}")
    if not source or not reason:
        raise ValueError("termination source and reason are required")
    data = state(ep)
    if not data:
        raise ValueError("Episode state authority missing")
    current = str(data.get("disposition") or ACTIVE).upper()
    if current in TERMINAL:
        raise ValueError(f"episode already terminated: {current}")
    if current != ACTIVE:
        raise ValueError(f"invalid current disposition: {current}")
    at = now()
    return episode_state_persistence.update_disposition(
        ep,
        data,
        target=target,
        source=source,
        reason=reason,
        at=at,
    )
