#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scheduler-lock-guarded Production Queue activation and rollback protocol.

No operation runs implicitly. Callers must explicitly invoke activate() or
rollback(); both serialize against the existing image scheduler lock, preserve
both queue copies, verify checksums before changing authority, and write the
activation receipt last.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import production_queue_activation as activation
import production_queue_store
import scheduler_core


def _copy_exact(source: Path, target: Path, expected_sha256: str, *, allow_overwrite: bool) -> str:
    source = Path(source)
    target = Path(target)
    if activation.sha256_file(source) != expected_sha256:
        raise RuntimeError("SOURCE_CHECKSUM_DRIFT")
    if target.exists():
        if not target.is_file():
            raise RuntimeError("TARGET_NOT_FILE")
        if activation.sha256_file(target) == expected_sha256:
            return "REUSE"
        if not allow_overwrite:
            raise RuntimeError("TARGET_CONFLICT")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_tmp = tempfile.mkstemp(prefix=target.name + ".", suffix=".queue-cutover-tmp", dir=str(target.parent))
    tmp = Path(raw_tmp)
    try:
        with os.fdopen(fd, "wb") as out, source.open("rb") as src:
            shutil.copyfileobj(src, out, length=1024 * 1024)
            out.flush()
            os.fsync(out.fileno())
        if activation.sha256_file(tmp) != expected_sha256:
            raise RuntimeError("TEMP_CHECKSUM_MISMATCH")
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)
    if activation.sha256_file(target) != expected_sha256:
        raise RuntimeError("TARGET_CHECKSUM_MISMATCH")
    return "COPY"


def _blocked(reason: str, **extra) -> dict:
    return {"status": "BLOCKED", "reason": reason, "activated": False, **extra}


def activate(episode_dir: Path) -> dict:
    ep = Path(episode_dir).resolve()
    try:
        with scheduler_core.queue_transaction(ep):
            legacy = production_queue_store.legacy_path(ep)
            workspace = production_queue_store.workspace_candidate(ep)
            marker = activation.inspect(ep, legacy_path=legacy, workspace_path=workspace)
            if not marker["valid"]:
                return _blocked("INVALID_ACTIVATION_RECEIPT", errors=marker.get("errors") or [])
            if marker["state"] == activation.ACTIVE:
                return {"status": "PASS", "reason": "ALREADY_ACTIVE", "activated": True,
                        "read_path": workspace.as_posix(), "write_path": workspace.as_posix()}
            if not legacy.is_file():
                return _blocked("LEGACY_QUEUE_MISSING")
            source_sha = activation.sha256_file(legacy)
            allow_overwrite = marker["state"] == activation.ROLLED_BACK
            try:
                copy_result = _copy_exact(legacy, workspace, source_sha, allow_overwrite=allow_overwrite)
            except RuntimeError as exc:
                return _blocked(str(exc))
            workspace_sha = activation.sha256_file(workspace)
            if source_sha != workspace_sha:
                return _blocked("POST_COPY_CHECKSUM_MISMATCH")
            receipt = activation.build_receipt(
                ep,
                state=activation.ACTIVE,
                legacy_sha256=source_sha,
                workspace_sha256=workspace_sha,
                reason="scheduler-lock-guarded queue activation",
            )
            activation.write_receipt(ep, receipt)
            verified = activation.inspect(ep, legacy_path=legacy, workspace_path=workspace)
            if not verified["valid"] or verified["state"] != activation.ACTIVE:
                return _blocked("ACTIVATION_RECEIPT_VERIFY_FAILED", errors=verified.get("errors") or [])
            return {
                "status": "PASS",
                "reason": "ACTIVATED",
                "activated": True,
                "copy_result": copy_result,
                "sha256": workspace_sha,
                "legacy_preserved": legacy.is_file(),
                "read_path": workspace.as_posix(),
                "write_path": workspace.as_posix(),
                "receipt_path": activation.marker_path(ep).as_posix(),
            }
    except scheduler_core.QueueMutationBusy:
        return _blocked("QUEUE_MUTATION_BUSY")


def rollback(episode_dir: Path) -> dict:
    ep = Path(episode_dir).resolve()
    try:
        with scheduler_core.queue_transaction(ep):
            legacy = production_queue_store.legacy_path(ep)
            workspace = production_queue_store.workspace_candidate(ep)
            marker = activation.inspect(ep, legacy_path=legacy, workspace_path=workspace)
            if not marker["valid"]:
                return _blocked("INVALID_ACTIVATION_RECEIPT", errors=marker.get("errors") or [])
            if marker["state"] != activation.ACTIVE:
                return {"status": "PASS", "reason": "ALREADY_LEGACY", "activated": False,
                        "read_path": legacy.as_posix(), "write_path": legacy.as_posix()}
            if not workspace.is_file():
                return _blocked("ACTIVE_WORKSPACE_QUEUE_MISSING")
            source_sha = activation.sha256_file(workspace)
            try:
                copy_result = _copy_exact(workspace, legacy, source_sha, allow_overwrite=True)
            except RuntimeError as exc:
                return _blocked(str(exc))
            legacy_sha = activation.sha256_file(legacy)
            if source_sha != legacy_sha:
                return _blocked("ROLLBACK_CHECKSUM_MISMATCH")
            receipt = activation.build_receipt(
                ep,
                state=activation.ROLLED_BACK,
                legacy_sha256=legacy_sha,
                workspace_sha256=source_sha,
                reason="scheduler-lock-guarded queue rollback",
            )
            activation.write_receipt(ep, receipt)
            verified = activation.inspect(ep, legacy_path=legacy, workspace_path=workspace)
            if not verified["valid"] or verified["state"] != activation.ROLLED_BACK:
                return _blocked("ROLLBACK_RECEIPT_VERIFY_FAILED", errors=verified.get("errors") or [])
            return {
                "status": "PASS",
                "reason": "ROLLED_BACK",
                "activated": False,
                "copy_result": copy_result,
                "sha256": legacy_sha,
                "workspace_preserved": workspace.is_file(),
                "read_path": legacy.as_posix(),
                "write_path": legacy.as_posix(),
                "receipt_path": activation.marker_path(ep).as_posix(),
            }
    except scheduler_core.QueueMutationBusy:
        return _blocked("QUEUE_MUTATION_BUSY")
