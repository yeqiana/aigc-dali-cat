#!/usr/bin/env python3
"""Run one read-only PREIMAGE Critic smoke against an isolated candidate fixture."""
from __future__ import annotations

import json
import os
import sys
import uuid
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))
sys.path.insert(0, str(SYSTEM / "agents"))


def _bootstrap() -> None:
    from phase9_runtime_launcher import load_runtime_env_file
    env, _source = load_runtime_env_file(ROOT / ".storyos/runtime-launcher/runtime.env", dict(os.environ))
    os.environ.update(env)


def _make_isolated_episode(ep: Path) -> tuple[dict, list[dict]]:
    import preimage_authority_snapshot
    import preimage_task_contract as contract

    (ep / "meta").mkdir(parents=True, exist_ok=False)
    (ep / "meta/story-gates.json").write_text(json.dumps({
        "schema_version": 1,
        "story": {"premise": "A frozen ordinary journey contains no supernatural claim.", "pov": "first_person"},
        "visual": {},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    snapshot = preimage_authority_snapshot.build(ep, write=True, kind="PREIMAGE_INPUT_SNAPSHOT")
    rows = contract.plan_tasks(ep, snapshot)
    for task in rows:
        candidate = contract.candidate_template(task, contract.valid_payload(task))
        errors = contract.write_candidate(ep, task, candidate)
        if errors:
            raise RuntimeError(f"isolated canonical candidate fixture invalid: {task['task_type']}: {errors}")
        contract.update_task_state(ep, task, "COMPLETED", candidate_file=task["candidate_output"])
    resumed = contract.plan_tasks(ep, snapshot, resume=True)
    return snapshot, resumed


def run(retry: int = 0) -> dict:
    _bootstrap()
    # The isolated fixture has no registered MySQL Episode identity. Keep the
    # project bootstrap, then scope only this disposable fixture's review store
    # to the supported JSON backend; no production runtime setting is changed.
    os.environ["STORYOS_EPISODE_META_STORE_MODE"] = "json"
    import preimage_authority_snapshot
    import preimage_task_contract as contract
    import preimage_semantic_critic_adapter as critic
    import product_review_adapter
    import product_runtime_adapter

    suffix = f"-retry{retry}" if retry else ""
    report_path = ROOT / f"reports/p3-preimage-semantic-critic-real-shadow-smoke{suffix}-20260928.json"
    if report_path.exists():
        raise RuntimeError(f"refusing to overwrite prior smoke evidence: {report_path}")
    run_id = uuid.uuid4().hex[:12]
    ep = ROOT / ".storyos" / "p3-preimage-semantic-critic" / f"isolated-smoke-{run_id}"
    snapshot, rows = _make_isolated_episode(ep)
    pointer_before = product_runtime_adapter.load_current_request(ep)
    before_candidates = {
        task["task_type"]: contract.sha(contract.candidate_path(ep, task["task_type"]))
        for task in rows
    }
    capsule = critic.build_frozen_candidate_set(ep, snapshot, rows)
    request = critic.prepare_shadow_request(ep, capsule, attempt=1, review_attempt=1)
    if request is None:
        raise RuntimeError("PREIMAGE Semantic Critic shadow is disabled")
    model, effort = critic.configured_cli_model()
    smoke_error = None
    execution = None
    try:
        execution = critic.execute_shadow_request(ep, attempt=1, timeout=900)
    except Exception as exc:
        smoke_error = f"{type(exc).__name__}: {exc}"
    request_path = product_review_adapter.request_path(ep, critic.REQUEST_KIND, attempt=1)
    pointer_after = product_runtime_adapter.load_current_request(ep)
    source_sha_match = critic.build_frozen_candidate_set(ep, snapshot, rows)["capsule_sha256"] == capsule["capsule_sha256"]
    after_candidates = {
        task["task_type"]: contract.sha(contract.candidate_path(ep, task["task_type"]))
        for task in rows
    }
    telemetry = (execution or {}).get("model_execution") or {}
    checks = {
        "real_model_execution": telemetry.get("real_model_execution") is True,
        "critic_invoked": (execution or {}).get("critic_invoked") is True,
        "telemetry_complete": (execution or {}).get("telemetry_complete") is True,
        "failure": telemetry.get("failure") is True,
        "timeout": telemetry.get("timeout") is True,
        "decision_schema_valid": bool(execution and set(execution.get("decision") or {}) == critic.REQUIRED_DECISION_KEYS),
        "source_sha_match": source_sha_match,
        "obligation_sha_match": capsule["obligation_sha256"] == (execution or {}).get("obligation_sha256"),
        "comparison_completed": bool(execution and isinstance(execution.get("comparison"), dict)),
        "existing_semantic_unchanged": before_candidates == after_candidates,
        "authority_write": (execution or {}).get("authority_write") is True,
        "gate_pass": (execution or {}).get("gate_pass") is True,
        "episode_transition": (execution or {}).get("episode_transition") is True,
        "repair_invoked": (execution or {}).get("repair_invoked") is True,
        "shadow_only": bool(request.get("request_metadata", {}).get("shadow_only")),
        "current_host_pointer_unchanged": pointer_before == pointer_after,
        "image_generation_invoked": False,
    }
    pass_status = (
        checks["real_model_execution"] and checks["critic_invoked"] and checks["telemetry_complete"]
        and telemetry.get("failure") is False and telemetry.get("timeout") is False
        and checks["decision_schema_valid"] and checks["source_sha_match"] and checks["obligation_sha_match"]
        and checks["comparison_completed"] and checks["existing_semantic_unchanged"]
        and not checks["authority_write"] and not checks["gate_pass"] and not checks["episode_transition"]
        and not checks["repair_invoked"] and checks["shadow_only"] and checks["current_host_pointer_unchanged"]
        and not checks["image_generation_invoked"] and telemetry.get("tool_free") is True
    )
    report = {
        "schema_version": 1,
        "kind": "p3_preimage_semantic_critic_real_shadow_smoke",
        "status": "PASS" if pass_status else "FAILED",
        "sample_type": "isolated_fixture_episode",
        "review_persistence_mode": "json_isolated_fixture_after_runtime_env_bootstrap",
        "episode": ep.relative_to(ROOT).as_posix(),
        "snapshot_id": snapshot["snapshot_id"],
        "request_id": request.get("request_id"),
        "request_path": request_path.relative_to(ROOT).as_posix(),
        "request_sha256": critic.digest(request),
        "request_snapshot_path": request.get("request_metadata", {}).get("request_snapshot_path"),
        "request_snapshot_sha256": request.get("request_snapshot_sha256"),
        "candidate_set_sha256": capsule["candidate_set_sha256"],
        "obligation_sha256": capsule["obligation_sha256"],
        "decision_schema_sha256": critic.sha_file(critic.DECISION_SCHEMA),
        "model": model,
        "reasoning_effort": effort,
        "decision": (execution or {}).get("decision"),
        "comparison": (execution or {}).get("comparison"),
        "model_execution": telemetry,
        "checks": checks,
        "image_generation_invoked": False,
        "episode_state": "ISOLATED_FIXTURE_NO_CANONICAL_STATE",
        "failure": smoke_error,
        "paired_benchmark_eligible": pass_status,
        "canonical_authority_modified": False,
        "story_semantic_critic_modified": False,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": report_path.relative_to(ROOT).as_posix(), "status": report["status"],
                      "model": model, "reasoning_effort": effort, "failure": smoke_error}, ensure_ascii=False))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--retry", type=int, default=0)
    args = parser.parse_args()
    result = run(retry=args.retry)
    raise SystemExit(0 if result["status"] == "PASS" else 1)
