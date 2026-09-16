#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated end-to-end canary for Production Queue authority cutover.

This command never operates on a repository Episode.  It builds a disposable
Episode + Runtime Workspace under a temporary root, exercises the real guarded
activation/store/scheduler/rollback path, then removes the whole sandbox.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import production_queue_activation as activation
import production_queue_cutover
import production_queue_store
import runtime_workspace
import scheduler_core
import story_json


@contextmanager
def _isolated_runtime_root(root: Path):
    root = Path(root).resolve()
    old_root = runtime_workspace.ROOT
    old_episodes_root = runtime_workspace.EPISODES_ROOT
    old_default_root = runtime_workspace.DEFAULT_ROOT
    old_env = os.environ.get(runtime_workspace.ENV_ROOT)
    runtime_workspace.ROOT = root
    runtime_workspace.EPISODES_ROOT = root / "episodes"
    runtime_workspace.DEFAULT_ROOT = root / "runtime-home"
    os.environ[runtime_workspace.ENV_ROOT] = str(runtime_workspace.DEFAULT_ROOT)
    try:
        yield
    finally:
        runtime_workspace.ROOT = old_root
        runtime_workspace.EPISODES_ROOT = old_episodes_root
        runtime_workspace.DEFAULT_ROOT = old_default_root
        if old_env is None:
            os.environ.pop(runtime_workspace.ENV_ROOT, None)
        else:
            os.environ[runtime_workspace.ENV_ROOT] = old_env


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def run_isolated_canary(*, base_dir: Path | None = None) -> dict:
    """Exercise real Queue cutover semantics in a disposable sandbox only."""
    parent = str(Path(base_dir).resolve()) if base_dir is not None else None
    with tempfile.TemporaryDirectory(prefix="storyos-queue-canary-", dir=parent) as raw_root:
        root = Path(raw_root).resolve()
        with _isolated_runtime_root(root):
            ep = runtime_workspace.EPISODES_ROOT / "_canary" / "production-queue"
            (ep / "meta").mkdir(parents=True, exist_ok=True)
            story_json.write_json(ep / "meta/episode-state.json", {
                "current_state": "VISUAL_CALIBRATED",
                "disposition": "ACTIVE",
            })
            legacy = production_queue_store.legacy_path(ep)
            initial_queue = {
                "schema_version": 1,
                "items": [{"id": "canary-legacy-v1", "frame": 1, "status": "queued"}],
                "waves": [],
            }
            story_json.write_json(legacy, initial_queue)
            legacy_before = legacy.read_bytes()

            before = production_queue_store.migration_status(ep)
            _require(before["authority"] == "legacy_episode", "CANARY_INITIAL_AUTHORITY_NOT_LEGACY")
            _require(before["activated"] is False, "CANARY_INITIAL_STATE_ACTIVE")

            activated = production_queue_cutover.activate(ep)
            _require(activated.get("status") == "PASS", "CANARY_ACTIVATION_FAILED")
            workspace = production_queue_store.workspace_candidate(ep)
            _require(production_queue_store.read_path(ep) == workspace, "CANARY_WORKSPACE_READ_NOT_ACTIVE")
            _require(legacy.read_bytes() == legacy_before, "CANARY_LEGACY_CHANGED_DURING_ACTIVATION")

            scheduler_queue = scheduler_core.load_queue(ep)
            scheduler_queue["items"].append({"id": "canary-workspace-v2", "frame": 2, "status": "queued"})
            scheduler_core.save_queue(ep, scheduler_queue)
            _require(legacy.read_bytes() == legacy_before, "CANARY_LEGACY_CHANGED_DURING_WORKSPACE_WRITE")
            _require(
                any(row.get("id") == "canary-workspace-v2" for row in scheduler_core.load_queue(ep).get("items") or []),
                "CANARY_SCHEDULER_WRITE_NOT_VISIBLE",
            )

            active_status = production_queue_store.migration_status(ep)
            _require(active_status["authority"] == "runtime_workspace", "CANARY_ACTIVE_AUTHORITY_NOT_WORKSPACE")
            active_receipt = activation.inspect(ep, legacy_path=legacy, workspace_path=workspace)
            _require(active_receipt["valid"] and active_receipt["state"] == activation.ACTIVE,
                     "CANARY_ACTIVE_RECEIPT_INVALID")

            rolled_back = production_queue_cutover.rollback(ep)
            _require(rolled_back.get("status") == "PASS", "CANARY_ROLLBACK_FAILED")
            _require(production_queue_store.read_path(ep) == legacy, "CANARY_LEGACY_READ_NOT_RESTORED")
            _require(legacy.read_bytes() == workspace.read_bytes(), "CANARY_ROLLBACK_COPY_MISMATCH")
            _require(
                any(row.get("id") == "canary-workspace-v2" for row in scheduler_core.load_queue(ep).get("items") or []),
                "CANARY_ROLLBACK_LOST_LATEST_QUEUE",
            )
            final_status = production_queue_store.migration_status(ep)
            final_receipt = activation.inspect(ep, legacy_path=legacy, workspace_path=workspace)
            _require(final_status["authority"] == "legacy_episode", "CANARY_FINAL_AUTHORITY_NOT_LEGACY")
            _require(final_receipt["valid"] and final_receipt["state"] == activation.ROLLED_BACK,
                     "CANARY_ROLLBACK_RECEIPT_INVALID")

            return {
                "status": "PASS",
                "sandboxed": True,
                "real_episode_touched": False,
                "initial_authority": before["authority"],
                "active_authority": active_status["authority"],
                "final_authority": final_status["authority"],
                "activation_reason": activated.get("reason"),
                "rollback_reason": rolled_back.get("reason"),
                "workspace_write_verified": True,
                "legacy_frozen_while_active": True,
                "rollback_latest_queue_preserved": True,
            }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-dir", type=Path, default=None,
                        help="Optional parent for the disposable sandbox; never an Episode path.")
    args = parser.parse_args()
    try:
        result = run_isolated_canary(base_dir=args.base_dir)
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
