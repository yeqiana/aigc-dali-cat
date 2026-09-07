#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.7 mock runtime DAG for autonomous smoke testing.

This module is isolated from production runtime. It validates lifecycle,
checkpoint and recovery orchestration only.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MockFrameResult:
    frame: str
    status: str
    event: str


FRAMES = [f"FRAME_{i:02d}" for i in range(1, 21)]


def execute_frame(frame: str, injected_failure=None) -> MockFrameResult:
    if injected_failure:
        if injected_failure.failure_type in {"IMAGE_TIMEOUT", "PROVIDER_502"}:
            return MockFrameResult(frame, "RETRY", injected_failure.failure_type)
        if injected_failure.failure_type == "VISUAL_GATE_FAIL":
            return MockFrameResult(frame, "REPAIR", injected_failure.failure_type)
        if injected_failure.failure_type == "PROCESS_CRASH":
            return MockFrameResult(frame, "RESUME", injected_failure.failure_type)
    return MockFrameResult(frame, "SUCCESS", "TASK_SUCCESS")


def run_smoke(injector):
    results = []
    for frame in FRAMES:
        results.append(execute_frame(frame, injector(frame)))
    return results


def self_test():
    assert len(FRAMES) == 20
    assert execute_frame("FRAME_01").status == "SUCCESS"
    print("MOCK RUNTIME DAG SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
