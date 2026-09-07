#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.7 daemon event bridge.

Bridges runner lifecycle events into runtime trace evidence.
This is observability only; it does not change episode stage authority.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path


TRACE_REL = Path("meta/runtime/trace-events.jsonl")


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def emit(episode: Path, event: str, **payload) -> dict:
    row = {
        "timestamp": _now(),
        "event": event,
        "episode": str(episode),
        **payload,
    }
    path = episode / TRACE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def self_test(tmp: Path) -> None:
    event = emit(tmp, "RUNNER_STARTED", mode="AUTONOMOUS")
    assert event["event"] == "RUNNER_STARTED"
    assert (tmp / TRACE_REL).exists()


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        self_test(Path(d))
    print("RUNTIME DAEMON EVENT BRIDGE SELF-TEST PASS")
