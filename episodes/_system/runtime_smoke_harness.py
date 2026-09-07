#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.7 runtime smoke harness.

Regression harness for autonomous runner lifecycle.
It validates orchestration behavior only; it does not bypass stage authority.
"""
from __future__ import annotations

import json
from pathlib import Path


FAILURE_MATRIX = {
    "FRAME_03": "IMAGE_TIMEOUT",
    "FRAME_07": "PROVIDER_502",
    "FRAME_12": "VISUAL_GATE_FAIL",
    "FRAME_18": "PROCESS_CRASH",
}


def build_case() -> dict:
    return {
        "episode": "MOCK_RUNTIME_EP001",
        "frames": 20,
        "parallel": 5,
        "failure_injection": True,
        "failures": FAILURE_MATRIX,
    }


def write_case(path: Path) -> None:
    path.write_text(
        json.dumps(build_case(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def self_test() -> None:
    case = build_case()
    assert case["frames"] == 20
    assert case["parallel"] == 5
    assert case["failures"]["FRAME_18"] == "PROCESS_CRASH"
    print("RUNTIME SMOKE HARNESS SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
