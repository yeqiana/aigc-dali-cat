#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Host-agent adapter for WORK/WEB Story OS execution.

This module deliberately does not invoke a model. It prepares machine-readable,
idempotent requests for the surrounding ChatGPT product runtime. Local Python
must never silently fall back to Codex while WORK/WEB is selected.

V2.6.1.1 keeps immutable request history under meta/runtime/host-requests/ while
maintaining meta/runtime/product-host-request.json as a compatibility/current
pointer.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import episode_performance
import frame_contract
import preimage_authority_snapshot
import preimage_task_contract
import preimage_protocol
import preproduction_handoff
import storyos_config
import story_json
import runtime_memory_advice
import runtime_workspace
import hot_state_bridge
import host_request_persistence
import episode_state_persistence

ROOT = Path(__file__).resolve().parents[2]
REQUEST_REL = Path("meta/runtime/product-host-request.json")
REQUEST_HISTORY_REL = Path("meta/runtime/host-requests")
HOST_ACTION_REQUIRED_RC = 20
STAGES = ("IDEA_LOCKED","STORYBOARD_LOCKED","VISUAL_CALIBRATED","PRODUCTION_PASSED","PUBLISH_READY","PUBLISHED","DATA_REVIEWED")

STATE_TO_STEP = {
    "IDEA_LOCKED": ("CREATIVE_STORY", "STORYBOARD_LOCKED"),
    "VISUAL_CALIBRATED": ("PRODUCTION", "PRODUCTION_PASSED"),
    "PRODUCTION_PASSED": ("RELEASE", "PUBLISH_READY"),
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def execution_now() -> str:
    """Higher-resolution timestamp for real Host worker overlap measurement."""
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="microseconds")


def _read_json(path: Path) -> dict:
    data = story_json.read_json(path, require_object=False)
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, data: dict) -> None:
    story_json.write_json(path, data)


def _read_current_request(ep: Path) -> dict | None:
    ep = Path(ep).resolve()
    hot = hot_state_bridge.read(ep, "HOST_REQUEST_CURRENT")
    if isinstance(hot.get("value"), dict):
        return hot["value"]
    if not hot_state_bridge.file_fallback_allowed(hot):
        return None
    current_path = runtime_workspace.resolve_read_path(ep, REQUEST_REL)
    if not current_path.is_file():
        return None
    current = _read_json(current_path)
    return current if isinstance(current, dict) else None


def load_current_request(ep: Path) -> dict | None:
    """Read the current host request through the Redis-aware owner boundary."""
    return _read_current_request(ep)


def _write_current_request(ep: Path, data: dict) -> Path:
    ep = Path(ep).resolve()
    current_path = runtime_workspace.workspace_path(ep, REQUEST_REL)
    if hot_state_bridge.compatibility_write_allowed():
        current_path = runtime_workspace.write_json(ep, REQUEST_REL, data)
    hot_state_bridge.mirror(ep, "HOST_REQUEST_CURRENT", data)
    return current_path


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _stable_hash(data: dict) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def episode_state(ep: Path) -> str:
    data = episode_state_persistence.load(Path(ep).resolve()) or {}
    return str(data.get("current_state") or "")


def _state_at_least(current: str, target: str) -> bool:
    return current in STAGES and target in STAGES and STAGES.index(current) >= STAGES.index(target)


def reconcile(ep: Path) -> dict | None:
    """Finalize a stale current host pointer when canonical evidence already proves completion."""
    current = _read_current_request(ep)
    if current is None:
        return None
    if current.get("status") != "HOST_ACTION_REQUIRED":
        return current
    request_id = str(current.get("request_id") or "")
    if not request_id:
        return current
    step = str(current.get("next_step") or "")
    target = str(current.get("target_state") or "")
    cur_state = episode_state(ep)
    complete = bool(target and _state_at_least(cur_state, target))
    if step in {"PREIMAGE_COMPILE", "PREIMAGE_FRAME_CONTRACT_COMPILE", "PREIMAGE_VERIFY"}:
        try:
            complete = (ep / "meta/preproduction-handoff.json").is_file() and not preproduction_handoff.verify(ep)
        except Exception:
            complete = False
    if complete:
        return mark_complete(ep, request_id, result={"reconciled_from_canonical_evidence": True, "episode_state": cur_state, "step": step})
    return current


def next_host_step(ep: Path, mode: str = "full_auto") -> tuple[str, str | None]:
    state = episode_state(ep)
    if state == "STORYBOARD_LOCKED":
        try:
            handoff_valid = (ep / "meta/preproduction-handoff.json").is_file() and not preproduction_handoff.verify(ep)
        except Exception:
            handoff_valid = False
        barrier = ep / "meta/runtime/preimage-authority-barrier.json"
        index = ep / "meta/runtime/contracts/frame-contract-index.json"
        task_state_path = ep / preimage_task_contract.STATE_REL
        task_state = _read_json(task_state_path) if task_state_path.is_file() else {}
        committed_path = ep / "meta/runtime/preimage-committed-snapshot.json"
        if task_state:
            committed = _read_json(committed_path) if committed_path.is_file() else {}
            if not committed or preimage_authority_snapshot.stale_owned(ep, committed):
                return "PREIMAGE_TASK_SET", None
        contract_errors: list[str] = []
        if index.is_file():
            try:
                contract_errors = frame_contract.verify_all(ep)
            except Exception as exc:
                contract_errors = [str(exc)]
        if barrier.is_file() and (not index.is_file() or contract_errors):
            return "PREIMAGE_FRAME_CONTRACT_COMPILE", None
        if index.is_file() and not contract_errors and not handoff_valid:
            return "PREIMAGE_VERIFY", None
        if not handoff_valid:
            return "PREIMAGE_TASK_SET", None
        if mode == "preproduction_only":
            return "COMPLETE", "STORYBOARD_LOCKED"
        return "VISUAL_LOCK", "VISUAL_CALIBRATED"
    if state == "PUBLISH_READY":
        return "COMPLETE", "PUBLISH_READY"
    return STATE_TO_STEP.get(state, ("READ_EPISODE_STATE", None))


def _persist_request(ep: Path, payload: dict, *, category: str) -> dict:
    fingerprint_basis = {
        key: value for key, value in payload.items()
        if key not in {"created_at", "request_id", "request_fingerprint", "request_path", "current_request_path"}
    }
    fingerprint = _stable_hash(fingerprint_basis)
    request_id = f"{category}-{fingerprint[:16]}"
    history_path = host_request_persistence.compatibility_path(ep, request_id)
    existing = host_request_persistence.load(ep, request_id)
    if existing is not None:
        if existing.get("request_fingerprint") != fingerprint:
            raise RuntimeError(f"host request id collision: {request_id}")
        stored = existing
    else:
        stored = {
            **payload,
            "schema_version": 2,
            "request_id": request_id,
            "request_fingerprint": fingerprint,
            "created_at": now(),
        }
        host_request_persistence.save(ep, stored)
    current = {
        **stored,
        "request_path": _display_path(history_path),
    }
    current_path = _write_current_request(ep, current)
    return {
        **stored,
        "request_path": _display_path(history_path),
        "current_request_path": _display_path(current_path),
    }


NEW_PRODUCT_RUNTIME = "WORK"
WORKSPACE_TRANSPORT = "DEVSPACE"


def build_request(
    ep: Path,
    *,
    runtime: str,
    mode: str,
    resume: bool,
    request_data: dict | None = None,
    source: str = "workflow_runner",
) -> dict:
    runtime = str(runtime).upper()
    if runtime != NEW_PRODUCT_RUNTIME:
        raise ValueError("new product runtime host actions require WORK + DevSpace; WEB/WebCodex is disabled")
    step, target = next_host_step(ep, mode)
    if step == "PREIMAGE_TASK_SET":
        requests = build_preimage_requests(ep, runtime=runtime, mode=mode, resume=resume, source=source)
        return {
            "status": "HOST_ACTION_REQUIRED",
            "next_step": step,
            "requests": requests,
            "host_task_count": len(requests),
            "host_dispatch_contract": {
                "strategy": "parallel_start_then_collect",
                "max_parallel": len(requests),
                "start_all_before_wait": True,
                "completion_order": "any",
                "authority_commit": "single_writer_after_barrier",
                "host_owned_concurrency": True,
                "measurement": "start-preimage/complete-preimage execution intervals",
            },
            "not_episode_stage": True,
            "not_gate_authority": True,
        }
    rel = ep.resolve().relative_to(ROOT.resolve()).as_posix()
    try:
        index=storyos_config.load_index(); required_read=((index.get("stage_read_sets") or {}).get(step) or [])
    except Exception:
        required_read=[]
    step_instructions=[]
    if step=="CREATIVE_STORY":
        step_instructions += [
            "Read config/profiles/account_creative/default.json as the account default topic/style profile, without overriding explicit user constraints or recent-5 anti-homogeneity evidence.",
            "For new/unlocked work author meta/shot-progression-review.json schema_version=3 using standards/directing_grammar_v1.json: large+small shot scales, globally unique scene_position_id, at least two translated classic shot-structure references, practical-light narrative design, and at least one physically valid concealed anomaly carrier for suspense/strange genres. Run shot_progression_gate.py validate before completing CREATIVE_STORY."
        ]
        memory_advice=runtime_memory_advice.advice_for_episode(ep)
        step_instructions += [
            "Use memory_advice only as historical watch-outs. It is advisory-only, cannot block production, and never overrides explicit user constraints, recent-5 evidence, or canonical Story OS standards."
        ]
    if step=="RELEASE":
        step_instructions += [
            "Inspect approved images before subtitle rendering. Prefer left-middle 42%-62% height, x=72; if moving outside that band, write safe_zone_override_reason per frame. Never cover faces, anomaly evidence, hands/actions, key props, native text or causal clues.",
            "Keep captions first-person, conversational, concise and eye-catching; canonical renderer maximum remains two lines."
        ]
    data = {
        "runtime": runtime,
        "status": "COMPLETE" if step == "COMPLETE" else "HOST_ACTION_REQUIRED",
        "source": source,
        "episode": rel,
        "episode_state": episode_state(ep),
        "execution_mode": mode,
        "resume": bool(resume),
        "next_step": step,
        "target_state": target,
        "required_read": required_read,
        "local_codex_spawn_allowed": False,
        "local_codex_fallback_allowed": False,
        "host_contract": {
            "actor": "chatgpt_product_runtime",
            "workspace_access": "use DevSpace/workspace tools directly",
            "workspace_transport": WORKSPACE_TRANSPORT,
            "webcodex_allowed": False,
            "critic_provenance": "WORK_ISOLATED",
            "image_generation": "delegate only the image execution substep according to runtime.image_execution_runtime; CODEX image mode must not take ownership of Story/PREIMAGE/Review/Release",
            "deterministic_scripts": "may run locally when they do not invoke a model backend",
            "stage_authority": "meta/episode-state.json",
            "must_not_claim_pass_without_evidence": True,
        },
        "instructions": [
            "Execute the declared non-image host step in the surrounding product runtime; do not hand Story/PREIMAGE/Review/Release ownership to local Codex.",
            "Reuse valid SHA-bound evidence and obey existing Story OS gates.",
            "For independent critics, prepare the product review request, author the candidate in a fresh isolated WORK review turn using DevSpace only, then finalize it.",
            "Do not use WebCodex for repository access or review execution.",
            "When a later image scheduler runs, honor runtime.image_execution_runtime. CODEX there means image generation/repair only, not CODEX full-auto.",
            *step_instructions,
        ],
        **({"memory_advice": memory_advice} if step=="CREATIVE_STORY" else {}),
    }
    if request_data:
        data["runtime_request_id"] = request_data.get("request_id")
    stored = _persist_request(ep, data, category="host")
    if stored.get("status") == "HOST_ACTION_REQUIRED":
        episode_performance.safe_begin_named_span(
            ep, f"HOST_ACTION_{step}", source=source,
            metadata={"request_id": stored.get("request_id"), "runtime": runtime, "next_step": step})
    return stored


def build_preimage_requests(ep: Path, *, runtime: str, mode: str, resume: bool, source: str) -> list[dict]:
    """Emit one immutable host request per unfinished PREIMAGE worker.

    These requests are execution facts only.  Host completion must provide a
    verified candidate through ``complete_preimage_task``; no request advances
    the canonical episode stage.
    """
    runtime = str(runtime).upper()
    if runtime != NEW_PRODUCT_RUNTIME:
        raise ValueError("PREIMAGE host tasks require WORK + DevSpace; WEB/WebCodex is disabled")
    snapshot = preimage_authority_snapshot.build(ep, write=True)
    tasks = preimage_task_contract.plan_tasks(ep, snapshot, resume=resume)
    out=[]
    for task in tasks:
        if task["status"] == "REUSED":
            preimage_task_contract.update_task_state(ep, task, "REUSED")
            continue
        data={
            "runtime": runtime, "status": "HOST_ACTION_REQUIRED", "source": source,
            "episode": ep.resolve().relative_to(ROOT.resolve()).as_posix(), "episode_state": episode_state(ep),
            "execution_mode": mode, "resume": bool(resume),
            # The registered DAG step name, from the one mapping that defines it.
            # Concatenating "PREIMAGE_" + task_type here produced host requests
            # naming a step that no registry holds (W-93/P0-E).
            "next_step": preimage_task_contract.canonical_step(task["task_type"]),
            "task": task, "snapshot_id": task["snapshot_id"], "candidate_output_path": task["candidate_output"],
            "resume_token": task["task_id"], "required_read": task["required_read"],
            "target_contract": "candidate_only_no_shared_authority_write",
            "host_contract": {"stage_authority":"meta/episode-state.json","must_not_claim_pass_without_evidence":True,
                              "must_not_write_shared_authority":True,"candidate_return_required":True,
                              "execution_start_handshake_required":True,
                              "dispatch_group":"PREIMAGE_TASK_SET","independent_parallelizable":True,
                              "wait_for_siblings_before_start":False,
                              "workspace_transport":WORKSPACE_TRANSPORT,"webcodex_allowed":False},
            "instructions":["Perform only this bounded PREIMAGE task.",
                            "This request is independent inside PREIMAGE_TASK_SET: start it without waiting for sibling PREIMAGE requests to finish.",
                            "Before model/work execution, claim this request with product_runtime_adapter.py start-preimage using this request_id and a stable worker_id.",
                            "Write/return the declared Candidate JSON only.",
                            "Do not modify story-gates.json, episode-state.json, or release-manifest.json."]}
        stored=_persist_request(ep,data,category="preimage")
        preimage_task_contract.update_task_state(ep,task,"HOST_ACTION_REQUIRED",request_id=stored["request_id"])
        episode_performance.safe_begin_named_span(ep,f"HOST_ACTION_PREIMAGE_{task['task_type']}",source=source,
            metadata={"request_id":stored["request_id"],"snapshot_id":task["snapshot_id"]})
        out.append(stored)
    return out


def mark_preimage_task_running(ep: Path, request_id: str, *, worker_id: str) -> dict:
    """Claim one PREIMAGE Host request for real execution.

    W-90: request creation is not execution.  The Host must explicitly mark the
    request RUNNING so concurrency metrics are based on observed execution
    intervals rather than overlapping HOST_ACTION_REQUIRED files.
    """
    worker_id = str(worker_id or "").strip()
    if not worker_id:
        raise ValueError("worker_id is required")
    request = host_request_persistence.load(ep, request_id)
    if request is None:
        raise FileNotFoundError(f"host request missing: {request_id}")
    task = request.get("task") or {}
    if not task or not str(request.get("next_step") or "").startswith("PREIMAGE_"):
        raise ValueError("not a PREIMAGE task request")
    status = str(request.get("status") or "")
    if status not in {"HOST_ACTION_REQUIRED", "RUNNING"}:
        raise ValueError(f"PREIMAGE host request is terminal: {status}")
    existing_worker = str(request.get("worker_id") or "").strip()
    if status == "RUNNING" and existing_worker and existing_worker != worker_id:
        raise RuntimeError(f"PREIMAGE_HOST_REQUEST_ALREADY_RUNNING: worker={existing_worker}")
    started_at = str(request.get("started_at") or execution_now())
    request.update({"status": "RUNNING", "started_at": started_at, "worker_id": worker_id})
    host_request_persistence.save(ep, request)
    preimage_task_contract.update_task_state(
        ep, task, "RUNNING", request_id=request_id,
        execution={"started_at": started_at, "worker_id": worker_id},
    )
    return request


def preimage_execution_metrics(ep: Path) -> dict:
    """Summarize only observed Host execution intervals; never infer starts.

    PREIMAGE authority commit can legitimately advance the current authority
    snapshot after the Host requests have finished.  Do not let that erase the
    just-observed execution evidence: prefer the current snapshot when it still
    has request rows, otherwise fall back to the latest snapshot that has a real
    ``started_at`` handshake.  The returned authority/measurement ids make that
    fallback explicit instead of silently mixing snapshots.
    """
    all_rows = []
    snapshot_path = ep / "meta/runtime/preimage-authority-snapshot.json"
    current_snapshot = _read_json(snapshot_path).get("snapshot_id") if snapshot_path.is_file() else None
    for data in host_request_persistence.list_all(ep):
        if (data.get("task") or {}) and str(data.get("next_step") or "").startswith("PREIMAGE_"):
            all_rows.append(data)

    def request_snapshot(row: dict) -> str | None:
        return row.get("snapshot_id") or (row.get("task") or {}).get("snapshot_id")

    measured_snapshot = current_snapshot
    scope = "current_authority_snapshot"
    if not current_snapshot:
        rows = all_rows
        measured_snapshot = None
        scope = "all_history_no_authority_snapshot"
    else:
        rows = [row for row in all_rows if request_snapshot(row) == current_snapshot]
        if not rows:
            observed = [row for row in all_rows if row.get("started_at")]
            if observed:
                latest = max(observed, key=lambda row: str(row.get("started_at") or ""))
                measured_snapshot = request_snapshot(latest)
                rows = [row for row in all_rows if request_snapshot(row) == measured_snapshot]
                scope = "latest_observed_execution_snapshot"
            else:
                measured_snapshot = current_snapshot
                rows = []
                scope = "current_authority_snapshot_no_requests"
    events: list[tuple[dt.datetime, int]] = []
    started = finished = 0
    inflight = 0
    for row in rows:
        started_raw = row.get("started_at")
        finished_raw = row.get("finished_at") or row.get("finalized_at") or row.get("completed_at")
        if not started_raw:
            continue
        try:
            start = dt.datetime.fromisoformat(str(started_raw))
        except ValueError:
            continue
        started += 1
        events.append((start, +1))
        if finished_raw:
            try:
                end = dt.datetime.fromisoformat(str(finished_raw))
            except ValueError:
                end = None
            if end is not None and end >= start:
                finished += 1
                events.append((end, -1))
            else:
                inflight += 1
        else:
            inflight += 1
    active = peak = 0
    # At the same timestamp, a finish releases capacity before another start.
    for _at, delta in sorted(events, key=lambda item: (item[0], item[1])):
        active += delta
        peak = max(peak, active)
    return {
        "snapshot_id": measured_snapshot,
        "authority_snapshot_id": current_snapshot,
        "snapshot_scope": scope,
        "requested": len(rows), "started": started, "finished": finished,
        "inflight_now": inflight, "peak_observed_concurrency": peak,
        "unmeasured_requests": max(0, len(rows) - started),
        "measurement": "host_execution_intervals_only",
    }


def complete_preimage_task(ep: Path, request_id: str, candidate: dict) -> dict:
    """Finalize exactly one host task after candidate validation, never a Gate."""
    request=host_request_persistence.load(ep,request_id)
    if request is None: raise FileNotFoundError(f"host request missing: {request_id}")
    task=request.get("task") or {}
    if not task or not str(request.get("next_step") or "").startswith("PREIMAGE_"):
        raise ValueError("not a PREIMAGE task request")
    if (request.get("host_contract") or {}).get("execution_start_handshake_required"):
        if request.get("status") != "RUNNING" or not request.get("started_at") or not request.get("worker_id"):
            raise ValueError("PREIMAGE_HOST_EXECUTION_START_REQUIRED")
    errors=preimage_task_contract.write_candidate(ep,task,candidate)
    if errors:
        finished_at = execution_now()
        preimage_task_contract.update_task_state(ep,task,"FAILED",request_id=request_id,reason="; ".join(errors),
            execution={"started_at": request.get("started_at"), "worker_id": request.get("worker_id"), "finished_at": finished_at})
        request.update({"status":"FAILED","completed_at":finished_at,"finished_at":finished_at,"candidate_errors":errors})
        host_request_persistence.save(ep,request); return request
    finished_at = execution_now()
    preimage_task_contract.update_task_state(ep,task,"COMPLETED",request_id=request_id,candidate_file=task["candidate_output"],
        execution={"started_at": request.get("started_at"), "worker_id": request.get("worker_id"), "finished_at": finished_at})
    request.update({"status":"FINALIZED","finalized_at":finished_at,"finished_at":finished_at,"candidate_path":task["candidate_output"]})
    host_request_persistence.save(ep,request)
    episode_performance.safe_end_named_span(ep,f"HOST_ACTION_PREIMAGE_{task['task_type']}",status="PASS",metadata={"request_id":request_id})
    # The fourth independently finalized candidate releases only the serial
    # authority commit. Completion of a request never grants a Gate decision.
    snapshot = _read_json(ep / "meta/runtime/preimage-authority-snapshot.json")
    planned = preimage_task_contract.plan_tasks(ep, snapshot, resume=True) if snapshot else []
    if planned and all(item.get("status") == "REUSED" for item in planned):
        request["authority_commit"] = preimage_protocol.commit_candidates(ep, snapshot, planned)
        host_request_persistence.save(ep, request)
    return request


def build_image_request(
    ep: Path,
    *,
    runtime: str,
    queue_items: list[dict],
    source: str,
) -> dict:
    runtime = str(runtime).upper()
    if runtime != NEW_PRODUCT_RUNTIME:
        raise ValueError("product image request requires WORK + DevSpace; WEB/WebCodex is disabled")
    rel = ep.resolve().relative_to(ROOT.resolve()).as_posix()
    items = []
    for row in queue_items:
        items.append({
            "id": row.get("id"),
            "frame": int(row.get("frame") or 0),
            "kind": row.get("kind"),
            "scope": row.get("scope"),
            "prompt_file": row.get("prompt_file"),
            "references": row.get("references") or [],
            "model": row.get("model"),
            "quality": row.get("quality"),
            "frame_contract": row.get("frame_contract"),
        })
    items.sort(key=lambda x: (int(x.get("frame") or 0), str(x.get("id") or "")))
    data = {
        "runtime": runtime,
        "status": "HOST_ACTION_REQUIRED",
        "source": source,
        "episode": rel,
        "episode_state": episode_state(ep),
        "next_step": "IMAGE_GENERATION",
        "local_codex_spawn_allowed": False,
        "local_codex_fallback_allowed": False,
        "items": items,
        "host_contract": {
            "actor": "chatgpt_product_runtime",
            "workspace_transport": WORKSPACE_TRANSPORT,
            "webcodex_allowed": False,
            "image_model_contract": "use each queue item's locked model/quality",
            "continuity_contract": "respect Frame Contract and reference arbitration",
            "file_transport": "save/import real generated RAW assets when the product runtime supports workspace file transfer",
            "on_missing_file_transport": "pause as HOST_ACTION_REQUIRED; never fall back to local Codex",
        },
    }
    stored = _persist_request(ep, data, category="image")
    episode_performance.safe_begin_named_span(
        ep, "HOST_ACTION_IMAGE_GENERATION", source=source,
        metadata={"request_id": stored.get("request_id"), "runtime": runtime, "count": len(items)})
    return stored


def mark_complete(ep: Path, request_id: str, *, result: dict | None = None) -> dict:
    data = host_request_persistence.load(ep, request_id)
    if data is None:
        raise FileNotFoundError(f"host request missing: {request_id}")
    data["status"] = "FINALIZED"
    data["finalized_at"] = now()
    span_name = "HOST_ACTION_IMAGE_GENERATION" if str(data.get("next_step") or "") == "IMAGE_GENERATION" else f"HOST_ACTION_{str(data.get('next_step') or 'UNKNOWN')}"
    episode_performance.safe_end_named_span(ep, span_name, status="PASS", metadata={"request_id": request_id})
    if result is not None:
        data["result"] = result
    host_request_persistence.save(ep, data)
    current = _read_current_request(ep)
    if current is not None and current.get("request_id") == request_id:
        current.update({
            "status": "FINALIZED",
            "finalized_at": data["finalized_at"],
        })
        if result is not None:
            current["result"] = result
        _write_current_request(ep, current)
    return data


def print_request(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def self_test() -> None:
    assert HOST_ACTION_REQUIRED_RC == 20
    assert NEW_PRODUCT_RUNTIME == "WORK"
    assert WORKSPACE_TRANSPORT == "DEVSPACE"
    assert _state_at_least("PUBLISH_READY", "STORYBOARD_LOCKED")
    assert not _state_at_least("IDEA_LOCKED", "STORYBOARD_LOCKED")
    assert STATE_TO_STEP["IDEA_LOCKED"] == ("CREATIVE_STORY", "STORYBOARD_LOCKED")
    assert REQUEST_HISTORY_REL.as_posix() == "meta/runtime/host-requests"
    assert next_host_step.__name__ == "next_host_step"
    print("PRODUCT RUNTIME ADAPTER V2.6.1.1 SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("complete-preimage", help="finalize one validated PREIMAGE host candidate through the canonical adapter")
    p.add_argument("episode_dir")
    p.add_argument("--request-id", required=True)
    p.add_argument("--candidate", required=True, help="candidate JSON path, absolute or episode-relative")
    p = sub.add_parser("start-preimage", help="claim one PREIMAGE Host request for actual execution")
    p.add_argument("episode_dir")
    p.add_argument("--request-id", required=True)
    p.add_argument("--worker-id", required=True)
    p = sub.add_parser("preimage-metrics", help="show observed PREIMAGE Host execution concurrency")
    p.add_argument("episode_dir")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd in {None, "self-test"}:
        self_test(); return 0
    ep = Path(args.episode_dir).resolve()
    if args.cmd == "start-preimage":
        print_request(mark_preimage_task_running(ep, args.request_id, worker_id=args.worker_id)); return 0
    if args.cmd == "preimage-metrics":
        print_request(preimage_execution_metrics(ep)); return 0
    raw = Path(args.candidate)
    candidate_path = raw.resolve() if raw.is_absolute() else (ep / raw).resolve()
    candidate = _read_json(candidate_path)
    result = complete_preimage_task(ep, args.request_id, candidate)
    print_request(result)
    return 0 if result.get("status") == "FINALIZED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
