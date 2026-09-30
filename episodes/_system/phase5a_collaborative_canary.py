#!/usr/bin/env python3
"""Fixed safety contract for the Phase 5A COLLABORATIVE subpath canary.

This module is not an Episode runner or an alternate stage authority. It only
defines the narrow authorization boundary that a dedicated canary harness may
use. Ordinary Runtime Requests and the normal Runtime DAG cannot opt into this
contract or use it to skip the canonical Visual Lock gate.
"""
from __future__ import annotations

from copy import deepcopy
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any, Mapping


CANARY_ENTRYPOINT = "phase5a_collaborative_canary"
CANARY_TYPE = "PHASE5A_COLLABORATIVE_REGRESSION"

_CONTRACT = MappingProxyType({
    "canary_type": CANARY_TYPE,
    "production_mode": "COLLABORATIVE",
    "scope": "PRODUCTION_SUBPATH",
    "promotable": False,
    "release_eligible": False,
    "stage_authority": False,
    "provider_generation_target": 1,
    "provider_generation_hard_max": 2,
    # This is a harness-only declaration. It is not a production option.
    "requires_visual_lock_stage": False,
})

_FORBIDDEN_REQUEST_KEYS = frozenset({
    "canary_type",
    "canary_scope",
    "skip_visual_lock",
    "requires_visual_lock_stage",
    "promotable",
    "release_eligible",
    "stage_authority",
})

_ALLOWED_ACTIONS = frozenset({
    "RUN_PRODUCTION_SUBPATH",
    "WRITE_CANARY_EVIDENCE",
    "RESUME_PRODUCTION_SUBPATH",
    "RUN_INCREMENTAL_REUSE",
})

_FORBIDDEN_ACTIONS = frozenset({
    "STAGE_PROMOTION",
    "WRITE_CANONICAL_STAGE",
    "WRITE_VISUAL_LOCK_PASS",
    "RELEASE_AUTHORITY_COMMIT",
    "PUBLISH_READY_TRANSITION",
    "PUBLISH",
})

WORKSPACE_REL = Path(".codex_tmp/phase5a")
MARKER_REL = Path("meta/phase5a-canary.json")
GLOBAL_CLAIM_REL = WORKSPACE_REL / ".phase5a-collaborative-canary-claim.json"
ROOT = Path(__file__).resolve().parents[2]


class CanaryContractError(ValueError):
    """Raised when the dedicated non-promotable canary contract is violated."""


def _telemetry(ep: Path, event: str, **attrs: Any) -> None:
    """Best-effort timing evidence; never grants authority or changes outcome."""
    try:
        import runtime_observability

        runtime_observability.safe_record_runtime_event(
            Path(ep), event, source=CANARY_ENTRYPOINT, **attrs
        )
    except Exception:
        return


def contract() -> dict[str, Any]:
    """Return a detached copy of the immutable harness contract."""
    return deepcopy(dict(_CONTRACT))


def workspace_marker(canary_id: str) -> dict[str, str]:
    """Return required non-authoritative workspace labels for a canary run."""
    value = str(canary_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", value) or ".." in value:
        raise CanaryContractError("INVALID_CANARY_ID")
    return {
        "workspace_class": "TEST_ONLY",
        "promotion_class": "NON_PROMOTABLE",
        "canary_type": CANARY_TYPE,
        "canary_id": value,
    }


def initialize_workspace(canary_id: str) -> Path:
    """Create one empty, isolated harness directory and its TEST_ONLY marker."""
    marker = workspace_marker(canary_id)
    repo_root = ROOT.resolve()
    base_requested = ROOT / WORKSPACE_REL
    base = base_requested.resolve()
    try:
        base.relative_to(repo_root)
    except ValueError as exc:
        raise CanaryContractError("CANARY_WORKSPACE_PATH_ESCAPE") from exc
    episode_requested = base_requested / str(canary_id)
    episode = episode_requested.resolve()
    try:
        episode.relative_to(base)
    except ValueError as exc:
        raise CanaryContractError("CANARY_WORKSPACE_PATH_ESCAPE") from exc
    if episode_requested.exists() or episode_requested.is_symlink():
        raise CanaryContractError("CANARY_WORKSPACE_ALREADY_EXISTS")
    episode_requested.mkdir(parents=True)
    marker_path = episode / MARKER_REL
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(json.dumps(marker, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8", newline="\n")
    return episode


def bind_and_freeze(ep: str | Path, request: Mapping[str, Any]) -> dict[str, Any]:
    """Bind an ordinary immutable Runtime Request then freeze its Model Policy."""
    from runtime_request import bind_data, effective_for_episode
    import model_policy

    episode = Path(ep).resolve()
    if not episode.is_relative_to((ROOT / WORKSPACE_REL).resolve()):
        raise CanaryContractError("CANARY_WORKSPACE_PATH_REQUIRED")
    reject_runtime_request_canary_fields(request)
    existing = effective_for_episode(episode)
    if existing is not None and dict(existing) != dict(request):
        raise CanaryContractError("CANARY_RUNTIME_REQUEST_IMMUTABLE")
    bind_data(dict(request), episode)
    bound = effective_for_episode(episode)
    _telemetry(episode, "STEP_FINISHED", step="RUNTIME_REQUEST_BIND", status="SUCCESS",
               evidence_ref=(bound or {}).get("request_id"))
    policy = model_policy_persistence_load(episode)
    if policy is None:
        frozen = model_policy.freeze_for_episode(episode)
        policy = frozen.get("policy") if isinstance(frozen, dict) else None
    if not isinstance(policy, dict):
        raise CanaryContractError("CANARY_MODEL_POLICY_FREEZE_FAILED: missing frozen payload")
    errors = model_policy.validate_bound_policy(episode)
    if errors:
        raise CanaryContractError("CANARY_MODEL_POLICY_FREEZE_FAILED: " + "; ".join(errors))
    _telemetry(episode, "STEP_FINISHED", step="MODEL_POLICY_FREEZE", status="SUCCESS",
               policy_version=policy.get("policy_version"),
               model_policy_sha256=policy.get("policy_sha256"))
    return {"runtime_request_id": bound.get("request_id"),
            "policy_version": policy.get("policy_version"),
            "policy_sha256": policy.get("policy_sha256")}


def model_policy_persistence_load(ep: Path) -> dict | None:
    import model_policy_persistence
    return model_policy_persistence.load(Path(ep).resolve())


def validate_contract(candidate: Mapping[str, Any] | None) -> dict[str, Any]:
    """Require an exact contract; caller-supplied relaxations fail closed."""
    if not isinstance(candidate, Mapping):
        raise CanaryContractError("CANARY_CONTRACT_REQUIRED")
    expected = dict(_CONTRACT)
    if dict(candidate) != expected:
        raise CanaryContractError("CANARY_CONTRACT_MISMATCH")
    return expected


def _contains_forbidden_request_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return bool(_FORBIDDEN_REQUEST_KEYS.intersection(value)) or any(
            _contains_forbidden_request_key(child) for child in value.values()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_forbidden_request_key(child) for child in value)
    return False


def reject_runtime_request_canary_fields(runtime_request: Mapping[str, Any]) -> None:
    """Shared fail-closed guard for Runtime Request bind/validation paths."""
    if not isinstance(runtime_request, Mapping):
        raise CanaryContractError("INVALID_RUNTIME_REQUEST")
    if _contains_forbidden_request_key(runtime_request):
        raise CanaryContractError("RUNTIME_REQUEST_CANNOT_ENABLE_CANARY_BYPASS")


def authorize_entry(
    *,
    entrypoint: str,
    runtime_request: Mapping[str, Any] | None,
    candidate_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Authorize only the dedicated harness; ordinary runtime entrypoints deny.

    The canary marker is intentionally not accepted from a Runtime Request. A
    valid user request may still be bound as input, but it cannot grant bypass
    authority or request a relaxed stage gate.
    """
    if entrypoint != CANARY_ENTRYPOINT:
        raise CanaryContractError("CANARY_ENTRYPOINT_REQUIRED")
    if runtime_request is not None:
        reject_runtime_request_canary_fields(runtime_request)
    return validate_contract(_CONTRACT if candidate_contract is None else candidate_contract)


def authorize_action(action: str) -> str:
    """Allow only subpath actions; stage, Visual Lock, and release writes deny."""
    normalized = str(action or "").strip().upper()
    if normalized in _FORBIDDEN_ACTIONS:
        raise CanaryContractError("CANARY_STAGE_OR_RELEASE_MUTATION_FORBIDDEN")
    if normalized not in _ALLOWED_ACTIONS:
        raise CanaryContractError("CANARY_ACTION_NOT_ALLOWLISTED")
    return normalized


def validate_generation_count(count: int) -> int:
    """Enforce the fixed 2-call ceiling without making it configurable."""
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise CanaryContractError("INVALID_CANARY_GENERATION_COUNT")
    if count > int(_CONTRACT["provider_generation_hard_max"]):
        raise CanaryContractError("CANARY_GENERATION_HARD_MAX_EXCEEDED")
    return count


def claim_global_canary(ep: str | Path, canary_id: str) -> dict[str, Any]:
    """Atomically reserve the single Phase 5A real-canary identity.

    The claim is deliberately persistent: after a crash, only the same marked
    workspace may resume. A second id must not get another real Provider budget.
    """
    episode, _marker = validate_workspace(ep, canary_id)
    claim_path = (ROOT / GLOBAL_CLAIM_REL).resolve()
    try:
        claim_path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise CanaryContractError("CANARY_GLOBAL_CLAIM_PATH_ESCAPE") from exc
    claim_path.parent.mkdir(parents=True, exist_ok=True)
    expected = {
        "canary_type": CANARY_TYPE,
        "canary_id": str(canary_id),
        "workspace": str(episode),
    }
    try:
        descriptor = os.open(str(claim_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        try:
            current = json.loads(claim_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise CanaryContractError("CANARY_GLOBAL_CLAIM_INVALID_FAIL_CLOSED") from exc
        if current != expected:
            raise CanaryContractError("CANARY_GLOBAL_SINGLETON_ALREADY_CLAIMED")
        return {**expected, "resumed": True}
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(expected, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        # Keep a partial claim as a fail-closed marker; never silently free a slot.
        raise CanaryContractError("CANARY_GLOBAL_CLAIM_WRITE_FAILED_FAIL_CLOSED")
    return {**expected, "resumed": False}


def validate_queued_attempt(item: Mapping[str, Any], asset_state: Mapping[str, Any]) -> None:
    """A Phase 5A original queue item may only reserve Attempt 1."""
    if item.get("status") != "queued":
        return
    if asset_state.get("active_attempt_index") is not None:
        raise CanaryContractError("CANARY_GENERATION_ATTEMPT_ALREADY_ACTIVE")
    consumed = int(asset_state.get("attempts_consumed") or 0)
    if item.get("kind") == "original" and consumed > 0:
        raise CanaryContractError("CANARY_ORIGINAL_ITEM_CANNOT_USE_ATTEMPT2")
    if int(asset_state.get("remaining_attempts") or 0) <= 0:
        raise CanaryContractError("CANARY_GENERATION_ATTEMPT_BUDGET_EXHAUSTED")


def _model_execution_receipts(ep: Path) -> list[dict[str, Any]]:
    directory = ep / "meta/provider-receipts/model-executions"
    rows: list[dict[str, Any]] = []
    if not directory.is_dir():
        return rows
    for path in sorted(directory.glob("*.json")):
        try:
            value = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _model_execution_receipt_snapshot(ep: Path) -> dict[str, str]:
    """Return a stable id-to-content digest snapshot for resume call counting."""
    directory = ep / "meta/provider-receipts/model-executions"
    snapshot: dict[str, str] = {}
    if not directory.is_dir():
        return snapshot
    for path in sorted(directory.glob("*.json")):
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        snapshot[path.stem] = hashlib.sha256(raw).hexdigest()
    return snapshot


def _trace_event_count(ep: Path, event_type: str, *, logical_asset_key: str,
                       generation_key: str) -> int:
    import runtime_observability

    path = ep / runtime_observability.TRACE_EVENTS_REL
    if not path.is_file():
        return 0
    count = 0
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        try:
            row = json.loads(raw)
        except ValueError:
            continue
        if (isinstance(row, dict) and row.get("event_type") == event_type
                and row.get("logical_asset_key") == logical_asset_key
                and row.get("generation_key") == generation_key):
            count += 1
    return count


def validate_workspace(ep: str | Path, canary_id: str) -> tuple[Path, dict[str, Any]]:
    """Accept only a marked disposable workspace below the reserved temp root."""
    episode = Path(ep).resolve()
    try:
        relative = episode.relative_to(ROOT)
    except ValueError as exc:
        raise CanaryContractError("CANARY_WORKSPACE_OUTSIDE_REPOSITORY") from exc
    if relative.parts[:len(WORKSPACE_REL.parts)] != WORKSPACE_REL.parts:
        raise CanaryContractError("CANARY_WORKSPACE_PATH_REQUIRED")
    if relative.parts[len(WORKSPACE_REL.parts):] != (str(canary_id),):
        raise CanaryContractError("CANARY_WORKSPACE_ID_MISMATCH")
    marker_path = episode / MARKER_REL
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise CanaryContractError("CANARY_WORKSPACE_MARKER_REQUIRED") from exc
    expected = workspace_marker(canary_id)
    if not isinstance(marker, dict) or marker != expected:
        raise CanaryContractError("CANARY_WORKSPACE_MARKER_INVALID")
    return episode, marker


def _preflight(ep: Path, canary_id: str) -> dict[str, Any]:
    """Check all durable bindings before asking the canonical scheduler to run."""
    import fast_frame_scout
    import frame_contract
    import generation_attempt_authority
    import image_model_policy
    import logical_asset_identity
    import model_policy
    import prompt_package
    import production_queue_store
    import runtime_request
    import scheduler_core
    import storyos_config
    import storage_config

    authorize_entry(entrypoint=CANARY_ENTRYPOINT, runtime_request=None)
    ep, marker = validate_workspace(ep, canary_id)
    authorize_action("RUN_PRODUCTION_SUBPATH")
    cfg = storyos_config.load_config()
    errors = storyos_config.validate(cfg)
    if errors:
        raise CanaryContractError("CONFIG_INVALID: " + "; ".join(str(x) for x in errors))
    mode = storyos_config.get_path(cfg, "production.mode")
    if mode != "COLLABORATIVE":
        raise CanaryContractError("CANARY_REQUIRES_COLLABORATIVE_MODE")
    mysql = storage_config.mysql_connection_kwargs()
    if (str(mysql.get("host")) not in {"127.0.0.1", "localhost"}
            or int(mysql.get("port") or 0) != 3306
            or str(mysql.get("database")) != "story_os_runtime"):
        raise CanaryContractError("CANARY_TEST_ONLY_MYSQL_REQUIRED")
    if (ep / "meta/episode-state.json").exists():
        raise CanaryContractError("CANARY_CANONICAL_STAGE_AUTHORITY_FORBIDDEN")
    if not (ep / "meta/release-manifest.json").is_file():
        raise CanaryContractError("CANARY_FRAME_CONTRACT_INPUTS_MISSING")
    bound_request = runtime_request.effective_for_episode(ep)
    if not bound_request:
        raise CanaryContractError("CANARY_RUNTIME_REQUEST_NOT_BOUND")
    errors = model_policy.validate_bound_policy(ep)
    if errors:
        raise CanaryContractError("CANARY_MODEL_POLICY_NOT_FROZEN: " + "; ".join(errors))
    controller = model_policy.resolve("image.controller", episode=ep)
    reviewer = model_policy.resolve("vision.final", episode=ep)
    payload = image_model_policy.for_episode(ep)
    if (controller.get("model"), controller.get("reasoning_effort")) != ("gpt-6-luna", "high"):
        raise CanaryContractError("CANARY_CONTROLLER_BINDING_MISMATCH")
    if (payload.get("model"), payload.get("quality")) != ("gpt-image-2.5-flare", "high"):
        raise CanaryContractError("CANARY_PAYLOAD_BINDING_MISMATCH")
    if (reviewer.get("model"), reviewer.get("reasoning_effort")) != ("gpt-6-luna", "high"):
        raise CanaryContractError("CANARY_REVIEW_BINDING_MISMATCH")
    queue = scheduler_core.load_queue(ep)
    items = [row for row in queue.get("items") or [] if isinstance(row, dict)]
    if len(items) != 1:
        raise CanaryContractError("CANARY_REQUIRES_EXACTLY_ONE_QUEUE_ITEM")
    item = items[0]
    if int(item.get("frame") or 0) != 1 or str(item.get("scope") or "") != "batch":
        raise CanaryContractError("CANARY_QUEUE_ITEM_MUST_BE_SINGLE_PRODUCTION_FRAME")
    if str(item.get("kind") or "") != "original":
        raise CanaryContractError("CANARY_QUEUE_ITEM_KIND_INVALID")
    if item.get("status") not in {"queued", "generated"}:
        raise CanaryContractError("CANARY_QUEUE_ITEM_NOT_RUNNABLE_OR_COMPLETE")
    if not item.get("prompt_package"):
        raise CanaryContractError("CANARY_PRODUCTION_PROMPT_NOT_COMPILED_FROM_CONTRACT")
    prompt_raw = str(item.get("prompt_file") or "").strip()
    if not prompt_raw:
        raise CanaryContractError("CANARY_PRODUCTION_PROMPT_SOURCE_MISSING")
    prompt_path = Path(prompt_raw)
    prompt_path = prompt_path if prompt_path.is_absolute() else (ROOT / prompt_path).resolve()
    if not prompt_path.is_file():
        raise CanaryContractError("CANARY_PRODUCTION_PROMPT_SOURCE_MISSING")
    try:
        compiled_contract = frame_contract.compile_frame(ep, 1, write_cache=False)
        compiled_prompt = prompt_package.compile_frame(ep, 1, prompt_path, write=False)
    except Exception as exc:
        raise CanaryContractError(f"CANARY_PRODUCTION_INPUT_COMPILE_FAILED: {exc}") from exc
    frame_contract_sha = str(compiled_contract.get("contract_sha256") or "").lower()
    queued_contract_sha = str(((item.get("frame_contract") or {}).get("contract_sha256")) or "").lower()
    prompt_package_sha = str(compiled_prompt.get("package_sha256") or "").lower()
    queued_package_sha = str(((item.get("prompt_package") or {}).get("package_sha256")) or "").lower()
    if not frame_contract_sha or frame_contract_sha != queued_contract_sha:
        raise CanaryContractError("CANARY_FRAME_CONTRACT_SOURCE_BINDING_MISMATCH")
    if (not prompt_package_sha or prompt_package_sha != queued_package_sha
            or compiled_prompt.get("frame_contract_sha256") != frame_contract_sha):
        raise CanaryContractError("CANARY_PROMPT_PACKAGE_SOURCE_BINDING_MISMATCH")
    if not fast_frame_scout.required(ep):
        raise CanaryContractError("CANARY_REVIEW_LANE_NOT_REQUIRED")
    key = logical_asset_identity.frame_asset_key(ep, 1)
    asset_state = generation_attempt_authority.load_asset_state(ep, key)
    validate_generation_count(asset_state["attempts_consumed"])
    # A completed queue item is safe to resume/reconcile. A queued item may be
    # run only when no lease is active and the hard ceiling still has capacity.
    validate_queued_attempt(item, asset_state)
    return {
        "episode": ep,
        "marker": marker,
        "runtime_request_id": bound_request.get("request_id"),
        "policy_version": controller.get("policy_version"),
        "policy_sha256": controller.get("model_policy_sha256"),
        "controller": {"model": controller.get("model"), "effort": controller.get("reasoning_effort")},
        "reviewer": {"model": reviewer.get("model"), "effort": reviewer.get("reasoning_effort"),
                     "profile": reviewer.get("profile")},
        "payload": {"model": payload.get("model"), "quality": payload.get("quality")},
        "logical_asset_key": key,
        "frame_contract_sha256": frame_contract_sha,
        "prompt_package_sha256": prompt_package_sha,
        "attempt_state": asset_state,
        "queue_item_id": item.get("id"),
        "queue_item_status": item.get("status"),
        "queue_authority": production_queue_store.authority(ep),
    }


def run_production_subpath(ep: str | Path, *, canary_id: str, timeout: int = 900,
                           codex: str | None = None, dry_run: bool = False) -> dict[str, Any]:
    """Run/resume exactly one item through the existing Production Scheduler.

    The harness owns no Stage, Release, Attempt, Provider, or Review authority.
    """
    preflight = _preflight(Path(ep), canary_id)
    if dry_run:
        return {"status": "READY", **{k: v for k, v in preflight.items() if k != "episode"}}
    global_claim = claim_global_canary(preflight["episode"], canary_id)
    import runtime_trace
    run_id = f"phase5a-{canary_id}"
    trace_id = runtime_trace.start_run(
        preflight["episode"], run_id, {"request_id": preflight["runtime_request_id"]},
        runtime="COLLABORATIVE", route_decision={"entry_step": "PRODUCTION_SUBPATH_CANARY"})
    _telemetry(preflight["episode"], "CANARY_RUN_STARTED",
               logical_asset_key=preflight["logical_asset_key"],
               model_policy_sha256=preflight["policy_sha256"],
               run_id=run_id, trace_id=trace_id, step="PHASE5A_CANARY",
               status="RUNNING")
    stage_path = preflight["episode"] / "meta/episode-state.json"
    before_stage = stage_path.read_bytes() if stage_path.is_file() else None
    release_path = preflight["episode"] / "meta/release-manifest.json"
    before_release = release_path.read_bytes() if release_path.is_file() else None
    import image_scheduler
    try:
        rc = image_scheduler.run_scheduler_async(preflight["episode"], max_workers=1,
                                                 timeout=int(timeout), codex=codex)
    except Exception as exc:
        original_exc = exc
        after_stage = stage_path.read_bytes() if stage_path.is_file() else None
        after_release = release_path.read_bytes() if release_path.is_file() else None
        if before_stage != after_stage:
            observed_exc = CanaryContractError("CANARY_STAGE_STATE_FILE_CHANGED_DURING_FAILED_RUN")
        elif before_release != after_release:
            observed_exc = CanaryContractError("CANARY_RELEASE_MANIFEST_CHANGED_DURING_FAILED_RUN")
        else:
            observed_exc = original_exc
        _telemetry(preflight["episode"], "CANARY_RUN_FINISHED",
                   logical_asset_key=preflight["logical_asset_key"], status="FAILED",
                   failure_class=type(observed_exc).__name__, run_id=run_id, trace_id=trace_id,
                   step="PHASE5A_CANARY", reason="scheduler_exception")
        runtime_trace.finish_run(preflight["episode"], trace_id, run_id, "FAILED",
                                 note=type(observed_exc).__name__)
        if observed_exc is not original_exc:
            raise observed_exc from original_exc
        raise
    after_state = __import__("generation_attempt_authority").load_asset_state(
        preflight["episode"], preflight["logical_asset_key"])
    validate_generation_count(after_state["attempts_consumed"])
    after_stage = stage_path.read_bytes() if stage_path.is_file() else None
    after_release = release_path.read_bytes() if release_path.is_file() else None
    stage_state_file_changed = before_stage != after_stage
    release_manifest_changed = before_release != after_release
    if after_stage is not None or stage_state_file_changed:
        raise CanaryContractError("CANARY_STAGE_AUTHORITY_MUTATED")
    if release_manifest_changed:
        raise CanaryContractError("CANARY_RELEASE_AUTHORITY_MUTATED")
    queue = image_scheduler.load_queue(preflight["episode"])
    item = next((row for row in queue.get("items") or []
                 if row.get("id") == preflight["queue_item_id"]), {})
    review = next((row for row in queue.get("review_work_items") or []
                   if row.get("generation_key") == item.get("generation_key")
                   and row.get("logical_asset_key") == preflight["logical_asset_key"]), {})
    result = {
        "status": "BLOCKED",
        "scheduler_rc": int(rc),
        "queue_item_status": item.get("status"),
        "generation_key": item.get("generation_key"),
        "attempt_index": item.get("attempt_index"),
        "review_status": review.get("status"),
        "review_receipt": review.get("receipt"),
        "attempt_state": after_state,
        "stage_state_file_present_after_run": after_stage is not None,
        "stage_state_file_changed_during_run": stage_state_file_changed,
        "release_manifest_changed_during_run": release_manifest_changed,
        "global_canary_claim": global_claim,
        "preflight": {k: v for k, v in preflight.items() if k != "episode"},
    }
    # Fast Scout is early triage only. Enqueue final semantic work into the
    # existing durable Review Lane and let the canonical Scheduler consume it.
    # The harness never invokes the Critic directly.
    if rc == 0 and item.get("status") == "generated" and review.get("status") == "finalized":
        import incremental_frame_review
        import production_ledger
        import review_queue
        import scheduler_core

        artifact_rel = str(item.get("output_path") or "").strip()
        artifact = (Path(artifact_rel) if Path(artifact_rel).is_absolute()
                    else (ROOT / artifact_rel).resolve())
        if not artifact_rel or not artifact.is_file():
            raise CanaryContractError("CANARY_COMMITTED_ARTIFACT_MISSING")
        with scheduler_core.queue_transaction(preflight["episode"]):
            q = scheduler_core.load_queue(preflight["episode"])
            current_item = next((row for row in q.get("items") or []
                                 if row.get("id") == preflight["queue_item_id"]), {})
            enqueued_final = review_queue.enqueue_final_semantic(
                q, episode=preflight["episode"], source_item=current_item,
                artifact=artifact, artifact_path=artifact_rel)
            if enqueued_final.get("status") not in {"ENQUEUED", "ALREADY_ENQUEUED"}:
                raise CanaryContractError("CANARY_FINAL_REVIEW_ENQUEUE_FAILED: "
                                          + str(enqueued_final.get("reason") or enqueued_final.get("status")))
            scheduler_core.save_queue(preflight["episode"], q)

        receipts_before_final = {row.get("call_id") for row in _model_execution_receipts(preflight["episode"])}
        final_scheduler_rc = image_scheduler.run_scheduler_async(
            preflight["episode"], max_workers=1, timeout=int(timeout), codex=codex)
        queue = image_scheduler.load_queue(preflight["episode"])
        review = next((row for row in queue.get("review_work_items") or []
                       if row.get("review_kind") == review_queue.FINAL_SEMANTIC
                       and row.get("generation_key") == item.get("generation_key")
                       and row.get("logical_asset_key") == preflight["logical_asset_key"]), {})
        semantic_receipt = review.get("receipt") or {}
        final_receipt = semantic_receipt.get("critic_receipt") or {}
        semantic_errors = ([] if review.get("status") == "finalized"
                           and semantic_receipt.get("review_outcome") in {"PASS", "REPAIR_NEEDED", "NEEDS_USER"}
                           else [str(semantic_receipt.get("notes") or "FINAL_SEMANTIC_REVIEW_NOT_TERMINAL")])
        incremental_rc = (incremental_frame_review.run_review(
            preflight["episode"], attempt=int(item.get("attempt_index") or 1),
            codex_raw=codex, timeout=int(timeout))
            if not semantic_errors and semantic_receipt.get("review_outcome") == "PASS" else None)
        incremental_plan = (incremental_frame_review.build_plan(preflight["episode"])
                            if incremental_rc == 0 else {})
        final_ledger = production_ledger.load_authority(preflight["episode"], default={}) or {}
        final_frame = ((final_ledger.get("frames") or {}).get("01") or {})
        bound_review = __import__("model_policy").resolve("vision.final", episode=preflight["episode"])
        # On first execution this is the newly written call; after a safe
        # resume it is the same persisted call embedded in the adopted Queue
        # Receipt. In either case validate the exact model execution evidence.
        all_final_receipts = [row for row in _model_execution_receipts(preflight["episode"])
                              if row.get("model_role") == "vision.final"
                              and row.get("generation_key") == item.get("generation_key")
                              and row.get("artifact_sha256") == semantic_receipt.get("artifact_sha256")]
        embedded_call_id = str(final_receipt.get("call_id") or "")
        final_receipts = [row for row in all_final_receipts
                          if embedded_call_id and row.get("call_id") == embedded_call_id]
        receipt_contract_pass = (
            int(final_scheduler_rc) == 0
            and review.get("status") == "finalized"
            and semantic_receipt.get("review_outcome") == "PASS"
            and semantic_receipt.get("generation_key") == item.get("generation_key")
            and semantic_receipt.get("artifact_sha256") == final_receipt.get("artifact_sha256")
            and final_receipt.get("status") == "SUCCESS"
            and final_receipt.get("model_role") == "vision.final"
            and final_receipt.get("profile") == bound_review.get("profile")
            and final_receipt.get("effective_model") == bound_review.get("model")
            and final_receipt.get("reasoning_effort") == bound_review.get("reasoning_effort")
            and final_receipt.get("model_policy_sha256") == preflight["policy_sha256"]
            and final_receipt.get("logical_asset_key") == preflight["logical_asset_key"]
            and final_receipt.get("generation_key") == item.get("generation_key")
            and int(final_receipt.get("attempt_index") or 0) == int(item.get("attempt_index") or 0)
            and final_receipt.get("artifact_sha256") == semantic_receipt.get("artifact_sha256")
            and final_receipt.get("effective_model_source") == "EXPLICIT_RUNTIME_BINDING"
            and len(final_receipts) == 1
            and len(all_final_receipts) == 1
        )
        receipt_is_adopted = bool(semantic_receipt.get("reused_official_evidence"))
        review_receipt_pass = (receipt_contract_pass and (
            receipt_is_adopted
            or final_receipts[0].get("call_id") not in receipts_before_final
        ))
        semantic_pass = (not semantic_errors
                         and final_frame.get("status") in production_ledger.ACCEPTED_LEDGER_STATES
                         and review_receipt_pass
                         and incremental_rc == 0
                         and incremental_plan.get("action") == "NOOP"
                         and "01" in (incremental_plan.get("reused_frames") or []))
        result.update({
            "final_semantic_enqueue_status": enqueued_final.get("status"),
            "final_semantic_scheduler_rc": int(final_scheduler_rc),
            "final_semantic_queue_status": review.get("status"),
            "final_semantic_queue_receipt": semantic_receipt,
            "final_semantic_errors": semantic_errors,
            "final_semantic_status": final_frame.get("status"),
            "final_semantic_model_receipts": final_receipts,
            "final_semantic_receipt_pass": review_receipt_pass,
            "incremental_review_rc": incremental_rc,
            "incremental_plan": incremental_plan,
            "real_evidence_reused": semantic_pass,
            "additional_critic_calls_after_reuse": 0 if semantic_pass else None,
        })
        if semantic_pass:
            # Safe scheduler resume after final evidence is persisted must leave
            # the Authority row and finalized Review item unchanged.
            before_consumed = int(after_state.get("attempts_consumed") or 0)
            before_generation_key = str(item.get("generation_key") or "")
            import runtime_observability
            trace_path = preflight["episode"] / runtime_observability.TRACE_EVENTS_REL
            before_review_starts = _trace_event_count(
                preflight["episode"], "REVIEW_STARTED",
                logical_asset_key=preflight["logical_asset_key"], generation_key=before_generation_key)
            before_worker_dispatches = _trace_event_count(
                preflight["episode"], "WORKER_DISPATCH_COMMITTED",
                logical_asset_key=preflight["logical_asset_key"], generation_key=before_generation_key)
            before_model_receipts = _model_execution_receipt_snapshot(preflight["episode"])
            before_review_model_receipt_count = sum(
                1 for row in _model_execution_receipts(preflight["episode"])
                if row.get("model_role") in {"vision.final", "final_semantic"}
            )
            before_review_key = (str(review.get("generation_key") or ""),
                                 str((review.get("receipt") or {}).get("artifact_sha256") or ""),
                                 str(review.get("review_kind") or ""))
            resume_rc = image_scheduler.run_scheduler_async(
                preflight["episode"], max_workers=1, timeout=int(timeout), codex=codex)
            resumed_state = __import__("generation_attempt_authority").load_asset_state(
                preflight["episode"], preflight["logical_asset_key"])
            resumed_queue = image_scheduler.load_queue(preflight["episode"])
            resumed_item = next((row for row in resumed_queue.get("items") or []
                                 if row.get("id") == preflight["queue_item_id"]), {})
            resumed_review = next((row for row in resumed_queue.get("review_work_items") or []
                                   if row.get("generation_key") == before_generation_key
                                   and row.get("logical_asset_key") == preflight["logical_asset_key"]
                                   and row.get("review_kind") == review_queue.FINAL_SEMANTIC), {})
            after_review_starts = _trace_event_count(
                preflight["episode"], "REVIEW_STARTED",
                logical_asset_key=preflight["logical_asset_key"], generation_key=before_generation_key)
            after_worker_dispatches = _trace_event_count(
                preflight["episode"], "WORKER_DISPATCH_COMMITTED",
                logical_asset_key=preflight["logical_asset_key"], generation_key=before_generation_key)
            after_model_receipts = _model_execution_receipt_snapshot(preflight["episode"])
            after_review_model_receipt_count = sum(
                1 for row in _model_execution_receipts(preflight["episode"])
                if row.get("model_role") in {"vision.final", "final_semantic"}
            )
            provider_redispatch_count = after_worker_dispatches - before_worker_dispatches
            review_redispatch_count = after_review_model_receipt_count - before_review_model_receipt_count
            resume_pass = (
                resume_rc == 0
                and int(resumed_state.get("attempts_consumed") or 0) == before_consumed
                and resumed_item.get("generation_key") == before_generation_key
                and resumed_review.get("status") == "finalized"
                and (str(resumed_review.get("generation_key") or ""),
                     str((resumed_review.get("receipt") or {}).get("artifact_sha256") or ""),
                     str(resumed_review.get("review_kind") or "")) == before_review_key
                and after_review_starts == before_review_starts
                and before_worker_dispatches >= 1
                and provider_redispatch_count == 0
                and review_redispatch_count == 0
                and after_model_receipts == before_model_receipts
            )
            result["resume"] = {
                "scheduler_rc": int(resume_rc),
                "provider_redispatch_count_observed": provider_redispatch_count,
                "review_redispatch_count_observed": review_redispatch_count,
                "worker_dispatch_commits_before": before_worker_dispatches,
                "worker_dispatch_commits_after": after_worker_dispatches,
                "model_execution_receipt_count_before": len(before_model_receipts),
                "model_execution_receipt_count_after": len(after_model_receipts),
                "model_execution_receipts_unchanged": after_model_receipts == before_model_receipts,
                "review_model_receipt_count_before": before_review_model_receipt_count,
                "review_model_receipt_count_after": after_review_model_receipt_count,
                "generation_key_unchanged": resumed_item.get("generation_key") == before_generation_key,
                "attempts_consumed_unchanged": int(resumed_state.get("attempts_consumed") or 0) == before_consumed,
            }
            result["review_queue_start_events_before_resume"] = before_review_starts
            result["review_queue_start_events_after_resume"] = after_review_starts
            if resume_pass:
                result["status"] = "PASS"
    _telemetry(preflight["episode"], "CANARY_RUN_FINISHED",
               status=result["status"], logical_asset_key=preflight["logical_asset_key"],
               generation_key=item.get("generation_key"), attempt_index=item.get("attempt_index"),
               evidence_ref=str((review.get("receipt") or {}).get("critic_log") or ""),
               reason=str(result.get("final_semantic_status") or review.get("status") or ""),
               step="PHASE5A_CANARY", run_id=run_id, trace_id=trace_id)
    runtime_trace.finish_run(preflight["episode"], trace_id, run_id, result["status"],
                             note="Phase 5A non-promotable production subpath canary")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run or safely resume one prepared Phase 5A canary asset")
    run.add_argument("episode_dir", type=Path)
    run.add_argument("--canary-id", required=True)
    run.add_argument("--timeout", type=int, default=900)
    run.add_argument("--codex")
    run.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = run_production_subpath(args.episode_dir, canary_id=args.canary_id,
                                        timeout=args.timeout, codex=args.codex,
                                        dry_run=args.dry_run)
    except Exception as exc:
        result = {"status": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"}
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get("status") in {"READY", "PASS"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
