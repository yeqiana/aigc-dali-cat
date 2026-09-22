#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Explicit Real-Episode Production Queue cutover harness.

Unlike ``production_queue_canary.py`` this module operates on one caller-supplied
repository Episode.  It never discovers an Episode, never creates a queue, and
never starts image execution.  ``preflight`` is read-only; the actual authority
transition remains delegated to the scheduler-lock-guarded cutover protocol.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import production_queue_activation as activation
import production_queue_cutover
import production_queue_store
import runner_state_store
import scheduler_core
import story_json

ROOT = Path(__file__).resolve().parents[2]
EPISODES_ROOT = ROOT / "episodes"


def resolve_episode(raw: str | Path) -> Path:
    ep = Path(raw)
    if not ep.is_absolute():
        ep = ROOT / ep
    ep = ep.resolve()
    if not ep.is_dir():
        raise ValueError(f"EPISODE_NOT_FOUND:{ep}")
    try:
        ep.relative_to(EPISODES_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("EPISODE_OUTSIDE_REPOSITORY_EPISODES") from exc
    if ep == EPISODES_ROOT.resolve() or ep.name.startswith("_"):
        raise ValueError("EPISODE_PATH_NOT_CONCRETE")
    return ep


def _read_queue(path: Path) -> tuple[dict | None, list[str]]:
    if not path.is_file():
        return None, ["LEGACY_QUEUE_MISSING"]
    try:
        queue = story_json.read_json(path)
    except Exception as exc:
        return None, [f"LEGACY_QUEUE_UNREADABLE:{type(exc).__name__}"]
    errors: list[str] = []
    if not isinstance(queue, dict):
        errors.append("LEGACY_QUEUE_NOT_OBJECT")
        return None, errors
    if queue.get("schema_version") != 1:
        errors.append("LEGACY_QUEUE_SCHEMA_INVALID")
    if not isinstance(queue.get("items"), list):
        errors.append("LEGACY_QUEUE_ITEMS_INVALID")
    if not isinstance(queue.get("waves"), list):
        errors.append("LEGACY_QUEUE_WAVES_INVALID")
    return queue, errors


def preflight(episode_dir: str | Path) -> dict:
    """Read-only GO/NO-GO check for one explicit repository Episode."""
    ep = resolve_episode(episode_dir)
    legacy = production_queue_store.legacy_path(ep)
    workspace = production_queue_store.workspace_candidate(ep)
    marker = activation.inspect(ep, legacy_path=legacy, workspace_path=workspace)
    queue, errors = _read_queue(legacy)

    if not marker.get("valid"):
        errors.append("INVALID_ACTIVATION_RECEIPT")
        errors.extend(str(x) for x in (marker.get("errors") or []))

    migration = production_queue_store.migration_status(ep)
    if migration.get("blocking_reason"):
        errors.append(str(migration["blocking_reason"]))

    runner = runner_state_store.load(ep)
    runner_status = str(runner.get("status") or "").upper()
    if runner_status == "RUNNING":
        errors.append("RUNNER_RUNNING")

    items = (queue or {}).get("items") or []
    running_ids = [str(row.get("id") or "") for row in items
                   if isinstance(row, dict) and str(row.get("status") or "").lower() == "running"]
    if running_ids:
        errors.append("QUEUE_HAS_RUNNING_IMAGE_ITEMS")

    # The on-disk lock file is deliberately *not* interpreted as a live owner:
    # runner_state_store documents that the inode persists after unlock.  The
    # only authoritative lock acquisition happens atomically inside activate /
    # rollback, which fail closed with QUEUE_MUTATION_BUSY.
    lock_path = (ep / scheduler_core.SCHEDULER_LOCK_REL).resolve()
    unique_errors = list(dict.fromkeys(errors))
    return {
        "status": "GO" if not unique_errors else "NO_GO",
        "episode": ep.relative_to(ROOT).as_posix(),
        "legacy_queue": legacy.as_posix(),
        "workspace_queue": workspace.as_posix(),
        "legacy_queue_readable": queue is not None and not any(x.startswith("LEGACY_QUEUE_") for x in unique_errors),
        "queue_items": len(items),
        "running_queue_item_ids": running_ids,
        "runner_status": runner_status or None,
        "activation_state": marker.get("state"),
        "activation_receipt_valid": bool(marker.get("valid")),
        "authority": migration.get("authority"),
        "cutover_ready": bool(migration.get("cutover_ready")),
        "workspace_shadow_enabled": bool(migration.get("workspace_shadow_enabled")),
        "scheduler_lock": {
            "path": lock_path.as_posix(),
            "file_exists": lock_path.exists(),
            "live_owner_check": "DEFERRED_TO_ATOMIC_CUTOVER",
        },
        "image_execution_started": False,
        "errors": unique_errors,
    }


def status(episode_dir: str | Path) -> dict:
    return preflight(episode_dir)


def activate(episode_dir: str | Path) -> dict:
    ep = resolve_episode(episode_dir)
    before = preflight(ep)
    if before["status"] != "GO":
        return {"status": "BLOCKED", "reason": "REAL_CANARY_PREFLIGHT_FAILED", "preflight": before}
    result = production_queue_cutover.activate(ep)
    return {**result, "preflight": before, "image_execution_started": False}


def rollback(episode_dir: str | Path) -> dict:
    ep = resolve_episode(episode_dir)
    runner = runner_state_store.load(ep)
    if str(runner.get("status") or "").upper() == "RUNNING":
        return {"status": "BLOCKED", "reason": "RUNNER_RUNNING", "activated": True}
    try:
        queue = scheduler_core.load_queue(ep)
    except Exception as exc:
        return {"status": "BLOCKED", "reason": f"QUEUE_UNREADABLE:{type(exc).__name__}", "activated": True}
    if any(isinstance(row, dict) and str(row.get("status") or "").lower() == "running"
           for row in (queue.get("items") or [])):
        return {"status": "BLOCKED", "reason": "QUEUE_HAS_RUNNING_IMAGE_ITEMS", "activated": True}
    result = production_queue_cutover.rollback(ep)
    return {**result, "image_execution_started": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "status", "activate", "rollback"):
        p = sub.add_parser(name)
        p.add_argument("episode_dir", help="Explicit repository Episode path; never auto-discovered.")
    args = parser.parse_args()
    try:
        fn = {"preflight": preflight, "status": status, "activate": activate, "rollback": rollback}[args.command]
        result = fn(args.episode_dir)
    except Exception as exc:
        result = {"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"GO", "PASS"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
