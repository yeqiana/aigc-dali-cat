#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical Story OS action executor roles.

Runtime roles describe who owns an action. Workspace providers such as WebCodex
describe how the WORK host accesses the repository. Provider names must never
appear as action executors or Episode authority identities.
"""
from __future__ import annotations

from typing import Any

WORK = "WORK"
CODEX_IMAGE = "CODEX_IMAGE"
CODEX_VISION = "CODEX_VISION"
MACHINE = "MACHINE"
EXTERNAL = "EXTERNAL"

EXECUTOR_ROLES = frozenset({WORK, CODEX_IMAGE, CODEX_VISION, MACHINE, EXTERNAL})


def validate(executor: Any, *, allow_none: bool = False) -> str | None:
    if executor is None:
        if allow_none:
            return None
        raise ValueError("action executor is required")
    value = str(executor).strip().upper()
    if value not in EXECUTOR_ROLES:
        raise ValueError(
            f"unsupported action executor {executor!r}; expected one of "
            + ", ".join(sorted(EXECUTOR_ROLES))
        )
    return value


def validate_action(action: Any) -> dict:
    if not isinstance(action, dict):
        raise ValueError("next action must be an object")
    executor = action.get("executor")
    work_pending = bool(action.get("work_pending"))
    if executor is None:
        if work_pending:
            raise ValueError("pending next action requires a canonical executor")
        return action
    validate(executor)
    return action


def self_test() -> None:
    for role in EXECUTOR_ROLES:
        assert validate(role.lower()) == role
    for forbidden in ("DEVSPACE", "WEBCODEX", "WEB", "CODEX", "WORK_ISOLATED"):
        try:
            validate(forbidden)
        except ValueError:
            pass
        else:
            raise AssertionError(f"provider/legacy role leaked into executor contract: {forbidden}")
    validate_action({"action": "COMPLETE", "executor": None, "work_pending": False})


if __name__ == "__main__":
    self_test()
    print("RUNTIME EXECUTOR ROLE SELF-TEST PASS")
