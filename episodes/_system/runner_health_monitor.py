#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.7 runner health checks."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import runner_state_store


def _parse_time(value: str):
    return dt.datetime.fromisoformat(value)


def check(episode: Path, heartbeat_timeout: int = 120) -> dict:
    state = runner_state_store.load(episode)
    heartbeat = state.get("heartbeat")
    status = "UNKNOWN"
    terminal={"COMPLETED","HOST_WAIT","CAPABILITY_WAIT","HUMAN_REQUIRED","HARD_STOP","YIELDED"}
    if state.get("status") in terminal:
        status=state["status"]
    elif heartbeat:
        try:
            stamp=_parse_time(heartbeat)
            if stamp.tzinfo is None: stamp=stamp.replace(tzinfo=dt.timezone.utc)
            age=(dt.datetime.now(dt.timezone.utc)-stamp).total_seconds()
            status="HEALTHY" if 0<=age<=heartbeat_timeout else "RECOVERY_REQUIRED"
        except (ValueError,TypeError): status="RECOVERY_REQUIRED"
    return {
        "episode": str(episode),
        "status": status,
        "runner_status": state.get("status"),
        "stage": state.get("state") or state.get("stage"),
    }
