#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.7 runner health checks.

This module is a **projection of runner lifecycle evidence only**. It reads what a
runner wrote to meta/runtime-runner-state.json and reports it. It never starts,
stops, restarts, signals or waits on a runner, and it holds no lock. There is no
watchdog here by design: an idle host loop is a fact to be surfaced at every read
site, never a condition this module acts on.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import runner_state_store


def _parse_time(value: str):
    return dt.datetime.fromisoformat(value)


def check(episode: Path, heartbeat_timeout: int = 120, *, work_pending: bool | None = None) -> dict:
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
    # HOST_WAIT is in the terminal set and an expired heartbeat yields
    # RECOVERY_REQUIRED: both mean nobody is running the host loop right now.
    # That is the whole point of the projection -- HEALTHY is the only status
    # that proves a live loop, so everything else reads IDLE.
    host_loop = "RUNNING" if status == "HEALTHY" else "IDLE"
    out = {
        "episode": str(episode),
        "status": status,
        "runner_status": state.get("status"),
        "stage": state.get("state") or state.get("stage"),
        "host_loop": host_loop,
        "host_loop_source": "meta/runtime-runner-state.json",
    }
    if work_pending is not None:
        # Reported, never acted on. There is no recovery trigger in this module.
        out["orphaned_pending_work"] = bool(work_pending and host_loop != "RUNNING")
    return out
