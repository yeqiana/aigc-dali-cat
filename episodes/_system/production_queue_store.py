#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Physical storage boundary for the Production Queue.

Phase 4 keeps the queue pinned to the Episode while all runtime consumers use
this boundary. The remaining cutover blocker is no longer consumer migration:
the hot single-writer queue still needs a scheduler-lock-guarded copy plus an
explicit verified activation protocol so an accidentally stale Workspace copy
can never shadow the live legacy queue.
"""
from __future__ import annotations

from pathlib import Path

import runtime_workspace

REL = Path("meta/production-queue.json")
STORAGE_MODE = "legacy_pinned"
CONSUMER_BOUNDARY_READY = True
CUTOVER_BLOCKER = "DEFER_ATOMIC_CUTOVER_PROTOCOL"


def legacy_path(episode_dir: Path) -> Path:
    return runtime_workspace.legacy_path(Path(episode_dir).resolve(), REL)


def read_path(episode_dir: Path) -> Path:
    return legacy_path(episode_dir)


def write_path(episode_dir: Path) -> Path:
    return legacy_path(episode_dir)


def workspace_candidate(episode_dir: Path) -> Path:
    return runtime_workspace.workspace_path(Path(episode_dir).resolve(), REL)


def migration_status(episode_dir: Path) -> dict:
    ep = Path(episode_dir).resolve()
    return {
        "storage_mode": STORAGE_MODE,
        "read_path": read_path(ep).as_posix(),
        "write_path": write_path(ep).as_posix(),
        "workspace_candidate": workspace_candidate(ep).as_posix(),
        "workspace_shadow_enabled": False,
        "consumer_boundary_ready": CONSUMER_BOUNDARY_READY,
        "cutover_ready": False,
        "blocking_reason": CUTOVER_BLOCKER,
        "required_before_cutover": [
            "scheduler_lock_guarded_copy",
            "checksum_verified_activation",
            "stale_workspace_shadow_rejected",
        ],
        "authority": "execution_record_not_episode_stage",
    }
