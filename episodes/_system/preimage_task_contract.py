#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PREIMAGE worker protocol: tasks/candidates/runtime-only resume state.

This module deliberately contains no episode-stage or Gate decision.  A task is
complete only when an independently produced candidate passes structural
verification; shared authority is committed later by ``authority_commit``.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

import runtime_atomic_store as atomic
import story_json

STATE_REL = Path("meta/runtime/preimage-task-state.json")
CANDIDATE_REL = Path("meta/runtime/preimage-candidates")
TASK_TYPES = (
    "CHARACTER_FINALIZE", "ENVIRONMENT_PREPARE", "WORLD_PREPARE", "VISUAL_NARRATIVE_PREPARE",
)

# Scopes are intentionally disjoint: the commit layer fails closed if this
# invariant is ever changed by a caller or an externally returned candidate.
TASK_SPECS = {
    "CHARACTER_FINALIZE": {
        "node_id": "character_finalize", "candidate": "character-finalize.json",
        "scope": ("character.finalize",),
        "required_read": ("meta/story-gates.json", "meta/character-contract.json", "meta/character-visual-contract.json"),
    },
    "ENVIRONMENT_PREPARE": {
        "node_id": "environment_prepare", "candidate": "environment.json",
        "scope": ("visual.environment_contract", "visual.frame_directives"),
        "required_read": ("meta/story-gates.json", "meta/story-semantic-review.json", "meta/runtime-request.json"),
    },
    "WORLD_PREPARE": {
        "node_id": "world_prepare", "candidate": "world.json",
        "scope": ("visual.world_identity", "visual.world_state", "visual.temporal_continuity", "visual.wardrobe"),
        "required_read": ("meta/story-gates.json", "meta/world-identity.json", "meta/character-contract.json"),
    },
    "VISUAL_NARRATIVE_PREPARE": {
        "node_id": "visual_narrative_prepare", "candidate": "visual-narrative.json",
        "scope": ("visual.narrative_core", "visual.shot_progression", "visual.capture_grammar"),
        "required_read": ("meta/story-gates.json", "meta/shot-progression-review.json", "meta/runtime-request.json"),
    },
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def candidate_path(ep: Path, task_type: str) -> Path:
    return Path(ep) / CANDIDATE_REL / TASK_SPECS[task_type]["candidate"]


def _state(ep: Path) -> dict:
    return story_json.read_json(Path(ep) / STATE_REL, default={}) or {}


def _state_base(snapshot_id: str) -> dict:
    return {
        "schema_version": 1,
        "snapshot_id": snapshot_id,
        "not_episode_stage": True,
        "not_gate_authority": True,
        "canonical_stage_source": "meta/episode-state.json",
        "tasks": {},
        "updated_at": now(),
    }


def task_contract(ep: Path, task_type: str, snapshot: dict, *, resume: bool = False) -> dict:
    if task_type not in TASK_SPECS:
        raise ValueError(f"unsupported PREIMAGE task type: {task_type}")
    spec = TASK_SPECS[task_type]
    out = candidate_path(ep, task_type)
    return {
        "schema_version": 1,
        "task_id": f"preimage-{task_type.lower()}-{snapshot['snapshot_id'][:12]}",
        "task_type": task_type,
        "node_id": spec["node_id"],
        "episode": str(Path(ep).resolve()),
        "snapshot_id": snapshot["snapshot_id"],
        "depends_on": ["story_lock"],
        "required_read": list(spec["required_read"]),
        "input_contract": {"source_authority_sha256": dict(snapshot.get("authority_sha256") or {})},
        "candidate_output": out.relative_to(Path(ep)).as_posix(),
        "verifier": f"verify_{task_type.lower()}_candidate",
        "retry_policy": {"retry_failed_only": True, "stale_requires_new_snapshot": True},
        "authority_scope": list(spec["scope"]),
        "target": "candidate_only_no_shared_authority_write",
        "status": "PENDING",
        "resume": bool(resume),
    }


def validate_patch_scopes(tasks: list[dict]) -> None:
    seen: dict[str, str] = {}
    for task in tasks:
        for scope in task.get("authority_scope") or []:
            if scope in seen:
                raise ValueError(f"PREIMAGE authority scope collision: {scope} ({seen[scope]}, {task.get('task_id')})")
            seen[scope] = str(task.get("task_id"))


def verify_candidate(candidate: dict, task: dict) -> list[str]:
    errors: list[str] = []
    for key in ("schema_version", "task_id", "task_type", "snapshot_id", "source_authority_sha256", "generated_at", "status", "payload"):
        if key not in candidate:
            errors.append(f"candidate missing {key}")
    if candidate.get("task_id") != task.get("task_id"):
        errors.append("candidate task_id mismatch")
    if candidate.get("task_type") != task.get("task_type"):
        errors.append("candidate task_type mismatch")
    if candidate.get("snapshot_id") != task.get("snapshot_id"):
        errors.append("candidate snapshot_id mismatch")
    if candidate.get("source_authority_sha256") != task.get("input_contract", {}).get("source_authority_sha256"):
        errors.append("candidate source authority SHA mismatch")
    if candidate.get("status") != "COMPLETED":
        errors.append("candidate status must be COMPLETED")
    if not isinstance(candidate.get("payload"), dict) or not candidate.get("payload"):
        errors.append("candidate payload must be a non-empty object")
    if set(candidate.get("authority_scope") or []) != set(task.get("authority_scope") or []):
        errors.append("candidate authority scope mismatch")
    expected=set(task.get("authority_scope") or [])
    actual=set((candidate.get("payload") or {}).keys()) if isinstance(candidate.get("payload"),dict) else set()
    if actual != expected:
        errors.append("candidate payload keys must exactly match declared authority scopes")
    for scope in expected:
        if not isinstance((candidate.get("payload") or {}).get(scope),dict) or not candidate["payload"][scope]:
            errors.append(f"candidate payload scope must be a non-empty object: {scope}")
    verifier=globals().get(str(task.get("verifier") or ""))
    if not callable(verifier): errors.append("candidate verifier missing")
    elif not errors: errors.extend(verifier(candidate,task))
    return errors

def verify_character_finalize_candidate(candidate: dict, task: dict) -> list[str]:
    value=candidate["payload"]["character.finalize"]
    keys={"character","identity","pov","appearance"}
    return [] if any(value.get(key) not in (None,"",{},[]) for key in keys) else ["character candidate requires character/identity/pov/appearance"]

def verify_environment_prepare_candidate(candidate: dict, task: dict) -> list[str]:
    env=candidate["payload"]["visual.environment_contract"]; directives=candidate["payload"]["visual.frame_directives"]
    errors=[]
    if not isinstance(env.get("baseline"),dict) or not env["baseline"]: errors.append("environment candidate requires non-empty baseline")
    if not directives: errors.append("environment candidate requires frame directives")
    return errors

def _applicable_object(value: dict) -> bool:
    return value.get("applicable") is False or bool(value)

def verify_world_prepare_candidate(candidate: dict, task: dict) -> list[str]:
    return [f"world candidate invalid: {scope}" for scope,value in candidate["payload"].items() if not _applicable_object(value)]

def verify_visual_narrative_prepare_candidate(candidate: dict, task: dict) -> list[str]:
    return [f"visual narrative candidate invalid: {scope}" for scope,value in candidate["payload"].items() if not value]

def valid_payload(task: dict) -> dict:
    """Explicit contract-shaped fixture/host template; never used by validation."""
    kind=task["task_type"]
    if kind=="CHARACTER_FINALIZE": return {"character.finalize":{"character":"locked","identity":"stable","pov":"first_person","appearance":"textual_anchor"}}
    if kind=="ENVIRONMENT_PREPARE": return {"visual.environment_contract":{"baseline":{"location":"ordinary","weather":"stable"}},"visual.frame_directives":{"01":{"environment":"ordinary"}}}
    if kind=="WORLD_PREPARE": return {scope:{"applicable":False} for scope in task["authority_scope"]}
    return {scope:{"rule":"candidate"} for scope in task["authority_scope"]}


def read_candidate(ep: Path, task: dict) -> dict | None:
    path = Path(ep) / task["candidate_output"]
    data = story_json.read_json(path, default=None)
    return data if isinstance(data, dict) else None


def write_candidate(ep: Path, task: dict, candidate: dict) -> list[str]:
    errors = verify_candidate(candidate, task)
    if errors:
        return errors
    story_json.write_json(Path(ep) / task["candidate_output"], candidate)
    return []


def update_task_state(ep: Path, task: dict, status: str, *, request_id: str | None = None,
                      candidate_file: str | None = None, reason: str | None = None) -> dict:
    path = Path(ep) / STATE_REL
    def mutate(current: dict) -> dict:
        if not current or current.get("snapshot_id") != task["snapshot_id"]:
            current.clear(); current.update(_state_base(task["snapshot_id"]))
        current["updated_at"] = now()
        row = dict(current.setdefault("tasks", {}).get(task["task_type"]) or {})
        row.update({"task_id": task["task_id"], "status": status, "request_id": request_id or row.get("request_id"),
                    "candidate_path": candidate_file or task["candidate_output"], "updated_at": now()})
        if reason: row["reason"] = reason
        current["tasks"][task["task_type"]] = row
        return dict(current)
    return atomic.update_json(path, lambda: _state_base(task["snapshot_id"]), mutate)


def plan_tasks(ep: Path, snapshot: dict, *, resume: bool = False) -> list[dict]:
    state = _state(ep)
    tasks = [task_contract(ep, kind, snapshot, resume=resume) for kind in TASK_TYPES]
    validate_patch_scopes(tasks)
    for task in tasks:
        candidate = read_candidate(ep, task)
        row = ((state.get("tasks") or {}).get(task["task_type"]) or {}) if state.get("snapshot_id") == snapshot["snapshot_id"] else {}
        if candidate and not verify_candidate(candidate, task) and row.get("status") in {"COMPLETED", "REUSED"}:
            task["status"] = "REUSED"
        elif row.get("status") == "FAILED" and resume:
            task["status"] = "RETRY"
        elif row.get("status") == "STALE":
            task["status"] = "STALE"
    return tasks


def candidate_template(task: dict, payload: dict) -> dict:
    """Helper for host integrations/tests; callers supply independently created payload."""
    return {
        "schema_version": 1, "task_id": task["task_id"], "task_type": task["task_type"],
        "snapshot_id": task["snapshot_id"], "source_authority_sha256": task["input_contract"]["source_authority_sha256"],
        "generated_at": now(), "status": "COMPLETED", "payload": payload,
        "authority_scope": list(task["authority_scope"]), "evidence": [], "verification": {"gate_pass": None},
        "model_execution": {"independent_task": True},
    }
