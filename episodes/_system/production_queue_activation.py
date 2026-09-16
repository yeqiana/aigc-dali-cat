#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integrity-checked activation receipt for Production Queue storage authority.

The receipt records only the authority switch. Queue contents may legitimately
change after activation, so recorded cutover checksums are historical proof of
the switch moment rather than permanent content hashes.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import runtime_atomic_store
import runtime_workspace
import story_json

REL = Path("meta/runtime/production-queue-activation.json")
SCHEMA_VERSION = 1
ACTIVE = "ACTIVE"
ROLLED_BACK = "ROLLED_BACK"
VALID_STATES = {ACTIVE, ROLLED_BACK}
LOGICAL_ASSET = "production_queue"


class QueueActivationInvalid(RuntimeError):
    pass


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def marker_path(episode_dir: Path) -> Path:
    return runtime_workspace.workspace_path(Path(episode_dir).resolve(), REL)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _receipt_digest(receipt: dict) -> str:
    body = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_receipt(episode_dir: Path, *, state: str, legacy_sha256: str,
                  workspace_sha256: str, reason: str | None = None) -> dict:
    ep = Path(episode_dir).resolve()
    if state not in VALID_STATES:
        raise ValueError(f"invalid queue activation state: {state}")
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "logical_asset": LOGICAL_ASSET,
        "episode_namespace": runtime_workspace.episode_namespace(ep).as_posix(),
        "state": state,
        "legacy_sha256_at_transition": str(legacy_sha256),
        "workspace_sha256_at_transition": str(workspace_sha256),
        "recorded_at": now(),
        "legacy_preserved": True,
    }
    if reason:
        receipt["reason"] = str(reason)
    receipt["receipt_sha256"] = _receipt_digest(receipt)
    return receipt


def write_receipt(episode_dir: Path, receipt: dict) -> Path:
    path = marker_path(episode_dir)
    runtime_atomic_store.atomic_write_json(path, receipt)
    return path


def read_receipt(episode_dir: Path) -> dict | None:
    path = marker_path(episode_dir)
    if not path.is_file():
        return None
    try:
        data = story_json.read_json(path, default={})
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def inspect(episode_dir: Path, *, legacy_path: Path, workspace_path: Path) -> dict:
    ep = Path(episode_dir).resolve()
    receipt = read_receipt(ep)
    if receipt is None:
        return {"present": False, "valid": True, "state": "ABSENT", "reason": None, "receipt": None}
    errors: list[str] = []
    if receipt.get("schema_version") != SCHEMA_VERSION:
        errors.append("SCHEMA_VERSION_INVALID")
    if receipt.get("logical_asset") != LOGICAL_ASSET:
        errors.append("LOGICAL_ASSET_INVALID")
    if receipt.get("episode_namespace") != runtime_workspace.episode_namespace(ep).as_posix():
        errors.append("EPISODE_NAMESPACE_MISMATCH")
    state = str(receipt.get("state") or "")
    if state not in VALID_STATES:
        errors.append("STATE_INVALID")
    expected_digest = _receipt_digest(receipt)
    if receipt.get("receipt_sha256") != expected_digest:
        errors.append("RECEIPT_CHECKSUM_INVALID")
    for field in ("legacy_sha256_at_transition", "workspace_sha256_at_transition"):
        value = str(receipt.get(field) or "")
        if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value.lower()):
            errors.append(f"{field.upper()}_INVALID")
    if state == ACTIVE and not Path(workspace_path).is_file():
        errors.append("ACTIVE_WORKSPACE_QUEUE_MISSING")
    if state == ROLLED_BACK and not Path(legacy_path).is_file():
        errors.append("ROLLED_BACK_LEGACY_QUEUE_MISSING")
    return {
        "present": True,
        "valid": not errors,
        "state": state or "INVALID",
        "reason": errors[0] if errors else None,
        "errors": errors,
        "receipt": receipt,
    }


def authority(episode_dir: Path, *, legacy_path: Path, workspace_path: Path) -> str:
    status = inspect(episode_dir, legacy_path=legacy_path, workspace_path=workspace_path)
    if not status["valid"]:
        raise QueueActivationInvalid("QUEUE_ACTIVATION_INVALID:" + ";".join(status.get("errors") or []))
    return "workspace" if status["state"] == ACTIVE else "legacy"
