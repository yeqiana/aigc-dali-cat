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

import production_queue_activation as activation
import runtime_workspace

REL = Path("meta/production-queue.json")
STORAGE_MODE = "activation_guarded"
CONSUMER_BOUNDARY_READY = True
CUTOVER_PROTOCOL_READY = True


def legacy_path(episode_dir: Path) -> Path:
    return runtime_workspace.legacy_path(Path(episode_dir).resolve(), REL)


def workspace_candidate(episode_dir: Path) -> Path:
    return runtime_workspace.workspace_path(Path(episode_dir).resolve(), REL)


def _authority(episode_dir: Path) -> str:
    ep = Path(episode_dir).resolve()
    return activation.authority(
        ep,
        legacy_path=legacy_path(ep),
        workspace_path=workspace_candidate(ep),
    )


def read_path(episode_dir: Path) -> Path:
    ep = Path(episode_dir).resolve()
    return workspace_candidate(ep) if _authority(ep) == "workspace" else legacy_path(ep)


def write_path(episode_dir: Path) -> Path:
    ep = Path(episode_dir).resolve()
    return workspace_candidate(ep) if _authority(ep) == "workspace" else legacy_path(ep)


def migration_status(episode_dir: Path) -> dict:
    ep = Path(episode_dir).resolve()
    legacy = legacy_path(ep)
    workspace = workspace_candidate(ep)
    receipt = activation.inspect(ep, legacy_path=legacy, workspace_path=workspace)
    if not receipt["valid"]:
        return {
            "storage_mode": STORAGE_MODE,
            "effective_storage_mode": "invalid_activation",
            "read_path": None,
            "write_path": None,
            "workspace_candidate": workspace.as_posix(),
            "workspace_shadow_enabled": False,
            "consumer_boundary_ready": CONSUMER_BOUNDARY_READY,
            "cutover_protocol_ready": CUTOVER_PROTOCOL_READY,
            "cutover_ready": False,
            "activated": False,
            "activation_state": receipt["state"],
            "blocking_reason": "INVALID_ACTIVATION_RECEIPT",
            "activation_errors": receipt.get("errors") or [],
            "authority": "invalid_fail_closed",
        }

    authority = "workspace" if receipt["state"] == activation.ACTIVE else "legacy"
    activated = authority == "workspace"
    blocking_reason = None
    cutover_ready = True
    if authority == "legacy" and not legacy.is_file():
        cutover_ready = False
        blocking_reason = "LEGACY_QUEUE_MISSING"
    elif receipt["state"] == "ABSENT" and workspace.exists():
        if not workspace.is_file():
            cutover_ready = False
            blocking_reason = "UNVERIFIED_WORKSPACE_SHADOW_INVALID"
        elif legacy.is_file() and activation.sha256_file(workspace) != activation.sha256_file(legacy):
            cutover_ready = False
            blocking_reason = "UNVERIFIED_WORKSPACE_SHADOW_CONFLICT"

    selected = workspace if activated else legacy
    return {
        "storage_mode": STORAGE_MODE,
        "effective_storage_mode": "workspace_active" if activated else "legacy_pinned",
        "read_path": selected.as_posix(),
        "write_path": selected.as_posix(),
        "workspace_candidate": workspace.as_posix(),
        "workspace_shadow_enabled": activated,
        "consumer_boundary_ready": CONSUMER_BOUNDARY_READY,
        "cutover_protocol_ready": CUTOVER_PROTOCOL_READY,
        "cutover_ready": cutover_ready,
        "activated": activated,
        "activation_state": receipt["state"],
        "blocking_reason": blocking_reason,
        "required_before_cutover": [] if cutover_ready else [blocking_reason],
        "authority": "runtime_workspace" if activated else "legacy_episode",
    }
