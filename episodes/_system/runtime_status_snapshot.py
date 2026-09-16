#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only unified runtime status projection for Story OS.

This module deliberately does not persist a new status file and does not become a
second state machine.  It reconciles the existing canonical/operational evidence
at read time so Platform/Console callers do not have to interpret several JSON
files independently.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

import runner_health_monitor
import runtime_workspace
import production_queue_store

SCHEMA_VERSION = 1
EPISODE_STATE_REL = Path("meta/episode-state.json")
DAG_STATE_REL = Path("meta/runtime-dag-state.json")
RUNNER_STATE_REL = Path("meta/runtime-runner-state.json")
NEXT_ACTION_REL = Path("meta/runtime/next-action.json")
LEDGER_REL = Path("meta/production-ledger.json")
QUEUE_REL = production_queue_store.REL
ADMISSIONS_REL = Path("meta/visual-lock-admissions.json")

ACCEPTED_FRAME_STATES = frozenset({"PASSED", "WEAK_PASS", "LOCKED"})
REVIEW_PENDING_FRAME_STATES = frozenset({"ORIGINAL_READY", "REPAIR_READY"})
USER_ACTIONS = frozenset({"USER_DECISION_REQUIRED", "HUMAN_DECISION_REQUIRED"})


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def _read(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _ledger_frames(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = ledger.get("frames") or {}
    if not isinstance(rows, dict):
        return {}
    return {str(key): value for key, value in rows.items() if isinstance(value, dict)}


def _frame_status(frames: dict[str, dict[str, Any]], frame: int) -> str:
    row = frames.get(f"{int(frame):02d}") or frames.get(str(int(frame))) or {}
    return str(row.get("status") or "")


def _image_progress(frames: dict[str, dict[str, Any]], queue: dict[str, Any]) -> dict[str, Any]:
    rows = list(frames.values())
    queue_items = [row for row in (queue.get("items") or []) if isinstance(row, dict)]

    def generated(row: dict[str, Any]) -> bool:
        current = row.get("current_candidate") or {}
        if isinstance(current, dict) and current.get("sha256"):
            return True
        return any(
            isinstance(attempt, dict) and attempt.get("result") == "success"
            for attempt in (row.get("attempts") or [])
        )

    def active_frames(status: str) -> list[int]:
        values: set[int] = set()
        for row in queue_items:
            if str(row.get("status") or "") != status:
                continue
            try:
                frame = int(row.get("frame") or 0)
            except (TypeError, ValueError):
                continue
            if frame > 0:
                values.add(frame)
        return sorted(values)

    return {
        "expected_frames": len(rows),
        "generated_frames": sum(generated(row) for row in rows),
        "accepted_frames": sum(str(row.get("status") or "") in ACCEPTED_FRAME_STATES for row in rows),
        "weak_pass_frames": sum(str(row.get("status") or "") == "WEAK_PASS" for row in rows),
        "pending_review_frames": sum(str(row.get("status") or "") in REVIEW_PENDING_FRAME_STATES for row in rows),
        "pending_decision_frames": sum(str(row.get("status") or "") == "NEEDS_USER" for row in rows),
        "technical_failed_frames": sum(str(row.get("status") or "") == "TECH_FAILED" for row in rows),
        "queued_frames": active_frames("queued"),
        "running_frames": active_frames("running"),
    }


def _review_progress(admissions: dict[str, Any], image_progress: dict[str, Any]) -> dict[str, Any]:
    items = admissions.get("items") or {}
    rows = list(items.values()) if isinstance(items, dict) else []
    rows = [row for row in rows if isinstance(row, dict)]
    return {
        "visual_lock_total": len(rows),
        "visual_lock_accepted": sum(str(row.get("status") or "") in {"PASS", "WEAK_PASS"} for row in rows),
        "visual_lock_weak_pass": sum(str(row.get("status") or "") == "WEAK_PASS" for row in rows),
        "visual_lock_failed": sum(str(row.get("status") or "") == "FAIL" for row in rows),
        "content_review_pending": int(image_progress.get("pending_review_frames") or 0),
        "content_decision_pending": int(image_progress.get("pending_decision_frames") or 0),
    }


def _effective_next_action(
    action: dict[str, Any],
    production_stage: str | None,
    frames: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    """Drop demonstrably stale action projections without rewriting their evidence."""
    if not action:
        return {}, []
    warnings: list[str] = []
    action_stage = str(action.get("episode_state") or action.get("production_stage") or "")
    if action_stage and production_stage and action_stage != production_stage:
        warnings.append("STALE_NEXT_ACTION_STAGE")
        return {}, warnings

    action_name = str(action.get("action") or "")
    if action_name in USER_ACTIONS:
        raw_frames = action.get("frames") or []
        referenced: list[int] = []
        for value in raw_frames:
            try:
                frame = int(value)
            except (TypeError, ValueError):
                continue
            if frame > 0:
                referenced.append(frame)
        if referenced and not any(_frame_status(frames, frame) == "NEEDS_USER" for frame in referenced):
            warnings.append("STALE_USER_DECISION_ACTION")
            return {}, warnings
    return action, warnings


def _dag_summary(dag: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": dag.get("status"),
        "current_step": dag.get("current_step") or dag.get("step"),
        "attempt": dag.get("attempt"),
        "updated_at": dag.get("updated_at"),
    }


def snapshot(episode: Path) -> dict[str, Any]:
    """Build one stable Console/Platform read model without mutating the Episode."""
    ep = Path(episode).resolve()
    episode_state = _read(ep / EPISODE_STATE_REL)
    dag = runtime_workspace.read_json(ep, DAG_STATE_REL, default={}) or {}
    runner = runtime_workspace.read_json(ep, RUNNER_STATE_REL, default={}) or {}
    next_action_raw = runtime_workspace.read_json(ep, NEXT_ACTION_REL, default={}) or {}
    ledger = _read(ep / LEDGER_REL)
    queue = _read(production_queue_store.read_path(ep))
    admissions = _read(ep / ADMISSIONS_REL)

    production_stage = str(episode_state.get("current_state") or "") or None
    frames = _ledger_frames(ledger)
    image_progress = _image_progress(frames, queue)
    review_progress = _review_progress(admissions, image_progress)
    next_action, consistency_warnings = _effective_next_action(next_action_raw, production_stage, frames)

    try:
        health = runner_health_monitor.check(ep)
    except Exception:
        health = {"status": "UNKNOWN", "runner_status": runner.get("status"), "host_loop": "IDLE"}

    action_name = str(next_action.get("action") or "") or None
    runner_status = str(runner.get("status") or health.get("runner_status") or "") or None
    auto_recoverable = bool(next_action.get("auto_recoverable")) if next_action else False
    explicit_user_need = bool(action_name in USER_ACTIONS or runner_status == "HUMAN_REQUIRED")
    if next_action:
        needs_user = explicit_user_need
    else:
        needs_user = explicit_user_need or int(image_progress["pending_decision_frames"]) > 0

    if production_stage == "PUBLISH_READY" or action_name == "COMPLETE":
        execution_status = "COMPLETE"
    elif needs_user:
        execution_status = "NEEDS_USER"
    elif str(health.get("status") or "") == "HEALTHY":
        execution_status = "RUNNING"
    elif action_name and auto_recoverable:
        execution_status = "READY"
    elif runner_status in {"HOST_WAIT", "CAPABILITY_WAIT", "HARD_STOP", "YIELDED"}:
        execution_status = runner_status
    elif action_name:
        execution_status = "BLOCKED" if bool(next_action.get("hard_stop")) else "READY"
    elif production_stage:
        execution_status = "IDLE"
    else:
        execution_status = "UNKNOWN"

    blocking_reason = None
    if next_action and (needs_user or bool(next_action.get("hard_stop")) or bool(next_action.get("blocking"))):
        blocking_reason = str(next_action.get("reason") or "") or None

    dag_summary = _dag_summary(dag)
    next_step = action_name or dag_summary.get("current_step")
    if not next_step and production_stage == "PUBLISH_READY":
        next_step = "COMPLETE"

    source_paths = {
        "episode_state": EPISODE_STATE_REL,
        "runtime_dag_state": DAG_STATE_REL,
        "runtime_runner_state": RUNNER_STATE_REL,
        "next_action": NEXT_ACTION_REL,
        "production_ledger": LEDGER_REL,
        "production_queue": QUEUE_REL,
        "visual_lock_admissions": ADMISSIONS_REL,
    }
    external_runtime_sources = {"runtime_dag_state", "runtime_runner_state", "next_action"}

    def source_info(name: str, rel: Path) -> dict[str, Any]:
        if name in external_runtime_sources:
            resolved = runtime_workspace.resolve_read_path(ep, rel)
            return {
                "path": str(rel).replace("\\", "/"),
                "present": resolved.is_file(),
                "source_kind": runtime_workspace.source_kind(ep, rel),
            }
        return {"path": str(rel).replace("\\", "/"), "present": (ep / rel).is_file(), "source_kind": "episode"}

    return {
        "schema_version": SCHEMA_VERSION,
        "observed_at": _now(),
        "episode": ep.name,
        "episode_path": str(ep),
        "production_stage": production_stage,
        "execution_status": execution_status,
        "blocking_reason": blocking_reason,
        "current_action": action_name,
        "image_progress": image_progress,
        "review_progress": review_progress,
        "auto_recoverable": auto_recoverable,
        "needs_user": needs_user,
        "heartbeat": {
            "at": runner.get("heartbeat"),
            "health": health.get("status"),
            "runner_status": runner_status,
            "host_loop": health.get("host_loop"),
        },
        "next_step": next_step,
        "dag": dag_summary,
        "consistency_warnings": consistency_warnings,
        "source_states": {
            "episode_stage": production_stage,
            "next_action": str(next_action_raw.get("action") or "") or None,
            "runner_status": runner_status,
            "runner_health": health.get("status"),
            "dag_status": dag_summary.get("status"),
        },
        "sources": {
            name: source_info(name, rel)
            for name, rel in source_paths.items()
        },
    }
