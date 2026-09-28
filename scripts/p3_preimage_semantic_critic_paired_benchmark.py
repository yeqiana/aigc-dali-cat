#!/usr/bin/env python3
"""Balanced five-case PREIMAGE semantic Critic paired benchmark."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))
sys.path.insert(0, str(SYSTEM / "agents"))


def _bootstrap() -> None:
    from phase9_runtime_launcher import load_runtime_env_file
    env, _source = load_runtime_env_file(ROOT / ".storyos/runtime-launcher/runtime.env", dict(os.environ))
    os.environ.update(env)
    os.environ["STORYOS_EPISODE_META_STORE_MODE"] = "json"


def _fixture_episode(ep: Path, case: dict):
    import preimage_authority_snapshot
    import preimage_task_contract as contract

    (ep / "meta").mkdir(parents=True, exist_ok=False)
    (ep / "meta/story-gates.json").write_text(json.dumps({
        "schema_version": 1,
        "story": {"premise": "Frozen PREIMAGE comparison fixture.", "pov": "first_person"},
        "visual": {},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    snapshot = preimage_authority_snapshot.build(ep, write=True, kind="PREIMAGE_INPUT_SNAPSHOT")
    rows = contract.plan_tasks(ep, snapshot)
    mutation = case.get("mutations") or {}
    for task in rows:
        payload = contract.valid_payload(task)
        kind = task["task_type"]
        if kind == "CHARACTER_FINALIZE":
            value = payload["character.finalize"]
            value["identity"] = mutation.get("character_identity", "person-a")
            value["pov"] = mutation.get("character_pov", "first_person")
            value["wardrobe"] = "dark coat"
        elif kind == "WORLD_PREPARE":
            if mutation.get("world_applicable") is False:
                pass
            else:
                for value in payload.values():
                    value.clear()
                    value.update({"rule": "frozen-world-contract", "applicable": True})
                payload["visual.world_identity"]["identity"] = mutation.get("world_identity", "person-a")
                payload["visual.temporal_continuity"]["time_of_day"] = mutation.get("world_time_of_day", "morning")
                payload["visual.wardrobe"]["wardrobe"] = "dark coat"
        elif kind == "ENVIRONMENT_PREPARE":
            payload["visual.environment_contract"]["baseline"]["time_of_day"] = mutation.get("environment_time_of_day", "morning")
        elif kind == "VISUAL_NARRATIVE_PREPARE":
            payload["visual.capture_grammar"]["pov"] = mutation.get("capture_pov", "first_person")
        candidate = contract.candidate_template(task, payload)
        errors = contract.write_candidate(ep, task, candidate)
        if errors:
            raise RuntimeError(f"fixture candidate failed existing verifier for {kind}: {errors}")
        contract.update_task_state(ep, task, "COMPLETED", candidate_file=task["candidate_output"])
    return snapshot, contract.plan_tasks(ep, snapshot, resume=True)


def run() -> dict:
    _bootstrap()
    import preimage_semantic_critic_adapter as critic

    sample_path = ROOT / "tests/fixtures/p3_preimage_semantic_critic/cases.json"
    sample_set = json.loads(sample_path.read_text(encoding="utf-8-sig"))
    cases = sample_set["cases"]
    if len(cases) < 5 or sum(row["reference_label"] == "PASS" for row in cases) < 2 or sum(row["reference_label"] == "FAIL" for row in cases) < 2:
        raise RuntimeError("benchmark fixture set is not balanced with five distinct samples")
    report_path = ROOT / "reports/p3-preimage-semantic-critic-paired-benchmark-20260928.json"
    if report_path.exists():
        raise RuntimeError(f"refusing to overwrite benchmark evidence: {report_path}")
    model, effort = critic.configured_cli_model()
    if not model or not effort:
        raise RuntimeError("active Codex model/reasoning effort is not observable")
    root = ROOT / ".storyos/p3-preimage-semantic-critic/benchmark-20260928"
    rows = []
    for case in cases:
        ep = root / case["sample_id"]
        snapshot, tasks = _fixture_episode(ep, case)
        capsule = critic.build_frozen_candidate_set(ep, snapshot, tasks)
        request = critic.prepare_shadow_request(ep, capsule, attempt=1, review_attempt=1)
        result = None
        failure = None
        try:
            result = critic.execute_shadow_request(
                ep, attempt=1, timeout=900, reference_label=case["reference_label"],
                reference_issue_codes=case["reference_issue_codes"],
            )
        except Exception as exc:
            failure = f"{type(exc).__name__}: {exc}"
        decision = (result or {}).get("decision") or {}
        telemetry = (result or {}).get("model_execution") or {}
        existing_decision = "ACCEPT_CANDIDATE"
        critic_decision = decision.get("decision")
        reference = case["reference_label"]
        expected_issues = set(case["reference_issue_codes"])
        observed_issues = set(decision.get("issue_codes") or [])
        repair_scope = set(decision.get("repair_scope") or [])
        expected_scope = set(case.get("repair_scope") or [])
        rows.append({
            "sample_id": case["sample_id"],
            "sample_type": "deterministic_fixture",
            "reference_label": reference,
            "reference_issue_codes": sorted(expected_issues),
            "existing_semantic_decision": existing_decision,
            "critic_decision": critic_decision,
            "decision_equivalent": critic_decision == existing_decision if critic_decision else None,
            "existing_issue_codes": [],
            "critic_issue_codes": sorted(observed_issues),
            "issue_intersection": sorted(expected_issues & observed_issues),
            "critic_extra_issues": sorted(observed_issues - expected_issues),
            "critic_missing_issues": sorted(expected_issues - observed_issues),
            "false_accept_existing": reference == "FAIL" and existing_decision == "ACCEPT_CANDIDATE",
            "false_accept_critic": reference == "FAIL" and critic_decision == "ACCEPT_CANDIDATE" if critic_decision else None,
            "false_reject_existing": reference == "PASS" and existing_decision != "ACCEPT_CANDIDATE",
            "false_reject_critic": reference == "PASS" and critic_decision not in {None, "ACCEPT_CANDIDATE"},
            "missed_issue_count_existing": len(expected_issues),
            "missed_issue_count_critic": len(expected_issues - observed_issues),
            "repair_scope_precision": len(repair_scope & expected_scope) / len(repair_scope) if decision.get("decision") == "REPAIR" and repair_scope else None,
            "repair_scope_expected": sorted(expected_scope),
            "repair_scope_observed": sorted(repair_scope),
            "schema_valid": bool(result and result.get("decision")),
            "wall_seconds": telemetry.get("wall_seconds"),
            "input_tokens": telemetry.get("input_tokens"),
            "cached_input_tokens": telemetry.get("cached_input_tokens"),
            "output_tokens": telemetry.get("output_tokens"),
            "reasoning_output_tokens": telemetry.get("reasoning_output_tokens"),
            "total_tokens": (telemetry.get("input_tokens") + telemetry.get("output_tokens")) if isinstance(telemetry.get("input_tokens"), int) and isinstance(telemetry.get("output_tokens"), int) else None,
            "failure": failure,
            "timeout": telemetry.get("timeout"),
            "provider": telemetry.get("provider"),
            "model": telemetry.get("model"),
            "reasoning_effort": effort,
            "request_sha": critic.digest(request),
            "candidate_sha": capsule["candidate_set_sha256"],
            "obligation_sha": capsule["obligation_sha256"],
            "authority_write": False,
            "episode_transition": False,
        })
    valid = [row for row in rows if row["schema_valid"] and row["failure"] is None and row["timeout"] is False]
    false_accept_existing = sum(bool(row["false_accept_existing"]) for row in valid)
    false_accept_critic = sum(bool(row["false_accept_critic"]) for row in valid)
    false_reject_existing = sum(bool(row["false_reject_existing"]) for row in valid)
    false_reject_critic = sum(bool(row["false_reject_critic"]) for row in valid)
    missed_existing = sum(int(row["missed_issue_count_existing"]) for row in valid)
    missed_critic = sum(int(row["missed_issue_count_critic"]) for row in valid)
    pass_rows = [row for row in valid if row["reference_label"] == "PASS"]
    quality_value = (
        (false_accept_critic < false_accept_existing or missed_critic < missed_existing)
        and false_reject_critic <= false_reject_existing
        and all(row["false_reject_critic"] is False for row in pass_rows)
    )
    walls = sorted(row["wall_seconds"] for row in valid if isinstance(row["wall_seconds"], (int, float)))
    tokens = sorted(row["total_tokens"] for row in valid if isinstance(row["total_tokens"], int))
    median = lambda values: (values[len(values)//2] if len(values) % 2 else (values[len(values)//2-1] + values[len(values)//2]) / 2) if values else None
    telemetry_complete = len(valid) == len(rows) and all(
        all(row.get(key) is not None for key in ("wall_seconds", "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "timeout", "provider", "model"))
        for row in valid
    )
    fixed = all(row.get("provider") == "codex_user_runner" and row.get("model") == model and row.get("reasoning_effort") == effort for row in valid)
    authority_zero = all(row["authority_write"] is False and row["episode_transition"] is False for row in rows)
    safety = len(valid) >= 5 and telemetry_complete and fixed and authority_zero
    report = {
        "schema_version": 1,
        "kind": "p3_preimage_semantic_critic_paired_benchmark",
        "status": "COMPLETE" if len(valid) == len(rows) else "INCOMPLETE",
        "sample_set_path": sample_path.relative_to(ROOT).as_posix(),
        "sample_set_sha256": critic.sha_file(sample_path),
        "provider": "codex_user_runner",
        "model": model,
        "reasoning_effort": effort,
        "attempted_pair_count": len(rows),
        "valid_pair_count": len(valid),
        "pass_labels": sum(row["reference_label"] == "PASS" for row in rows),
        "fail_labels": sum(row["reference_label"] == "FAIL" for row in rows),
        "telemetry_complete": telemetry_complete,
        "fixed_provider_model_reasoning": fixed,
        "authority_zero_regression": authority_zero,
        "no_failure_timeout": all(row["failure"] is None and row["timeout"] is False for row in valid),
        "existing_false_accept_count": false_accept_existing,
        "critic_false_accept_count": false_accept_critic,
        "existing_false_reject_count": false_reject_existing,
        "critic_false_reject_count": false_reject_critic,
        "existing_missed_issue_count": missed_existing,
        "critic_missed_issue_count": missed_critic,
        "quality_value": quality_value,
        "repair_value": any(row["repair_scope_precision"] is not None and row["repair_scope_precision"] >= 0.8 for row in valid),
        "median_wall_seconds": median(walls),
        "median_total_tokens": median(tokens),
        "safety_pass": safety,
        "production_decision": "READY_FOR_CUTOVER_REVIEW" if safety and quality_value else "NO-GO",
        "cases": rows,
        "authority_write": False,
        "episode_transition": False,
        "image_generation_invoked": False,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": report_path.relative_to(ROOT).as_posix(), "valid_pairs": report["valid_pair_count"],
                      "quality_value": quality_value, "production_decision": report["production_decision"]}, ensure_ascii=False))
    return report


if __name__ == "__main__":
    result = run()
    raise SystemExit(0 if result["valid_pair_count"] == result["attempted_pair_count"] else 1)
