#!/usr/bin/env python3
"""Read-only, fail-closed PREIMAGE Semantic Critic pre-cutover evidence gate."""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "episodes/_system"))
sys.path.insert(0, str(ROOT / "episodes/_system/agents"))

import storyos_config

REPORT = Path("reports/p3-preimage-semantic-critic-pre-cutover-gate-20260928.json")
EVIDENCE = {
    "p0": Path("reports/p0-agent-acceptance-20260926.json"),
    "character_health": Path("reports/p1-character-post-cutover-health-20260926.json"),
    "visual_health": Path("reports/p2-visual-narrative-post-cutover-health-20260927.json"),
    "world_gate": Path("reports/p2-world-pre-cutover-gate-v2-20260927.json"),
    "world_value": Path("reports/p2-world-value-probe-20260927.json"),
    "story_no_go": Path("reports/p3-story-semantic-critic-quality-assessment-20260928-retry1.json"),
    "smoke": Path("reports/p3-preimage-semantic-critic-real-shadow-smoke-retry1-20260928.json"),
    "benchmark": Path("reports/p3-preimage-semantic-critic-paired-benchmark-20260928.json"),
    "candidate_scan": Path("reports/p3-preimage-semantic-critic-real-smoke-candidates-20260928.json"),
    "repair_assessment": Path("reports/p3-preimage-semantic-critic-repair-scope-assessment-v2-20260928.json"),
}
SCHEMA = Path("episodes/_system/agents/critic_decision.schema.json")
WORLD_BLOCKER = "WORLD_NO_MEASURABLE_AGENT_VALUE"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _read_doc(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("evidence must be a JSON object")
    return value


def _sources(root: Path, overrides: dict[str, dict] | None = None) -> tuple[dict, dict, list[str]]:
    docs, refs, blockers = {}, {}, []
    overrides = overrides or {}
    for name, rel in EVIDENCE.items():
        path = root / rel
        if not path.is_file():
            docs[name] = overrides.get(name, {})
            refs[name] = {"path": rel.as_posix(), "sha256": None, "present": False}
            blockers.append(f"MISSING_EVIDENCE:{rel.as_posix()}")
            continue
        refs[name] = {"path": rel.as_posix(), "sha256": _sha(path), "present": True}
        try:
            docs[name] = _read_doc(path)
        except (OSError, json.JSONDecodeError, ValueError):
            docs[name] = {}
            blockers.append(f"INVALID_EVIDENCE:{rel.as_posix()}")
        if name in overrides:
            docs[name] = copy.deepcopy(overrides[name])
    return docs, refs, blockers


def _request_snapshot_check(root: Path, request_path: Path, snapshot_path: Path,
                            expected_request_sha: str, expected_snapshot_sha: str | None = None) -> bool:
    try:
        req_doc = _read_doc(root / request_path)
        snapshot_file = root / snapshot_path
        if not snapshot_file.is_file():
            return False
        if expected_snapshot_sha and _sha(snapshot_file) != expected_snapshot_sha:
            return False
        snap = _read_doc(snapshot_file)
        frozen = snap.get("request")
        if not isinstance(frozen, dict):
            return False
        # The producer hashes the prepared request after attaching the snapshot path
        # and snapshot digest. The immutable snapshot itself intentionally predates
        # those two self-referential fields.
        reconstructed = dict(frozen)
        reconstructed["request_snapshot_path"] = snapshot_path.as_posix()
        reconstructed["request_snapshot_sha256"] = _sha(snapshot_file)
        if _digest(reconstructed) != expected_request_sha:
            return False
        if req_doc.get("request_id") != frozen.get("request_id"):
            return False
        if req_doc.get("request_fingerprint") != frozen.get("request_fingerprint"):
            return False
        if frozen.get("host_execution") != "codex_user_runner_shadow":
            return False
        if frozen.get("request_metadata", {}).get("shadow_only") is not True:
            return False
        if frozen.get("request_metadata", {}).get("candidate_authority") != "runtime_evidence_only":
            return False
        for source in frozen.get("source_files") or []:
            source_path = root / str(source.get("path") or "")
            if not source_path.is_file() or _sha(source_path) != source.get("sha256"):
                return False
        return True
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False


def _verify_smoke_bindings(root: Path, smoke: dict) -> dict:
    ep = root / str(smoke.get("episode") or "")
    request_path = Path(str(smoke.get("request_path") or ""))
    snapshot_path = Path(str(smoke.get("request_snapshot_path") or ""))
    request_ok = _request_snapshot_check(
        root, request_path, snapshot_path,
        str(smoke.get("request_sha256") or ""), str(smoke.get("request_snapshot_sha256") or ""),
    )
    capsule_path = ep / "meta/runtime/agent-shadow/preimage-semantic-critic/attempt-1-candidate-set.json"
    capsule_ok = False
    obligation_ok = applicability_ok = False
    try:
        capsule = _read_doc(capsule_path)
        capsule_ok = capsule.get("candidate_set_sha256") == smoke.get("candidate_set_sha256")
        applicability = capsule.get("applicability")
        source_hashes = capsule.get("source_authority_sha256")
        obligation_ok = (
            capsule.get("obligation_sha256") == smoke.get("obligation_sha256")
            and _digest({"applicability": applicability, "source_authority_sha256": source_hashes}) == capsule.get("obligation_sha256")
        )
        expected_scopes = {
            scope
            for task in capsule.get("candidate_set", {}).values()
            for scope in (task.get("task_contract") or {}).get("authority_scope", [])
        }
        applicability_ok = bool(expected_scopes) and set(applicability or {}) == expected_scopes
        request_doc = _read_doc(root / request_path)
        request_metadata = request_doc.get("request_metadata") or {}
        capsule_ok = capsule_ok and request_metadata.get("candidate_set_sha256") == smoke.get("candidate_set_sha256")
        obligation_ok = obligation_ok and request_metadata.get("obligation_sha256") == smoke.get("obligation_sha256")
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass
    schema_ok = False
    schema_path = root / SCHEMA
    if schema_path.is_file():
        schema_ok = _sha(schema_path) == smoke.get("decision_schema_sha256")
    return {
        "request_snapshot_and_sources": request_ok,
        "candidate_set_sha_bound": capsule_ok,
        "obligation_sha_bound": obligation_ok,
        "applicability_bound": applicability_ok,
        "decision_schema_sha_bound": schema_ok,
    }


def _verify_benchmark_bindings(root: Path, benchmark: dict) -> bool:
    cases = benchmark.get("cases")
    if not isinstance(cases, list) or not cases:
        return False
    base = Path(".storyos/p3-preimage-semantic-critic/benchmark-20260928")
    for row in cases:
        ep_rel = base / str(row.get("sample_id") or "")
        req_rel = ep_rel / "meta/runtime/reviews/preimage-semantic-critic-shadow-attempt-1-request.json"
        try:
            req = _read_doc(root / req_rel)
            meta = req.get("request_metadata") or {}
            snap_rel = Path(str(meta.get("request_snapshot_path") or ""))
            snap_path = root / snap_rel
            snap = _read_doc(snap_path)
            frozen = snap.get("request")
            reconstructed = dict(frozen) if isinstance(frozen, dict) else {}
            reconstructed["request_snapshot_path"] = snap_rel.as_posix()
            reconstructed["request_snapshot_sha256"] = _sha(snap_path)
            capsule = _read_doc(root / ep_rel / "meta/runtime/agent-shadow/preimage-semantic-critic/attempt-1-candidate-set.json")
            if not isinstance(frozen, dict) or _digest(reconstructed) != row.get("request_sha"):
                return False
            if req.get("request_fingerprint") != frozen.get("request_fingerprint"):
                return False
            if capsule.get("candidate_set_sha256") != row.get("candidate_sha"):
                return False
            if capsule.get("obligation_sha256") != row.get("obligation_sha"):
                return False
            if meta.get("candidate_set_sha256") != row.get("candidate_sha") or meta.get("obligation_sha256") != row.get("obligation_sha"):
                return False
            if frozen.get("request_metadata", {}).get("shadow_only") is not True:
                return False
            for source in frozen.get("source_files") or []:
                source_path = root / str(source.get("path") or "")
                if not source_path.is_file() or _sha(source_path) != source.get("sha256"):
                    return False
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return False
    return True


def classify_status(mandatory_checks: dict[str, bool], *, real_episode_shadow_evidence: bool) -> str:
    if any(value is not True for value in mandatory_checks.values()):
        return "BLOCKED"
    return "READY" if real_episode_shadow_evidence else "CONDITIONAL"


def evaluate(root: Path = ROOT, *, generated_at: str | None = None,
             evidence_overrides: dict[str, dict] | None = None,
             config_override: dict | None = None) -> dict:
    root = Path(root).resolve()
    docs, source_refs, source_blockers = _sources(root, evidence_overrides)
    blockers = list(source_blockers)
    warnings: list[str] = []
    try:
        cfg = copy.deepcopy(config_override) if config_override is not None else storyos_config._load(root / "config/storyos.yaml")
        config_errors = storyos_config.validate(cfg)
    except Exception as exc:
        cfg, config_errors = {}, [f"config_load_failed:{type(exc).__name__}"]
    adapter = lambda key, default=False: storyos_config.get_path(cfg, f"agent_runtime.adapters.{key}", default)
    p0 = docs["p0"]
    character = docs["character_health"]
    visual = docs["visual_health"]
    world = docs["world_gate"]
    world_value = docs["world_value"]
    story = docs["story_no_go"]
    smoke = docs["smoke"]
    benchmark = docs["benchmark"]
    scan = docs["candidate_scan"]
    repair = docs["repair_assessment"]

    try:
        smoke_binding = _verify_smoke_bindings(root, smoke)
    except Exception:
        smoke_binding = {key: False for key in (
            "request_snapshot_and_sources", "candidate_set_sha_bound", "obligation_sha_bound",
            "applicability_bound", "decision_schema_sha_bound",
        )}
    assessment_benchmark_ref = repair.get("source_benchmark") or {}
    benchmark_ref_ok = (
        assessment_benchmark_ref.get("path") == EVIDENCE["benchmark"].as_posix()
        and assessment_benchmark_ref.get("sha256") == source_refs["benchmark"].get("sha256")
    )
    fixture_path = root / "tests/fixtures/p3_preimage_semantic_critic/cases.json"
    fixture_binding_ok = bool(
        fixture_path.is_file()
        and benchmark.get("sample_set_sha256") == _sha(fixture_path)
        and repair.get("fixture_sha256") == _sha(fixture_path)
    )
    benchmark_request_evidence = _verify_benchmark_bindings(root, benchmark)
    status_checks = {
        "p0_foundation_healthy": p0.get("kind") == "p0_agent_protocol_acceptance" and p0.get("commit_gate_ready") is True,
        "character_production_health": character.get("status") == "PASS" and (character.get("adapter_state") or {}).get("production_enabled") is True and (character.get("adapter_state") or {}).get("shadow_enabled") is False,
        "visual_production_health": visual.get("status") == "PASS" and (visual.get("adapter_state") or {}).get("production_enabled") is True and (visual.get("adapter_state") or {}).get("shadow_enabled") is False,
        "world_no_go_preserved": world.get("status") == "BLOCKED" and WORLD_BLOCKER in (world.get("blockers") or []) and world_value.get("final_decision") == "WORLD_PRODUCTION_NO_GO" and adapter("world_prepare.shadow_enabled") is True and adapter("world_prepare.production_enabled") is False,
        "story_semantic_no_go_preserved": story.get("production_decision") == "NO_GO" and story.get("quality_value") is False and adapter("story_semantic_critic.shadow_enabled") is True and adapter("story_semantic_critic.production_enabled") is False,
        "config_valid": not config_errors,
        "preimage_critic_shadow_enabled": adapter("preimage_semantic_critic.shadow_enabled") is True,
        "preimage_critic_production_disabled": adapter("preimage_semantic_critic.production_enabled") is False,
        "legacy_fallback_available": adapter("preimage_semantic_critic.legacy_fallback_on_technical") is True,
        "bounded_reflection_caps": (adapter("preimage_semantic_critic.bounded_reflection", {}) or {}).get("max_review_attempts") == 2 and (adapter("preimage_semantic_critic.bounded_reflection", {}) or {}).get("max_auto_repairs") == 1,
        "real_shadow_smoke_pass": smoke.get("status") == "PASS" and smoke.get("sample_type") == "isolated_fixture_episode",
        "real_model_execution": (smoke.get("model_execution") or {}).get("real_model_execution") is True,
        "smoke_telemetry_complete": (smoke.get("checks") or {}).get("telemetry_complete") is True and (smoke.get("model_execution") or {}).get("complete") is True,
        "no_smoke_failure_timeout": (smoke.get("model_execution") or {}).get("failure") is False and (smoke.get("model_execution") or {}).get("timeout") is False and (smoke.get("model_execution") or {}).get("returncode") == 0,
        "decision_schema_valid": (smoke.get("checks") or {}).get("decision_schema_valid") is True and smoke_binding["decision_schema_sha_bound"],
        "request_evidence_complete": smoke_binding["request_snapshot_and_sources"] and benchmark_request_evidence,
        "candidate_set_sha_bound": smoke_binding["candidate_set_sha_bound"],
        "obligation_sha_bound": smoke_binding["obligation_sha_bound"],
        "applicability_bound": smoke_binding["applicability_bound"],
        "authority_zero_regression": (smoke.get("checks") or {}).get("authority_write") is False and (smoke.get("checks") or {}).get("gate_pass") is False and (smoke.get("canonical_authority_modified") is False) and benchmark.get("authority_zero_regression") is True,
        "gate_authority_unchanged": (smoke.get("checks") or {}).get("gate_pass") is False and (smoke.get("checks") or {}).get("existing_semantic_unchanged") is True,
        "episode_transition_false": (smoke.get("checks") or {}).get("episode_transition") is False and benchmark.get("episode_transition") is False,
        "repair_not_invoked": (smoke.get("checks") or {}).get("repair_invoked") is False,
        "image_generation_not_invoked": (smoke.get("checks") or {}).get("image_generation_invoked") is False and benchmark.get("image_generation_invoked") is False,
        "benchmark_minimum_five_pairs": int(benchmark.get("valid_pair_count") or 0) >= 5 and len(benchmark.get("cases") or []) >= 5,
        "benchmark_balanced_labels": int(benchmark.get("pass_labels") or 0) >= 2 and int(benchmark.get("fail_labels") or 0) >= 2,
        "benchmark_fixed_provider_model_reasoning": benchmark.get("fixed_provider_model_reasoning") is True and benchmark.get("provider") == "codex_user_runner" and bool(benchmark.get("model")) and bool(benchmark.get("reasoning_effort")),
        "benchmark_telemetry_complete": benchmark.get("telemetry_complete") is True and all(all(row.get(key) is not None for key in ("wall_seconds", "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "provider", "model", "reasoning_effort")) for row in (benchmark.get("cases") or [])),
        "benchmark_authority_zero_regression": benchmark.get("authority_zero_regression") is True and all(row.get("authority_write") is False and row.get("episode_transition") is False for row in (benchmark.get("cases") or [])),
        "benchmark_no_failure_timeout": benchmark.get("no_failure_timeout") is True and all(row.get("failure") is None and row.get("timeout") is False for row in (benchmark.get("cases") or [])),
        "quality_value": benchmark.get("quality_value") is True,
        "false_accept_improved": int(benchmark.get("existing_false_accept_count") or 0) > int(benchmark.get("critic_false_accept_count") or 0),
        "false_reject_not_regressed": int(benchmark.get("critic_false_reject_count") or 0) <= int(benchmark.get("existing_false_reject_count") or 0),
        "repair_assessment_benchmark_sha_matches": benchmark_ref_ok,
        "benchmark_fixture_sha_bound": fixture_binding_ok,
        "repair_assessment_valid": repair.get("kind") == "p3_preimage_semantic_critic_repair_scope_assessment_v2" and repair.get("immutable") is True and repair.get("policy", {}).get("policy_source") == "cutover_gate_conservative_default",
        "production_not_already_enabled": adapter("preimage_semantic_critic.production_enabled") is False,
    }
    blockers.extend(key.upper() for key, passed in status_checks.items() if passed is not True)
    repair_mode = repair.get("repair_mode_at_cutover") or "UNSPECIFIED"
    repair_value_v2 = repair.get("repair_value_v2") is True
    repair_value_blocking = repair_mode != "STRICTLY_ADVISORY_NO_AUTOMATIC_REPAIR" and not repair_value_v2
    if repair.get("issue_code_recall") != "NOT_COMPARABLE" or repair.get("issue_code_taxonomy_mapping_available") is not False:
        status_checks["issue_code_recall_not_fabricated"] = False
        blockers.append("ISSUE_CODE_TAXONOMY_UNVERIFIED")
    else:
        status_checks["issue_code_recall_not_fabricated"] = True
    if repair_value_blocking:
        blockers.append("REPAIR_VALUE_V2_REQUIRED_FOR_AUTOMATIC_REPAIR")
    if repair.get("minimum_repair_scope_recall") is not None and repair["minimum_repair_scope_recall"] < 0.8:
        warnings.append("REPAIR_SCOPE_MINIMUM_RECALL_BELOW_0_8")
    if repair.get("issue_code_recall") == "NOT_COMPARABLE":
        warnings.append("ISSUE_CODE_RECALL_NOT_COMPARABLE")

    candidate_count = int(scan.get("candidate_count") or 0)
    eligible_count = int(scan.get("eligible_count") or 0)
    real_episode_shadow_evidence = eligible_count > 0 and smoke.get("sample_type") == "real_episode"
    if not real_episode_shadow_evidence:
        warnings.append("NO_REAL_PREIMAGE_CANDIDATE_SET_SHADOW_EVIDENCE")
    real_evidence_policy_source = "P3-specific real-Episode cutover rule not explicit; conservative precedent from final-plan P1.5 (real Episode comparison) and completed Visual Gate evidence"
    status = classify_status(status_checks, real_episode_shadow_evidence=real_episode_shadow_evidence)
    if status == "CONDITIONAL":
        blockers.append("PRODUCTION_EVIDENCE_REVIEW_REQUIRED")
    return {
        "schema_version": 1,
        "kind": "p3_preimage_semantic_critic_pre_cutover_gate",
        "generated_at": generated_at or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "immutable": True,
        "status": status,
        "production_cutover_performed": False,
        "ready_for_cutover": status == "READY",
        "production_readiness_real_evidence": "PASS" if real_episode_shadow_evidence else "REVIEW_REQUIRED",
        "policy_requirement": "REVIEW_REQUIRED" if not real_episode_shadow_evidence else "SATISFIED",
        "real_evidence_policy_source": real_evidence_policy_source,
        "real_episode_candidate_count": candidate_count,
        "real_episode_eligible_count": eligible_count,
        "real_episode_shadow_evidence": real_episode_shadow_evidence,
        "repair_mode_at_cutover": repair_mode,
        "repair_value_v2": repair_value_v2,
        "repair_value_blocking": repair_value_blocking,
        "repair_scope_precision_median": repair.get("repair_scope_precision_median"),
        "repair_scope_recall_median": repair.get("repair_scope_recall_median"),
        "repair_scope_f1_median": repair.get("repair_scope_f1_median"),
        "minimum_repair_scope_recall": repair.get("minimum_repair_scope_recall"),
        "issue_code_recall": repair.get("issue_code_recall", "NOT_COMPARABLE"),
        "mandatory_checks": status_checks,
        "source_evidence": source_refs,
        "evidence_sha_verified": all(row.get("present") and row.get("sha256") for row in source_refs.values()) and benchmark_ref_ok and fixture_binding_ok and smoke_binding["request_snapshot_and_sources"] and benchmark_request_evidence,
        "smoke_evidence_binding": smoke_binding,
        "benchmark_request_evidence_complete": benchmark_request_evidence,
        "benchmark_summary": {
            "valid_pairs": benchmark.get("valid_pair_count"),
            "pass_labels": benchmark.get("pass_labels"),
            "fail_labels": benchmark.get("fail_labels"),
            "quality_value": benchmark.get("quality_value"),
            "existing_false_accept": benchmark.get("existing_false_accept_count"),
            "critic_false_accept": benchmark.get("critic_false_accept_count"),
            "existing_false_reject": benchmark.get("existing_false_reject_count"),
            "critic_false_reject": benchmark.get("critic_false_reject_count"),
        },
        "warnings": sorted(set(warnings)),
        "blockers": sorted(set(blockers)),
        "config_state": {
            "shadow_enabled": adapter("preimage_semantic_critic.shadow_enabled"),
            "production_enabled": adapter("preimage_semantic_critic.production_enabled"),
            "legacy_fallback_on_technical": adapter("preimage_semantic_critic.legacy_fallback_on_technical"),
        },
        "git_head": _git_head(root),
        "note": "Read-only fail-closed gate. It never mutates config, candidates, authority, review records, episode state, or invokes a model/image provider.",
    }


def _git_head(root: Path) -> str | None:
    import subprocess
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def write_immutable(path: Path, report: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with path.open("xb") as handle:
        handle.write(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / REPORT)
    args = parser.parse_args()
    report = evaluate(ROOT)
    write_immutable(args.output, report)
    print(json.dumps({"status": report["status"], "path": args.output.relative_to(ROOT).as_posix(),
                      "blockers": report["blockers"], "warnings": report["warnings"]}, ensure_ascii=False))
    return 0 if report["status"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
