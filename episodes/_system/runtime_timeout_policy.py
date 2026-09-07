#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS timeout policy single source.

Every runtime role that needs a timeout default reads it here, and the YAML
section config/storyos.yaml:timeout_policy is the human-editable authority.
Values equal the historical defaults so behavior does not change until a
deliberate tuning decision is made. Clamp bounds reproduce the two existing
cap semantics (fast frame scout 60..240, speculative image lane 60..600).
"""
from __future__ import annotations

from typing import Any

import storyos_config

# role -> historical default seconds (behavior-preserving baseline).
DEFAULT_SECONDS: dict[str, int] = {
    "codex_supervisor_run": 7200,   # full-chain codex supervisor / DAG run
    "codex_scoped_step": 3600,      # single scoped codex step worker
    "image_worker_request": 600,    # one image backend request
    "image_lane_run": 600,          # scheduler/speculative image lane
    "visual_baseline_critic": 300,  # visual lock baseline critic
    "fast_scout": 240,              # fast frame scout
    "review_critic": 900,           # story/visual/caption review critics
    "image_probe": 900,             # image provider capability probe
    "deep_semantic_review": 1800,   # frame semantic / incremental review
    "release_semantic": 1800,       # recent5 / release critic semantic build
}
REQUIRED_ROLES: tuple[str, ...] = tuple(DEFAULT_SECONDS)

# role -> (min_seconds, max_seconds); absent role means no clamp.
CLAMP_BOUNDS: dict[str, tuple[int, int]] = {
    "fast_scout": (60, 240),
    "image_lane_run": (60, 600),
}


def _policy() -> dict[str, Any]:
    cfg = storyos_config.load_config()
    value = storyos_config.get_path(cfg, "timeout_policy")
    return value if isinstance(value, dict) else {}


def default_seconds(role: str) -> int:
    if role not in DEFAULT_SECONDS:
        raise ValueError(f"unknown timeout role: {role}")
    return DEFAULT_SECONDS[role]


def configured_seconds(role: str) -> int:
    """Resolve role timeout from YAML, falling back to the historical default."""
    if role not in DEFAULT_SECONDS:
        raise ValueError(f"unknown timeout role: {role}")
    value = _policy().get(role, DEFAULT_SECONDS[role])
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"timeout_policy.{role} must be a positive int")
    return value


def seconds(role: str) -> int:
    return configured_seconds(role)


def clamp(role: str, value: int) -> int:
    """Clamp value to the role bounds (identity when role is unbound)."""
    bounds = CLAMP_BOUNDS.get(role)
    if bounds is None:
        return int(value)
    low, high = bounds
    return max(low, min(high, int(value)))


def self_test() -> None:
    cfg = storyos_config.load_config()
    policy = storyos_config.get_path(cfg, "timeout_policy") or {}
    for role in REQUIRED_ROLES:
        assert policy.get(role) == DEFAULT_SECONDS[role], role
    assert clamp("fast_scout", 10_000) == 240
    assert clamp("fast_scout", 10) == 60
    assert clamp("image_lane_run", 10) == 60
    assert clamp("image_lane_run", 10_000) == 600
    assert clamp("review_critic", 123) == 123
    print("RUNTIME TIMEOUT POLICY SELF-TEST PASS")


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test()
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

