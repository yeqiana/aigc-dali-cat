#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.7 runtime smoke execution adapter.

Connects smoke cases with the autonomous runner boundary.
This adapter prepares execution metadata only; it does not bypass runtime gates.
"""
from __future__ import annotations

import json
from pathlib import Path

from runtime_failure_injector import get_failure


def build_execution_case(episode: str = "MOCK_RUNTIME_EP001") -> dict:
    return {
        "episode": episode,
        "frames": [f"FRAME_{i:02d}" for i in range(1, 21)],
        "parallel": 5,
        "failure_injection": True,
        "failures": {
            frame: get_failure(frame).failure_type
            for frame in ["FRAME_03", "FRAME_07", "FRAME_12", "FRAME_18"]
        },
    }


def write_case(path: Path) -> None:
    path.write_text(
        json.dumps(build_execution_case(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def self_test() -> None:
    case = build_execution_case()
    assert len(case["frames"]) == 20
    assert case["parallel"] == 5
    assert case["failures"]["FRAME_18"] == "PROCESS_CRASH"
    print("RUNTIME SMOKE EXECUTION ADAPTER SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
