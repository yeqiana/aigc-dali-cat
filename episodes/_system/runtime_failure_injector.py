#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.7 smoke failure injector.

Only used by runtime regression tests. It never changes production state.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InjectedFailure:
    frame: str
    failure_type: str
    expected_category: str
    expected_action: str


FAILURES = {
    "FRAME_03": InjectedFailure("FRAME_03", "IMAGE_TIMEOUT", "TECH_FAILED", "RETRY"),
    "FRAME_07": InjectedFailure("FRAME_07", "PROVIDER_502", "TECH_FAILED", "RETRY"),
    "FRAME_12": InjectedFailure("FRAME_12", "VISUAL_GATE_FAIL", "CONTENT_FAILED", "REPAIR"),
    "FRAME_18": InjectedFailure("FRAME_18", "PROCESS_CRASH", "HUMAN_REQUIRED", "PAUSE"),
}


def get_failure(frame: str) -> InjectedFailure | None:
    return FAILURES.get(frame)


def self_test() -> None:
    assert get_failure("FRAME_03").expected_action == "RETRY"
    assert get_failure("FRAME_12").expected_action == "REPAIR"
    assert get_failure("FRAME_18").failure_type == "PROCESS_CRASH"
    print("RUNTIME FAILURE INJECTOR SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
