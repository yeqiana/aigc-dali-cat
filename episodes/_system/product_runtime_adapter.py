#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Host-agent adapter for WORK Story OS execution.

This module deliberately does not invoke a model. It prepares machine-readable,
idempotent requests for the surrounding ChatGPT product runtime. Local Python
must never silently fall back to Codex while WORK is selected. Repository
access is supplied by the configured Workspace Provider.

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
import workspace_provider
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
        # Dispatcher fast path.  The verify_all() below re-compiles every frame
        # contract and re-reads the durable Episode contract store hundreds of
        # times per frame; it exists only to answer "must PREIMAGE recompile the
        # frame contracts".  Once the PREIMAGE handoff verifies, that answer can
        # no longer matter: runtime_dag's PREIMAGE_COMPILE reuse branch returns
        # REUSED for any valid handoff before it would ever recompile, and the
        # real gate is validate_target on the next stage transition.  Without
        # this, every dispatch during the whole VISUAL_LOCK phase paid that walk.
        if handoff_valid:
            if mode == "preproduction_only":
                return "COMPLETE", "STORYBOARD_LOCKED"
            return "VISUAL_LOCK", "VISUAL_CALIBRATED"
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


def _persist_request(ep: Path, payload: dict, *, category: str, set_current: bool = True) -> dict:
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
    result = {
        **stored,
        "request_path": _display_path(history_path),
    }
    if set_current:
        current = dict(result)
        current_path = _write_current_request(ep, current)
        result["current_request_path"] = _display_path(current_path)
    return result


NEW_PRODUCT_RUNTIME = "WORK"


def _shadow_runtime_dependencies():
    """Lazy-load Shadow-only modules so default-off legacy routing has no Agent import cost."""
    import agent_shadow_compare as comparator
    import preimage_execution_persistence as persistence
    from agents import character_finalize_adapter as adapter
    from platform.agent.runtime import AgentRuntime as runtime_cls
    return comparator, persistence, adapter, runtime_cls


def _world_shadow_runtime_dependencies():
    import agent_shadow_compare as comparator
    import preimage_execution_persistence as persistence
    from agents import world_prepare_adapter as adapter
    from platform.agent.runtime import AgentRuntime as runtime_cls
    return comparator, persistence, adapter, runtime_cls


def world_prepare_host_candidate(task: dict, produced: dict) -> tuple[dict | None, list[str], dict | None]:
    """Host-side Candidate envelope and deterministic verification for World output."""
    payload = produced.get("payload") if isinstance(produced, dict) else None
    telemetry = produced.get("model_execution") if isinstance(produced, dict) else None
    if not isinstance(payload, dict):
        return None, [str((produced or {}).get("failure_reason") or "World producer returned no payload")], None
    candidate = preimage_task_contract.candidate_template(task, payload)
    if isinstance(telemetry, dict):
        candidate["model_execution"] = dict(telemetry)
    errors = preimage_task_contract.verify_candidate(candidate, task)
    semantic = None
    if not errors:
        comparator, _persistence, _adapter, _runtime_cls = _world_shadow_runtime_dependencies()
        semantic = comparator.compare_world_prepare_semantics(task, candidate)
        if semantic.get("pass") is not True:
            errors.extend(semantic.get("errors") or ["World semantic obligations failed"])
    return (candidate if not errors else None), errors, semantic


def character_finalize_shadow_enabled() -> bool:
    cfg = storyos_config.load_config()
    return storyos_config.get_path(
        cfg, "agent_runtime.adapters.character_finalize.shadow_enabled", False
    ) is True


def character_finalize_production_enabled() -> bool:
    cfg = storyos_config.load_config()
    return storyos_config.get_path(
        cfg, "agent_runtime.adapters.character_finalize.production_enabled", False
    ) is True


def character_finalize_legacy_fallback_enabled() -> bool:
    cfg = storyos_config.load_config()
    return storyos_config.get_path(
        cfg, "agent_runtime.adapters.character_finalize.legacy_fallback_on_technical", True
    ) is True


def world_prepare_shadow_enabled() -> bool:
    cfg = storyos_config.load_config()
    return storyos_config.get_path(
        cfg, "agent_runtime.adapters.world_prepare.shadow_enabled", False
    ) is True


def world_prepare_production_enabled() -> bool:
    cfg = storyos_config.load_config()
    return storyos_config.get_path(
        cfg, "agent_runtime.adapters.world_prepare.production_enabled", False
    ) is True


def _character_live_execution_id(task: dict) -> str:
    raw = f"{task.get('task_id')}|{task.get('snapshot_id')}|character-live-v1"
    return "exec_live_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _character_shadow_execution_id(task: dict) -> str:
    raw = f"{task.get('task_id')}|{task.get('snapshot_id')}|character-shadow-v1"
    return "exec_shadow_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _world_shadow_execution_id(task: dict) -> str:
    raw = f"{task.get('task_id')}|{task.get('snapshot_id')}|world-shadow-v1"
    return "exec_world_shadow_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


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
        raise ValueError("new product runtime host actions require WORK; workspace access is provided separately")
    workspace = workspace_provider.current()
    step, target = next_host_step(ep, mode)
    if step == "PREIMAGE_TASK_SET":
        requests = build_preimage_requests(ep, runtime=runtime, mode=mode, resume=resume, source=source)
        response = {
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
        shadow_requests = build_preimage_shadow_requests(
            ep, requests, runtime=runtime, mode=mode, resume=resume, source=source
        )
        world_shadow_requests = build_preimage_world_shadow_requests(
            ep, requests, runtime=runtime, mode=mode, resume=resume, source=source
        )
        shadow_requests.extend(world_shadow_requests)
        if shadow_requests:
            response["shadow_requests"] = shadow_requests
            response["shadow_host_task_count"] = len(shadow_requests)
            response["shadow_contract"] = {
                "canonical_authority": False,
                "writes_legacy_candidate": False,
                "included_in_preimage_concurrency_metric": False,
                "comparison": "deterministic_first",
            }
        return response
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
            "workspace_access": workspace.repository_access,
            **workspace.contract_fields(),
            "critic_provenance": "WORK_ISOLATED",
            "image_generation": "delegate only the image execution substep according to runtime.image_execution_runtime; CODEX image mode must not take ownership of Story/PREIMAGE/Review/Release",
            "deterministic_scripts": "may run locally when they do not invoke a model backend",
            "stage_authority": "meta/episode-state.json",
            "must_not_claim_pass_without_evidence": True,
        },
        "instructions": [
            "Execute the declared non-image host step in the surrounding product runtime; do not hand Story/PREIMAGE/Review/Release ownership to local Codex.",
            "Reuse valid SHA-bound evidence and obey existing Story OS gates.",
            f"For independent critics, prepare the product review request, author the candidate in a fresh isolated WORK review turn using the configured {workspace.provider_id} Workspace Provider, then finalize it.",
            "Workspace Provider access does not grant Episode state or release authority.",
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
        raise ValueError("PREIMAGE host tasks require WORK; workspace access is provided separately")
    workspace = workspace_provider.current()
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
                              "model_execution_telemetry_requested":True,
                              **workspace.contract_fields()},
            "instructions":["Perform only this bounded PREIMAGE task.",
                            "This request is independent inside PREIMAGE_TASK_SET: start it without waiting for sibling PREIMAGE requests to finish.",
                            "Before model/work execution, claim this request with product_runtime_adapter.py start-preimage using this request_id and a stable worker_id.",
                            "Write/return the declared Candidate JSON only.",
                            "When the Host/provider exposes execution usage, include model_execution telemetry: real_model_execution, wall_seconds, input_tokens, output_tokens, repeated_reads, failure, timeout, provider, model, telemetry_source. Never estimate missing values.",
                            "Do not modify story-gates.json, episode-state.json, or release-manifest.json."]}
        if task["task_type"] == "CHARACTER_FINALIZE" and character_finalize_production_enabled():
            _comparator, _persistence, character_finalize_adapter, _runtime_cls = _shadow_runtime_dependencies()
            execution_id = _character_live_execution_id(task)
            envelope = character_finalize_adapter.build_execution(
                task,
                attempt=1,
                shadow=False,
                execution_id=execution_id,
                routing_decision={
                    "executor": runtime,
                    "provider": workspace.provider_id,
                    "reason": "character_finalize_production",
                },
            )
            data["agent_adapter"] = "CHARACTER_FINALIZE_AGENT"
            data["agent_execution"] = envelope.to_dict()
            data["legacy_fallback_on_technical"] = character_finalize_legacy_fallback_enabled()
            data["host_contract"]["agent_candidate_required"] = True
            data["host_contract"]["model_execution_telemetry_required"] = True
            data["instructions"] = [
                "This canonical Character Finalize task is executed through the Character Agent Adapter.",
                "Return only the declared Character Finalize Candidate; the adapter, verifier, barrier, and existing authority_commit remain authoritative.",
                "Do not write shared authority directly.",
                *data["instructions"],
            ]
        stored=_persist_request(ep,data,category="preimage")
        preimage_task_contract.update_task_state(ep,task,"HOST_ACTION_REQUIRED",request_id=stored["request_id"])
        episode_performance.safe_begin_named_span(ep,f"HOST_ACTION_PREIMAGE_{task['task_type']}",source=source,
            metadata={"request_id":stored["request_id"],"snapshot_id":task["snapshot_id"]})
        out.append(stored)
    return out


def build_preimage_shadow_requests(
    ep: Path,
    legacy_requests: list[dict],
    *,
    runtime: str,
    mode: str,
    resume: bool,
    source: str,
) -> list[dict]:
    """Build optional Character Finalize shadow requests without canonical side effects."""
    if not character_finalize_shadow_enabled() or character_finalize_production_enabled():
        return []
    _comparator, _persistence, character_finalize_adapter, _runtime_cls = _shadow_runtime_dependencies()
    workspace = workspace_provider.current()
    out = []
    for legacy in legacy_requests:
        task = legacy.get("task") or {}
        if task.get("task_type") != "CHARACTER_FINALIZE":
            continue
        execution_id = _character_shadow_execution_id(task)
        envelope = character_finalize_adapter.build_execution(
            task,
            attempt=1,
            shadow=True,
            execution_id=execution_id,
            routing_decision={
                "executor": runtime,
                "provider": workspace.provider_id,
                "reason": "character_finalize_shadow",
            },
        )
        data = {
            "runtime": runtime,
            "status": "HOST_ACTION_REQUIRED",
            "source": f"{source}:character_finalize_shadow",
            "episode": ep.resolve().relative_to(ROOT.resolve()).as_posix(),
            "episode_state": episode_state(ep),
            "execution_mode": mode,
            "resume": bool(resume),
            "next_step": "PREIMAGE_CHARACTER_FINALIZE_SHADOW",
            "shadow": True,
            "shadow_kind": "CHARACTER_FINALIZE_AGENT",
            "legacy_request_id": legacy.get("request_id"),
            "task": task,
            "snapshot_id": task["snapshot_id"],
            "agent_execution": envelope.to_dict(),
            "target_contract": "agent_shadow_candidate_only_no_file_write",
            "host_contract": {
                "stage_authority": "meta/episode-state.json",
                "must_not_claim_pass_without_evidence": True,
                "must_not_write_shared_authority": True,
                "must_not_write_legacy_candidate": True,
                "candidate_return_required": True,
                "execution_start_handshake_required": True,
                "dispatch_group": "PREIMAGE_AGENT_SHADOW",
                "independent_parallelizable": True,
                "not_canonical_preimage_concurrency": True,
                "model_execution_telemetry_required_for_cutover": True,
                **workspace.contract_fields(),
            },
            "instructions": [
                "Execute only the Character Finalize shadow task.",
                "Do not write the legacy Candidate path or any shared authority.",
                "Start with product_runtime_adapter.py start-preimage-shadow.",
                "Return the Candidate through complete-preimage-shadow only.",
                "Include provider-backed model_execution telemetry for cutover evidence: real_model_execution, wall_seconds, input_tokens, output_tokens, repeated_reads, failure, timeout, provider, model, telemetry_source. Never guess unavailable values.",
                "This shadow result is comparison evidence and cannot release a Gate.",
            ],
        }
        out.append(_persist_request(ep, data, category="preimage-shadow", set_current=False))
    return out


def build_preimage_world_shadow_requests(
    ep: Path,
    legacy_requests: list[dict],
    *,
    runtime: str,
    mode: str,
    resume: bool,
    source: str,
) -> list[dict]:
    """Create a World candidate-only request in its own shadow request domain."""
    if not world_prepare_shadow_enabled() or world_prepare_production_enabled():
        return []
    _comparator, _persistence, world_adapter, _runtime_cls = _world_shadow_runtime_dependencies()
    from agents import world_prepare_model_producer
    workspace = workspace_provider.current()
    out = []
    for legacy in legacy_requests:
        task = legacy.get("task") or {}
        if task.get("task_type") != "WORLD_PREPARE":
            continue
        task = world_prepare_model_producer.freeze_task(ep, task)
        execution_id = _world_shadow_execution_id(task)
        envelope = world_adapter.build_execution(
            task, attempt=1, shadow=True, execution_id=execution_id,
            routing_decision={
                "executor": runtime, "provider": workspace.provider_id,
                "reason": "world_prepare_shadow",
            },
        )
        data = {
            "runtime": runtime,
            "status": "HOST_ACTION_REQUIRED",
            "source": f"{source}:world_prepare_shadow",
            "episode": ep.resolve().relative_to(ROOT.resolve()).as_posix(),
            "episode_state": episode_state(ep),
            "execution_mode": mode,
            "resume": bool(resume),
            "next_step": "PREIMAGE_WORLD_PREPARE_SHADOW",
            "shadow": True,
            "shadow_kind": "WORLD_PREPARE_AGENT",
            "legacy_request_id": legacy.get("request_id"),
            "task": task,
            "snapshot_id": task["snapshot_id"],
            "agent_execution": envelope.to_dict(),
            "target_contract": "agent_shadow_candidate_only_no_file_write",
            "host_contract": {
                "stage_authority": "meta/episode-state.json",
                "must_not_claim_pass_without_evidence": True,
                "must_not_write_shared_authority": True,
                "must_not_write_legacy_candidate": True,
                "candidate_return_required": True,
                "execution_start_handshake_required": True,
                "dispatch_group": "PREIMAGE_WORLD_AGENT_SHADOW",
                "independent_parallelizable": True,
                "not_canonical_preimage_concurrency": True,
                **workspace.contract_fields(),
            },
            "instructions": [
            "Execute WORLD_PREPARE through the existing Platform AgentRuntime and WorldPrepareAgentAdapter using this frozen PREIMAGE authority snapshot.",
            "Return a Candidate only. Do not write the legacy Candidate path, shared authority, Gate, Episode state, or current Host Request pointer.",
            "Start with product_runtime_adapter.py start-preimage-world-shadow and finalize through complete-preimage-world-shadow.",
            "When a real Codex model producer is used, include telemetry from episodes/_system/codex_execution_telemetry.py: token usage only from turn.completed.usage and wall/timeout/failure only from the user-runner receipt. Include elapsed_seconds, timed_out, and returncode in the runner receipt; never estimate tokens or fill missing values with zero.",
            "Set repeated_reads only with observable reads; if a frozen capsule is provided once and the model has no tools/file reads, record repeated_reads=0 with repeated_reads_scope=capsule.",
            "The candidate is comparison evidence only and cannot pass a Gate or release authority.",
            ],
        }
        out.append(_persist_request(ep, data, category="preimage-world-shadow", set_current=False))
    return out


def _world_shadow_request_matches_task(request: dict, task: dict) -> bool:
    shadow_task = request.get("task") or {}
    return (
        request.get("shadow") is True
        and request.get("shadow_kind") == "WORLD_PREPARE_AGENT"
        and shadow_task.get("task_id") == task.get("task_id")
        and shadow_task.get("snapshot_id") == task.get("snapshot_id")
    )


def reconcile_world_prepare_shadow(ep: Path, task: dict) -> dict | None:
    """Compare World candidates once both shadow and canonical legacy candidates exist."""
    comparator, persistence, _adapter, _runtime_cls = _world_shadow_runtime_dependencies()
    legacy_candidate = preimage_task_contract.read_candidate(ep, task)
    if not isinstance(legacy_candidate, dict):
        return None
    latest = next((row for row in host_request_persistence.list_all(ep)
                   if _world_shadow_request_matches_task(row, task)
                   and isinstance(row.get("shadow_candidate"), dict)), None)
    if latest is None:
        return None
    comparison = comparator.compare_preimage_candidates(task, legacy_candidate, latest["shadow_candidate"])
    latest["shadow_comparison"] = comparison
    latest["comparison_status"] = "COMPARED"
    latest["comparison_updated_at"] = execution_now()
    host_request_persistence.save(ep, latest)
    meta = latest.get("agent_execution") or {}
    execution_id = str(meta.get("execution_id") or "")
    if execution_id:
        try:
            persistence.mark_shadow_completed(
                ep, snapshot_id=task["snapshot_id"], task_id=task["task_id"],
                execution_id=execution_id,
                candidate_sha256=_stable_hash(latest["shadow_candidate"]),
                comparison_status="COMPARED",
                execution_evidence=dict(latest.get("model_execution_evidence") or {}),
            )
        except ValueError:
            pass
    return comparison


def _shadow_request_matches_task(request: dict, task: dict) -> bool:
    shadow_task = request.get("task") or {}
    return (
        request.get("shadow") is True
        and request.get("shadow_kind") == "CHARACTER_FINALIZE_AGENT"
        and shadow_task.get("task_id") == task.get("task_id")
        and shadow_task.get("snapshot_id") == task.get("snapshot_id")
    )


def reconcile_character_shadow(ep: Path, task: dict) -> dict | None:
    """Compare finalized shadow evidence with the legacy canonical Candidate when both exist."""
    agent_shadow_compare, preimage_execution_persistence, _adapter, _runtime_cls = _shadow_runtime_dependencies()
    legacy_candidate = preimage_task_contract.read_candidate(ep, task)
    if not isinstance(legacy_candidate, dict):
        return None
    latest = None
    for request in host_request_persistence.list_all(ep):
        if _shadow_request_matches_task(request, task) and isinstance(request.get("shadow_candidate"), dict):
            latest = request
    if latest is None:
        return None
    comparison = agent_shadow_compare.compare_preimage_candidates(
        task, legacy_candidate, latest["shadow_candidate"]
    )
    latest["shadow_comparison"] = comparison
    latest["comparison_status"] = "COMPARED"
    latest["comparison_updated_at"] = execution_now()
    host_request_persistence.save(ep, latest)
    execution_meta = latest.get("agent_execution") or {}
    execution_id = str(execution_meta.get("execution_id") or "")
    if execution_id:
        try:
            preimage_execution_persistence.mark_shadow_completed(
                ep,
                snapshot_id=task["snapshot_id"],
                task_id=task["task_id"],
                execution_id=execution_id,
                candidate_sha256=_stable_hash(latest["shadow_candidate"]),
                comparison_status="COMPARED",
                execution_evidence=dict(latest.get("model_execution_evidence") or {}),
            )
        except ValueError:
            pass
    return comparison


def mark_preimage_shadow_running(ep: Path, request_id: str, *, worker_id: str) -> dict:
    _comparator, preimage_execution_persistence, _adapter, _runtime_cls = _shadow_runtime_dependencies()
    worker_id = str(worker_id or "").strip()
    if not worker_id:
        raise ValueError("worker_id is required")
    request = host_request_persistence.load(ep, request_id)
    if request is None:
        raise FileNotFoundError(f"host request missing: {request_id}")
    if request.get("shadow") is not True or request.get("shadow_kind") != "CHARACTER_FINALIZE_AGENT":
        raise ValueError("not a Character Finalize shadow request")
    if request.get("status") not in {"HOST_ACTION_REQUIRED", "RUNNING"}:
        raise ValueError(f"PREIMAGE shadow request is terminal: {request.get('status')}")
    existing_worker = str(request.get("worker_id") or "").strip()
    if request.get("status") == "RUNNING" and existing_worker and existing_worker != worker_id:
        raise RuntimeError(f"PREIMAGE_SHADOW_REQUEST_ALREADY_RUNNING: worker={existing_worker}")
    task = request["task"]
    agent_execution = request.get("agent_execution") or {}
    execution_id = str(agent_execution.get("execution_id") or "")
    attempt = int(agent_execution.get("attempt") or 1)
    idempotency_key = str(agent_execution.get("idempotency_key") or "")
    record = preimage_execution_persistence.begin_execution(
        ep,
        snapshot_id=task["snapshot_id"],
        task_id=task["task_id"],
        execution_id=execution_id,
        attempt=attempt,
        idempotency_key=idempotency_key,
        shadow=True,
        trace_id=agent_execution.get("trace_id"),
    )
    if record.get("status") not in {"ACTIVE", "CANDIDATE_READY"}:
        raise RuntimeError(f"PREIMAGE_SHADOW_EXECUTION_NOT_RUNNABLE: {record.get('status')}")
    started_at = str(request.get("started_at") or execution_now())
    request.update({
        "status": "RUNNING",
        "started_at": started_at,
        "worker_id": worker_id,
        "execution_record_status": record.get("status"),
    })
    host_request_persistence.save(ep, request)
    episode_performance.safe_begin_named_span(
        ep,
        "HOST_ACTION_PREIMAGE_CHARACTER_FINALIZE_SHADOW",
        source="character_finalize_shadow",
        metadata={"request_id": request_id, "execution_id": execution_id},
    )
    return request


def complete_preimage_shadow_task(ep: Path, request_id: str, candidate: dict) -> dict:
    _comparator, preimage_execution_persistence, character_finalize_adapter, AgentRuntime = _shadow_runtime_dependencies()
    request = host_request_persistence.load(ep, request_id)
    if request is None:
        raise FileNotFoundError(f"host request missing: {request_id}")
    if request.get("shadow") is not True or request.get("shadow_kind") != "CHARACTER_FINALIZE_AGENT":
        raise ValueError("not a Character Finalize shadow request")
    if request.get("status") == "FINALIZED" and isinstance(request.get("shadow_candidate"), dict):
        if _stable_hash(request["shadow_candidate"]) != _stable_hash(candidate):
            raise ValueError("PREIMAGE_SHADOW_ALREADY_FINALIZED_DIFFERENT_CANDIDATE")
        task = request["task"]
        execution_meta = request.get("agent_execution") or {}
        execution_id = str(execution_meta.get("execution_id") or "")
        record = preimage_execution_persistence.find_execution(
            ep, task["snapshot_id"], task["task_id"], execution_id
        )
        if record and record.get("status") == "CANDIDATE_READY":
            preimage_execution_persistence.mark_shadow_completed(
                ep,
                snapshot_id=task["snapshot_id"],
                task_id=task["task_id"],
                execution_id=execution_id,
                candidate_sha256=_stable_hash(request["shadow_candidate"]),
                comparison_status=request.get("comparison_status"),
                execution_evidence=dict(request.get("model_execution_evidence") or {}),
            )
        return request
    if request.get("status") != "RUNNING" or not request.get("worker_id"):
        raise ValueError("PREIMAGE_SHADOW_EXECUTION_START_REQUIRED")
    task = request["task"]
    agent_execution = request.get("agent_execution") or {}
    execution_id = str(agent_execution.get("execution_id") or "")
    envelope = character_finalize_adapter.build_execution(
        task,
        attempt=int(agent_execution.get("attempt") or 1),
        shadow=True,
        execution_id=execution_id,
        routing_decision=agent_execution.get("routing_decision") or {},
    )
    runtime = AgentRuntime()
    character_finalize_adapter.register_skill(runtime, lambda _input, _context: candidate)
    result = runtime.execute(envelope.plan)
    shadow_candidate = character_finalize_adapter.extract_candidate(result)
    execution_evidence = character_finalize_adapter.model_execution_evidence(shadow_candidate)
    errors = character_finalize_adapter.validate_candidate(shadow_candidate, task)
    if errors:
        preimage_execution_persistence.mark_shadow_failed(
            ep,
            snapshot_id=task["snapshot_id"],
            task_id=task["task_id"],
            execution_id=execution_id,
            reason="; ".join(errors),
        )
        request.update({
            "status": "FAILED",
            "finished_at": execution_now(),
            "candidate_errors": errors,
            "model_execution_evidence": execution_evidence,
        })
        host_request_persistence.save(ep, request)
        return request
    record = preimage_execution_persistence.find_execution(
        ep, task["snapshot_id"], task["task_id"], execution_id
    )
    if record and record.get("status") == "ACTIVE":
        preimage_execution_persistence.mark_candidate_ready(
            ep,
            snapshot_id=task["snapshot_id"],
            task_id=task["task_id"],
            execution_id=execution_id,
        )
    request.update({
        "status": "FINALIZED",
        "finalized_at": execution_now(),
        "finished_at": execution_now(),
        "shadow_candidate": shadow_candidate,
        "comparison_status": "WAITING_FOR_LEGACY",
        "model_execution_evidence": execution_evidence,
    })
    host_request_persistence.save(ep, request)
    comparison = reconcile_character_shadow(ep, task)
    if comparison is not None:
        request = host_request_persistence.load(ep, request_id) or request
    preimage_execution_persistence.mark_shadow_completed(
        ep,
        snapshot_id=task["snapshot_id"],
        task_id=task["task_id"],
        execution_id=execution_id,
        candidate_sha256=_stable_hash(shadow_candidate),
        comparison_status=request.get("comparison_status"),
        execution_evidence=execution_evidence,
    )
    episode_performance.safe_end_named_span(
        ep,
        "HOST_ACTION_PREIMAGE_CHARACTER_FINALIZE_SHADOW",
        status="PASS",
        metadata={
            "request_id": request_id,
            "structural_equal": (request.get("shadow_comparison") or {}).get("structural_equal"),
        },
    )
    return request


def mark_preimage_world_shadow_running(ep: Path, request_id: str, *, worker_id: str) -> dict:
    _comparator, persistence, _adapter, _runtime_cls = _world_shadow_runtime_dependencies()
    worker_id = str(worker_id or "").strip()
    if not worker_id:
        raise ValueError("worker_id is required")
    request = host_request_persistence.load(ep, request_id)
    if request is None:
        raise FileNotFoundError(f"host request missing: {request_id}")
    if request.get("shadow") is not True or request.get("shadow_kind") != "WORLD_PREPARE_AGENT":
        raise ValueError("not a World Prepare shadow request")
    if request.get("status") not in {"HOST_ACTION_REQUIRED", "RUNNING"}:
        raise ValueError(f"World PREIMAGE shadow request is terminal: {request.get('status')}")
    existing_worker = str(request.get("worker_id") or "").strip()
    if request.get("status") == "RUNNING" and existing_worker and existing_worker != worker_id:
        raise RuntimeError(f"PREIMAGE_WORLD_SHADOW_REQUEST_ALREADY_RUNNING: worker={existing_worker}")
    task = request["task"]
    meta = request.get("agent_execution") or {}
    record = persistence.begin_execution(
        ep, snapshot_id=task["snapshot_id"], task_id=task["task_id"],
        execution_id=str(meta.get("execution_id") or ""),
        attempt=int(meta.get("attempt") or 1),
        idempotency_key=str(meta.get("idempotency_key") or ""),
        shadow=True, trace_id=meta.get("trace_id"),
    )
    if record.get("status") not in {"ACTIVE", "CANDIDATE_READY"}:
        raise RuntimeError(f"PREIMAGE_WORLD_SHADOW_NOT_RUNNABLE: {record.get('status')}")
    request.update({
        "status": "RUNNING",
        "started_at": str(request.get("started_at") or execution_now()),
        "worker_id": worker_id,
        "execution_record_status": record.get("status"),
    })
    host_request_persistence.save(ep, request)
    episode_performance.safe_begin_named_span(
        ep, "HOST_ACTION_PREIMAGE_WORLD_PREPARE_SHADOW", source="world_prepare_shadow",
        metadata={"request_id": request_id, "execution_id": meta.get("execution_id")},
    )
    return request


def complete_preimage_world_shadow_task(ep: Path, request_id: str, candidate: dict) -> dict:
    _comparator, persistence, world_adapter, AgentRuntime = _world_shadow_runtime_dependencies()
    request = host_request_persistence.load(ep, request_id)
    if request is None:
        raise FileNotFoundError(f"host request missing: {request_id}")
    if request.get("shadow") is not True or request.get("shadow_kind") != "WORLD_PREPARE_AGENT":
        raise ValueError("not a World Prepare shadow request")
    if request.get("status") == "FINALIZED" and isinstance(request.get("shadow_candidate"), dict):
        if _stable_hash(request["shadow_candidate"]) != _stable_hash(candidate):
            raise ValueError("PREIMAGE_WORLD_SHADOW_ALREADY_FINALIZED_DIFFERENT_CANDIDATE")
        return request
    if request.get("status") != "RUNNING" or not request.get("worker_id"):
        raise ValueError("PREIMAGE_WORLD_SHADOW_EXECUTION_START_REQUIRED")
    task = request["task"]
    meta = request.get("agent_execution") or {}
    execution_id = str(meta.get("execution_id") or "")
    envelope = world_adapter.build_execution(
        task, attempt=int(meta.get("attempt") or 1), shadow=True,
        execution_id=execution_id, routing_decision=meta.get("routing_decision") or {},
    )
    runtime = AgentRuntime()
    world_adapter.register_skill(runtime, lambda _input, _context: candidate)
    result = runtime.execute(envelope.plan)
    shadow_candidate = world_adapter.extract_candidate(result)
    errors = world_adapter.validate_candidate(shadow_candidate, task)
    execution_evidence = preimage_task_contract.model_execution_evidence(shadow_candidate)
    semantic = _comparator.compare_world_prepare_semantics(task, shadow_candidate)
    if semantic.get("pass") is not True:
        errors.extend(semantic.get("errors") or ["World semantic obligations failed"])
    if errors:
        persistence.mark_shadow_failed(
            ep, snapshot_id=task["snapshot_id"], task_id=task["task_id"],
            execution_id=execution_id, reason="; ".join(errors),
        )
        request.update({
            "status": "FAILED", "finished_at": execution_now(),
            "candidate_errors": errors, "model_execution_evidence": execution_evidence,
            "world_semantic_comparison": semantic,
        })
        host_request_persistence.save(ep, request)
        episode_performance.safe_end_named_span(
            ep, "HOST_ACTION_PREIMAGE_WORLD_PREPARE_SHADOW", status="FAILED",
            metadata={"request_id": request_id},
        )
        return request
    record = persistence.find_execution(ep, task["snapshot_id"], task["task_id"], execution_id)
    if record and record.get("status") == "ACTIVE":
        persistence.mark_candidate_ready(
            ep, snapshot_id=task["snapshot_id"], task_id=task["task_id"], execution_id=execution_id,
        )
    request.update({
        "status": "FINALIZED", "finalized_at": execution_now(), "finished_at": execution_now(),
        "shadow_candidate": shadow_candidate, "comparison_status": "WAITING_FOR_LEGACY",
        "model_execution_evidence": execution_evidence,
        "world_semantic_comparison": semantic,
    })
    host_request_persistence.save(ep, request)
    comparison = reconcile_world_prepare_shadow(ep, task)
    if comparison is not None:
        request = host_request_persistence.load(ep, request_id) or request
    persistence.mark_shadow_completed(
        ep, snapshot_id=task["snapshot_id"], task_id=task["task_id"],
        execution_id=execution_id, candidate_sha256=_stable_hash(shadow_candidate),
        comparison_status=request.get("comparison_status"), execution_evidence=execution_evidence,
    )
    episode_performance.safe_end_named_span(
        ep, "HOST_ACTION_PREIMAGE_WORLD_PREPARE_SHADOW", status="PASS",
        metadata={"request_id": request_id,
                  "comparison_status": request.get("comparison_status")},
    )
    return request


def fail_preimage_world_shadow_task(ep: Path, request_id: str, produced: dict, *, reason: str) -> dict:
    """Persist real producer failure/timeout evidence and close the shadow attempt."""
    _comparator, persistence, _adapter, _runtime_cls = _world_shadow_runtime_dependencies()
    request = host_request_persistence.load(ep, request_id)
    if request is None:
        raise FileNotFoundError(f"World Prepare shadow request missing: {request_id}")
    task = request.get("task") or {}
    meta = request.get("agent_execution") or {}
    execution_id = str(meta.get("execution_id") or "")
    telemetry = dict((produced or {}).get("model_execution") or {})
    if execution_id:
        persistence.mark_shadow_failed(
            ep, snapshot_id=task["snapshot_id"], task_id=task["task_id"],
            execution_id=execution_id, reason=str(reason),
        )
    request.update({
        "status": "FAILED",
        "finished_at": execution_now(),
        "failure_reason": str(reason),
        "model_execution_telemetry": telemetry,
        "model_execution_evidence": preimage_task_contract.model_execution_evidence(
            {"model_execution": telemetry}
        ),
    })
    host_request_persistence.save(ep, request)
    episode_performance.safe_end_named_span(
        ep, "HOST_ACTION_PREIMAGE_WORLD_PREPARE_SHADOW", status="FAILED",
        metadata={"request_id": request_id, "reason": str(reason)},
    )
    return request


def character_shadow_metrics(ep: Path) -> dict:
    import statistics
    rows = [
        row for row in host_request_persistence.list_all(ep)
        if row.get("shadow") is True and row.get("shadow_kind") == "CHARACTER_FINALIZE_AGENT"
    ]
    host_durations = []
    trusted_model_walls = []
    finalized = failed = compared = structural_equal = semantic_review = 0
    telemetry_complete = real_model_execution = model_failures = model_timeouts = 0
    input_tokens = output_tokens = repeated_reads = 0
    for row in rows:
        status = str(row.get("status") or "")
        finalized += int(status == "FINALIZED")
        failed += int(status == "FAILED")
        comparison = row.get("shadow_comparison") or {}
        if row.get("comparison_status") == "COMPARED":
            compared += 1
            structural_equal += int(comparison.get("structural_equal") is True)
            semantic_review += int(comparison.get("needs_semantic_review") is True)
        evidence = row.get("model_execution_evidence") or {}
        if evidence.get("complete") is True:
            telemetry_complete += 1
            real_model_execution += int(evidence.get("real_model_execution") is True)
            model_failures += int(evidence.get("failure") is True)
            model_timeouts += int(evidence.get("timeout") is True)
            input_tokens += int(evidence.get("input_tokens") or 0)
            output_tokens += int(evidence.get("output_tokens") or 0)
            repeated_reads += int(evidence.get("repeated_reads") or 0)
            wall = evidence.get("wall_seconds")
            if isinstance(wall, (int, float)) and not isinstance(wall, bool) and wall >= 0:
                trusted_model_walls.append(float(wall))
        start_raw = row.get("started_at")
        end_raw = row.get("finished_at") or row.get("finalized_at")
        if start_raw and end_raw:
            try:
                start = dt.datetime.fromisoformat(str(start_raw))
                end = dt.datetime.fromisoformat(str(end_raw))
                if end >= start:
                    host_durations.append((end - start).total_seconds())
            except ValueError:
                pass
    return {
        "schema_version": 1,
        "kind": "character_finalize_agent_shadow_metrics",
        "requested": len(rows),
        "started": sum(1 for row in rows if row.get("started_at")),
        "finalized": finalized,
        "failed": failed,
        "compared": compared,
        "structural_equal": structural_equal,
        "needs_semantic_review": semantic_review,
        "host_handshake_median_seconds": statistics.median(host_durations) if host_durations else None,
        "host_handshake_min_seconds": min(host_durations) if host_durations else None,
        "host_handshake_max_seconds": max(host_durations) if host_durations else None,
        "telemetry_complete": telemetry_complete,
        "telemetry_incomplete": max(0, len(rows) - telemetry_complete),
        "real_model_execution": real_model_execution,
        "trusted_model_wall_sample_count": len(trusted_model_walls),
        "trusted_model_median_wall_seconds": statistics.median(trusted_model_walls) if trusted_model_walls else None,
        "trusted_model_min_wall_seconds": min(trusted_model_walls) if trusted_model_walls else None,
        "trusted_model_max_wall_seconds": max(trusted_model_walls) if trusted_model_walls else None,
        "input_tokens_total": input_tokens,
        "output_tokens_total": output_tokens,
        "repeated_reads_total": repeated_reads,
        "model_failures": model_failures,
        "model_timeouts": model_timeouts,
        "model_wall_policy": "explicit_model_execution_evidence_only_never_host_handshake",
        "canonical_side_effect": False,
        "included_in_preimage_concurrency_metric": False,
    }


def world_prepare_shadow_metrics(ep: Path) -> dict:
    rows = [row for row in host_request_persistence.list_all(ep)
            if row.get("shadow") is True and row.get("shadow_kind") == "WORLD_PREPARE_AGENT"]
    comparisons = [row.get("shadow_comparison") or {} for row in rows]
    return {
        "kind": "world_prepare_agent_shadow_metrics",
        "requested": len(rows),
        "finalized": sum(row.get("status") == "FINALIZED" for row in rows),
        "compared": sum(row.get("comparison_status") == "COMPARED" for row in rows),
        "failed": sum(row.get("status") == "FAILED" for row in rows),
        "structural_equal": sum(row.get("structural_equal") is True for row in comparisons),
        "canonical_side_effect": False,
        "included_in_preimage_concurrency_metric": False,
        "telemetry_complete": sum(
            (row.get("model_execution_evidence") or {}).get("complete") is True for row in rows
        ) == len(rows),
    }


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
    if request.get("shadow") is True:
        raise ValueError("shadow PREIMAGE request must use start-preimage-shadow")
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
    if request.get("agent_adapter") == "CHARACTER_FINALIZE_AGENT":
        _comparator, preimage_execution_persistence, _adapter, _runtime_cls = _shadow_runtime_dependencies()
        execution_meta = request.get("agent_execution") or {}
        record = preimage_execution_persistence.begin_execution(
            ep,
            snapshot_id=task["snapshot_id"],
            task_id=task["task_id"],
            execution_id=str(execution_meta.get("execution_id") or ""),
            attempt=int(execution_meta.get("attempt") or 1),
            idempotency_key=str(execution_meta.get("idempotency_key") or ""),
            shadow=False,
            trace_id=execution_meta.get("trace_id"),
        )
        if record.get("status") not in {"ACTIVE", "CANDIDATE_READY"}:
            raise RuntimeError(f"PREIMAGE_AGENT_EXECUTION_NOT_RUNNABLE: {record.get('status')}")
        request["execution_record_status"] = record.get("status")
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
        if (data.get("task") or {}) and data.get("shadow") is not True and str(data.get("next_step") or "").startswith("PREIMAGE_"):
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


def _live_agent_execution_contexts(ep: Path, snapshot_id: str) -> list[dict]:
    contexts=[]
    for row in host_request_persistence.list_all(ep):
        if row.get("shadow") is True or row.get("agent_adapter") != "CHARACTER_FINALIZE_AGENT":
            continue
        task=row.get("task") or {}
        if task.get("snapshot_id") != snapshot_id or row.get("status") != "FINALIZED":
            continue
        if row.get("agent_fallback_active") is True:
            continue
        meta=row.get("agent_execution") or {}
        if not meta.get("execution_id") or not meta.get("idempotency_key"):
            raise RuntimeError("live Character Agent request missing execution identity")
        contexts.append({
            "task_id": task.get("task_id"),
            "execution_id": meta.get("execution_id"),
            "attempt": int(meta.get("attempt") or 1),
            "idempotency_key": meta.get("idempotency_key"),
        })
    unique={str(row["task_id"]):row for row in contexts}
    return list(unique.values())


def complete_preimage_task(ep: Path, request_id: str, candidate: dict) -> dict:
    """Finalize exactly one host task after candidate validation, never a Gate."""
    request=host_request_persistence.load(ep,request_id)
    if request is None: raise FileNotFoundError(f"host request missing: {request_id}")
    if request.get("shadow") is True:
        raise ValueError("shadow PREIMAGE request must use complete-preimage-shadow")
    task=request.get("task") or {}
    if not task or not str(request.get("next_step") or "").startswith("PREIMAGE_"):
        raise ValueError("not a PREIMAGE task request")
    if (request.get("host_contract") or {}).get("execution_start_handshake_required"):
        if request.get("status") != "RUNNING" or not request.get("started_at") or not request.get("worker_id"):
            raise ValueError("PREIMAGE_HOST_EXECUTION_START_REQUIRED")
    agent_live = request.get("agent_adapter") == "CHARACTER_FINALIZE_AGENT"
    if agent_live:
        _comparator, preimage_execution_persistence, character_finalize_adapter, AgentRuntime = _shadow_runtime_dependencies()
        execution_meta = request.get("agent_execution") or {}
        try:
            envelope = character_finalize_adapter.build_execution(
                task,
                attempt=int(execution_meta.get("attempt") or 1),
                shadow=False,
                execution_id=str(execution_meta.get("execution_id") or ""),
                routing_decision=execution_meta.get("routing_decision") or {},
            )
            runtime = AgentRuntime()
            character_finalize_adapter.register_skill(runtime, lambda _input, _context: candidate)
            result = runtime.execute(envelope.plan)
            candidate = character_finalize_adapter.extract_candidate(result)
        except Exception as exc:
            try:
                preimage_execution_persistence.mark_execution_failed(
                    ep,
                    snapshot_id=task["snapshot_id"],
                    task_id=task["task_id"],
                    execution_id=str(execution_meta.get("execution_id") or ""),
                    reason=f"{type(exc).__name__}: {exc}",
                    failure_kind="TECHNICAL",
                )
            except ValueError:
                pass
            if request.get("legacy_fallback_on_technical") is not True:
                raise
            request["agent_fallback_active"] = True
            request["agent_fallback_reason"] = f"{type(exc).__name__}: {exc}"
            host_request_persistence.save(ep, request)
    errors=preimage_task_contract.write_candidate(ep,task,candidate)
    model_execution_evidence=preimage_task_contract.model_execution_evidence(candidate)
    if errors:
        if agent_live and request.get("agent_fallback_active") is not True:
            _comparator, preimage_execution_persistence, _adapter, _runtime_cls = _shadow_runtime_dependencies()
            execution_meta = request.get("agent_execution") or {}
            try:
                preimage_execution_persistence.mark_execution_failed(
                    ep,
                    snapshot_id=task["snapshot_id"],
                    task_id=task["task_id"],
                    execution_id=str(execution_meta.get("execution_id") or ""),
                    reason="; ".join(errors),
                    failure_kind="CONTENT",
                )
            except ValueError:
                pass
        finished_at = execution_now()
        preimage_task_contract.update_task_state(ep,task,"FAILED",request_id=request_id,reason="; ".join(errors),
            execution={"started_at": request.get("started_at"), "worker_id": request.get("worker_id"), "finished_at": finished_at})
        request.update({"status":"FAILED","completed_at":finished_at,"finished_at":finished_at,"candidate_errors":errors})
        request["model_execution_evidence"]=model_execution_evidence
        host_request_persistence.save(ep,request); return request
    finished_at = execution_now()
    preimage_task_contract.update_task_state(ep,task,"COMPLETED",request_id=request_id,candidate_file=task["candidate_output"],
        execution={"started_at": request.get("started_at"), "worker_id": request.get("worker_id"), "finished_at": finished_at})
    request.update({"status":"FINALIZED","finalized_at":finished_at,"finished_at":finished_at,"candidate_path":task["candidate_output"]})
    request["model_execution_evidence"]=model_execution_evidence
    host_request_persistence.save(ep,request)
    if agent_live and request.get("agent_fallback_active") is not True:
        _comparator, preimage_execution_persistence, _adapter, _runtime_cls = _shadow_runtime_dependencies()
        execution_meta = request.get("agent_execution") or {}
        record = preimage_execution_persistence.find_execution(
            ep, task["snapshot_id"], task["task_id"], str(execution_meta.get("execution_id") or "")
        )
        if record and record.get("status") == "ACTIVE":
            preimage_execution_persistence.mark_candidate_ready(
                ep,
                snapshot_id=task["snapshot_id"],
                task_id=task["task_id"],
                execution_id=str(execution_meta.get("execution_id") or ""),
            )
        request["agent_execution_context"] = {
            "task_id": task["task_id"],
            "execution_id": execution_meta.get("execution_id"),
            "attempt": int(execution_meta.get("attempt") or 1),
            "idempotency_key": execution_meta.get("idempotency_key"),
        }
        host_request_persistence.save(ep, request)
    shadow_comparison = reconcile_character_shadow(ep, task)
    if shadow_comparison is not None:
        request["shadow_comparison"] = shadow_comparison
        host_request_persistence.save(ep, request)
    if task.get("task_type") == "WORLD_PREPARE":
        world_shadow_comparison = reconcile_world_prepare_shadow(ep, task)
        if world_shadow_comparison is not None:
            request["shadow_comparison"] = world_shadow_comparison
            host_request_persistence.save(ep, request)
    episode_performance.safe_end_named_span(ep,f"HOST_ACTION_PREIMAGE_{task['task_type']}",status="PASS",metadata={"request_id":request_id})
    # The fourth independently finalized candidate releases only the serial
    # authority commit. Completion of a request never grants a Gate decision.
    snapshot = _read_json(ep / "meta/runtime/preimage-authority-snapshot.json")
    planned = preimage_task_contract.plan_tasks(ep, snapshot, resume=True) if snapshot else []
    if planned and all(item.get("status") == "REUSED" for item in planned):
        execution_contexts = _live_agent_execution_contexts(ep, snapshot["snapshot_id"])
        request["authority_commit"] = preimage_protocol.commit_candidates(
            ep, snapshot, planned, execution_contexts=execution_contexts or None
        )
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
        raise ValueError("product image request requires WORK; workspace access is provided separately")
    workspace = workspace_provider.current()
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
            **workspace.contract_fields(),
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
    assert workspace_provider.current().transport == "WEBCODEX"
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
    p = sub.add_parser("complete-preimage-shadow", help="finalize one Character Finalize Agent shadow candidate without canonical writes")
    p.add_argument("episode_dir")
    p.add_argument("--request-id", required=True)
    p.add_argument("--candidate", required=True)
    p = sub.add_parser("start-preimage-shadow", help="claim one Character Finalize Agent shadow request")
    p.add_argument("episode_dir")
    p.add_argument("--request-id", required=True)
    p.add_argument("--worker-id", required=True)
    p = sub.add_parser("complete-preimage-world-shadow", help="finalize one World Prepare Agent shadow candidate")
    p.add_argument("episode_dir")
    p.add_argument("--request-id", required=True)
    p.add_argument("--candidate", default=None,
                   help="optional prepared Candidate JSON; omitted means Host runs the real read-only Codex producer")
    p = sub.add_parser("start-preimage-world-shadow", help="claim one World Prepare Agent shadow request")
    p.add_argument("episode_dir")
    p.add_argument("--request-id", required=True)
    p.add_argument("--worker-id", required=True)
    p = sub.add_parser("preimage-metrics", help="show observed PREIMAGE Host execution concurrency")
    p.add_argument("episode_dir")
    p = sub.add_parser("preimage-shadow-metrics", help="show Character Finalize Agent shadow comparison metrics")
    p.add_argument("episode_dir")
    p = sub.add_parser("preimage-world-shadow-metrics", help="show World Prepare Agent shadow metrics")
    p.add_argument("episode_dir")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd in {None, "self-test"}:
        self_test(); return 0
    ep = Path(args.episode_dir).resolve()
    if args.cmd == "start-preimage":
        print_request(mark_preimage_task_running(ep, args.request_id, worker_id=args.worker_id)); return 0
    if args.cmd == "start-preimage-shadow":
        print_request(mark_preimage_shadow_running(ep, args.request_id, worker_id=args.worker_id)); return 0
    if args.cmd == "start-preimage-world-shadow":
        print_request(mark_preimage_world_shadow_running(ep, args.request_id, worker_id=args.worker_id)); return 0
    if args.cmd == "complete-preimage-shadow":
        raw = Path(args.candidate)
        candidate_path = raw.resolve() if raw.is_absolute() else (ep / raw).resolve()
        candidate = _read_json(candidate_path)
        result = complete_preimage_shadow_task(ep, args.request_id, candidate)
        print_request(result)
        return 0 if result.get("status") == "FINALIZED" else 2
    if args.cmd == "complete-preimage-world-shadow":
        if args.candidate:
            raw = Path(args.candidate)
            candidate_path = raw.resolve() if raw.is_absolute() else (ep / raw).resolve()
            candidate = _read_json(candidate_path)
        else:
            request = host_request_persistence.load(ep, args.request_id)
            if request is None:
                raise FileNotFoundError(f"World Prepare shadow request missing: {args.request_id}")
            from agents import world_prepare_model_producer
            produced = world_prepare_model_producer.run(ep, request["task"], role="agent_shadow")
            candidate, errors, semantic = world_prepare_host_candidate(request["task"], produced)
            if errors or candidate is None:
                result = fail_preimage_world_shadow_task(
                    ep, args.request_id, produced,
                    reason="; ".join(errors or [str(produced.get("failure_reason") or "World producer failed")]),
                )
                print_request(result)
                return 3
            produced["semantic"] = semantic
            produced["candidate"] = candidate
            request["model_execution_telemetry"] = produced.get("model_execution")
        if not args.candidate and request is not None:
            host_request_persistence.save(ep, request)
        result = complete_preimage_world_shadow_task(ep, args.request_id, candidate)
        print_request(result)
        return 0 if result.get("status") == "FINALIZED" else 2
    if args.cmd == "preimage-metrics":
        print_request(preimage_execution_metrics(ep)); return 0
    if args.cmd == "preimage-shadow-metrics":
        print_request(character_shadow_metrics(ep)); return 0
    if args.cmd == "preimage-world-shadow-metrics":
        print_request(world_prepare_shadow_metrics(ep)); return 0
    raw = Path(args.candidate)
    candidate_path = raw.resolve() if raw.is_absolute() else (ep / raw).resolve()
    candidate = _read_json(candidate_path)
    result = complete_preimage_task(ep, args.request_id, candidate)
    print_request(result)
    return 0 if result.get("status") == "FINALIZED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
