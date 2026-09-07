#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.7 runtime resume token.

Recovery metadata only. It never replaces episode-state.json as stage authority.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

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
    path = episode / REL
    path.parent.mkdir(parents=True, exist_ok=True)
    from runtime_atomic_store import atomic_write_json
    atomic_write_json(path,payload)


def load(episode: Path) -> dict:
    path = episode / REL
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


if __name__ == "__main__":
    print("RUNTIME RESUME TOKEN READY")
