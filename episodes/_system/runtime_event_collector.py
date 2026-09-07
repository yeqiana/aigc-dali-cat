#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.7 runtime event collector.

Workers emit execution events only. Scheduler owns ledger mutations.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from async_task_runtime import TaskEvent


@dataclass
class RuntimeImageEvent:
    event: str
    item_id: str
    payload: dict[str, Any]


_EVENT_MAP = {
    "TASK_STARTED": "IMAGE_STARTED",
    "TASK_SUCCESS": "IMAGE_SUCCESS",
    "TASK_FAILED": "IMAGE_FAILED",
}


def json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def collect(task_event: TaskEvent) -> RuntimeImageEvent:
    return RuntimeImageEvent(
        event=_EVENT_MAP.get(task_event.event, task_event.event),
        item_id=task_event.task_id,
        payload=task_event.payload,
    )


def self_test() -> None:
    assert collect(TaskEvent("TASK_STARTED", "01", {})).event == "IMAGE_STARTED"
    assert collect(TaskEvent("TASK_SUCCESS", "01", {})).event == "IMAGE_SUCCESS"
    assert collect(TaskEvent("TASK_FAILED", "01", {})).event == "IMAGE_FAILED"
    assert json_safe({"path": Path("a") / "b.png"}) == {"path": "a/b.png"}


if __name__ == "__main__":
    self_test()
    print("RUNTIME EVENT COLLECTOR SELF-TEST PASS")
