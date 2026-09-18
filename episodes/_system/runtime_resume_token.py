#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.7 runtime resume token.

Recovery metadata only. It never replaces episode-state.json as stage authority.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import runtime_workspace
import hot_state_bridge

REL = Path("meta/runtime-resume-token.json")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def save(episode: Path, *, stage: str, step: str, attempt: int,
         failure_category: str | None = None,
         last_event: str | None = None,
         resume_action: str = "CONTINUE") -> None:
    payload = {
        "schema_version": 1,
        "episode": str(episode),
        "stage": stage,
        "step": step,
        "attempt": attempt,
        "failure_category": failure_category,
        "last_event": last_event,
        "resume_action": resume_action,
        "updated_at": now(),
    }
    runtime_workspace.write_json(episode, REL, payload)
    hot_state_bridge.mirror(episode, "RESUME_TOKEN", payload)


def load(episode: Path) -> dict:
    hot = hot_state_bridge.read(episode, "RESUME_TOKEN")
    data = hot_state_bridge.value_or_fallback(
        hot,
        lambda: runtime_workspace.read_json(episode, REL, default={}),
        default={},
    )
    return data if isinstance(data, dict) else {}


if __name__ == "__main__":
    print("RUNTIME RESUME TOKEN READY")
