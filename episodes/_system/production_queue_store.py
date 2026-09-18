#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Physical storage boundary for the Production Queue.

Newly-created Episodes use Runtime Workspace as the native Production Queue
authority. Legacy Episodes remain pinned to their Episode copy unless an
explicit activation receipt changes authority. A ROLLED_BACK receipt always
wins over the native default so rollback remains durable and restart-safe.
"""
from __future__ import annotations

from pathlib import Path

import production_queue_activation as activation
import runtime_workspace
import story_json
import episode_state_persistence

REL = Path("meta/production-queue.json")
STORAGE_MODE = "activation_guarded"
CONSUMER_BOUNDARY_READY = True
CUTOVER_PROTOCOL_READY = True
STATE_REL = Path("meta/episode-state.json")
NATIVE_WORKSPACE_POLICY = "native_workspace_v1"


def legacy_path(episode_dir: Path) -> Path:
    return runtime_workspace.legacy_path(Path(episode_dir).resolve(), REL)


def workspace_candidate(episode_dir: Path) -> Path:
    return runtime_workspace.workspace_path(Path(episode_dir).resolve(), REL)


def native_workspace_default(episode_dir: Path) -> bool:
    ep = Path(episode_dir).resolve()
    state = episode_state_persistence.load(ep) or {}
    if not isinstance(state, dict):
        return False
    storage = state.get("runtime_storage") or {}
    queue = (storage.get("production_queue") or {}) if isinstance(storage, dict) else {}
    return (
        isinstance(queue, dict)
        and queue.get("authority") == "runtime_workspace"
        and queue.get("policy") == NATIVE_WORKSPACE_POLICY
    )


def authority(episode_dir: Path) -> str:
    ep = Path(episode_dir).resolve()
    legacy = legacy_path(ep)
    workspace = workspace_candidate(ep)
    receipt = activation.inspect(ep, legacy_path=legacy, workspace_path=workspace)
    if not receipt["valid"]:
        raise activation.QueueActivationInvalid(
            "QUEUE_ACTIVATION_INVALID:" + ";".join(receipt.get("errors") or [])
        )
    if receipt["state"] == activation.ACTIVE:
        return "workspace"
    if receipt["state"] == activation.ROLLED_BACK:
        return "legacy"
    return "workspace" if native_workspace_default(ep) else "legacy"


def read_path(episode_dir: Path) -> Path:
    ep = Path(episode_dir).resolve()
    return workspace_candidate(ep) if authority(ep) == "workspace" else legacy_path(ep)


def write_path(episode_dir: Path) -> Path:
    ep = Path(episode_dir).resolve()
    return workspace_candidate(ep) if authority(ep) == "workspace" else legacy_path(ep)


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

    native_default = receipt["state"] == "ABSENT" and native_workspace_default(ep)
    authority = (
        "workspace"
        if receipt["state"] == activation.ACTIVE or native_default
        else "legacy"
    )
    activated = authority == "workspace"
    blocking_reason = None
    cutover_ready = True
    if authority == "legacy" and not legacy.is_file():
        cutover_ready = False
        blocking_reason = "LEGACY_QUEUE_MISSING"
    elif receipt["state"] == "ABSENT" and not native_default and workspace.exists():
        if not workspace.is_file():
            cutover_ready = False
            blocking_reason = "UNVERIFIED_WORKSPACE_SHADOW_INVALID"
        elif legacy.is_file() and activation.sha256_file(workspace) != activation.sha256_file(legacy):
            cutover_ready = False
            blocking_reason = "UNVERIFIED_WORKSPACE_SHADOW_CONFLICT"

    selected = workspace if activated else legacy
    if native_default:
        effective_storage_mode = "workspace_native"
    elif receipt["state"] == activation.ACTIVE:
        effective_storage_mode = "workspace_active"
    else:
        effective_storage_mode = "legacy_pinned"
    return {
        "storage_mode": STORAGE_MODE,
        "effective_storage_mode": effective_storage_mode,
        "read_path": selected.as_posix(),
        "write_path": selected.as_posix(),
        "workspace_candidate": workspace.as_posix(),
        "workspace_shadow_enabled": activated,
        "consumer_boundary_ready": CONSUMER_BOUNDARY_READY,
        "cutover_protocol_ready": CUTOVER_PROTOCOL_READY,
        "cutover_ready": cutover_ready,
        "activated": activated,
        "activation_state": receipt["state"],
        "native_workspace_default": native_default,
        "blocking_reason": blocking_reason,
        "required_before_cutover": [] if cutover_ready else [blocking_reason],
        "authority": "runtime_workspace" if activated else "legacy_episode",
    }
