#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Physical storage boundary for the Production Queue.

Phase 3 intentionally keeps the queue pinned to the Episode.  The queue is a hot
single-writer execution record shared by scheduler, recovery, repair and status
consumers.  Centralising path selection now makes a later Workspace cutover one
controlled switch, while refusing to let an accidentally copied Workspace queue
shadow the live legacy queue before all consumers are ready.
"""
from __future__ import annotations

from pathlib import Path

import runtime_workspace

REL = Path("meta/production-queue.json")
STORAGE_MODE = "legacy_pinned"


def read_path(episode_dir: Path) -> Path:
    return runtime_workspace.legacy_path(Path(episode_dir).resolve(), REL)


def write_path(episode_dir: Path) -> Path:
    return runtime_workspace.legacy_path(Path(episode_dir).resolve(), REL)


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
        "cutover_ready": False,
        "blocking_reason": "DEFER_CONSUMER_MIGRATION",
        "authority": "execution_record_not_episode_stage",
    }
