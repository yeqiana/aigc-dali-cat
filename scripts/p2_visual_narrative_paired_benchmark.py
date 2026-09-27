#!/usr/bin/env python3
"""Paired read-only benchmark for legacy and Agent VISUAL_NARRATIVE_PREPARE."""
from __future__ import annotations

import argparse
import concurrent.futures
import copy
import datetime as dt
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes/_system"
sys.path[:0] = [str(SYSTEM), str(ROOT)]

import agent_shadow_compare
import episode_state_persistence
import preimage_authority_snapshot
import preimage_task_contract
import product_runtime_adapter
import story_json
from agents import visual_narrative_prepare_model_producer as producer

DEFAULT_EPISODE = "episodes/独立篇/01_五环外的浓雾"
DEFAULT_SMOKE_REPORT = "reports/p2-visual-narrative-shadow-smoke-retry3-20260927.json"
DEFAULT_MANIFEST = ".storyos/tmp/p2-visual-narrative-paired-benchmark.json"
DEFAULT_RUN_DIR = ".storyos/tmp/p2-visual-narrative-paired-runs"
DEFAULT_REPORT = "reports/p2-visual-narrative-paired-benchmark-20260927.json"
WALL_REGRESSION_MAX = 0.05
TOKEN_REGRESSION_MAX = 0.10
SPEED_VALUE_MIN = 0.10
TOKEN_VALUE_MIN = 0.20


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_json(path: Path, default=None):
    return story_json.read_json(path, default=default)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def fingerprint(ep: Path, task: dict) -> dict:
    capsule = (task.get("input_contract") or {}).get("visual_narrative_capsule") or {}
    state = episode_state_persistence.load(ep) or read_json(ep / "meta/episode-state.json", {}) or {}
    return {
        "snapshot_id": task.get("snapshot_id"),
        "capsule_sha256": capsule.get("capsule_sha256"),
        "source_sha256": copy.deepcopy(capsule.get("source_sha256") or {}),
        "authority_sha256": preimage_authority_snapshot.owned_hashes(ep),
        "episode_state": state.get("current_state"),
    }


def telemetry_complete(raw: dict) -> bool:
    return bool(
        raw.get("real_model_execution") is True
        and isinstance(raw.get("wall_seconds"), (int, float))
        and not isinstance(raw.get("wall_seconds"), bool)
        and raw.get("wall_seconds") >= 0
        and all(type(raw.get(key)) is int and raw.get(key) >= 0 for key in (
            "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "repeated_reads"
        ))
        and raw.get("repeated_reads_scope") == "frozen_authority_capsule"
        and isinstance(raw.get("failure"), bool)
        and isinstance(raw.get("timeout"), bool)
        and type(raw.get("returncode")) is int
        and bool(raw.get("provider")) and bool(raw.get("model"))
        and raw.get("reasoning_effort") == producer.REASONING_EFFORT
        and type(raw.get("usage_event_count")) is int and raw["usage_event_count"] > 0
        and raw.get("telemetry_source") == "codex_cli_jsonl.turn.completed+codex_user_runner.receipt"
        and raw.get("tool_free") is True
    )


def run_producer(ep: Path, task: dict, role: str) -> dict:
    try:
        produced = producer.run(ep, task, role=role)
        candidate = None
        errors: list[str] = []
        semantic = None
        if role == "agent_shadow":
            candidate, errors, semantic = product_runtime_adapter.visual_narrative_host_candidate(task, produced)
        elif isinstance(produced.get("payload"), dict):
            candidate = preimage_task_contract.candidate_template(task, produced["payload"])
            candidate["model_execution"] = dict(produced.get("model_execution") or {})
            errors = preimage_task_contract.verify_candidate(candidate, task)
            if not errors:
                semantic = agent_shadow_compare.compare_visual_narrative_semantics(task, candidate)
                if semantic.get("pass") is not True:
                    errors.extend(semantic.get("errors") or ["Legacy Visual obligations failed"])
                if errors:
                    candidate = None
        else:
            errors = [str(produced.get("failure_reason") or "legacy producer returned no payload")]
        return {
            "role": role, "producer": produced, "candidate": candidate,
            "candidate_errors": errors, "semantic": semantic,
            "telemetry_complete": telemetry_complete(produced.get("model_execution") or {}),
        }
    except Exception as exc:
        return {
            "role": role,
            "producer": {
                "payload": None,
                "model_execution": {
                    "real_model_execution": None, "wall_seconds": None, "elapsed_seconds": None,
                    "input_tokens": None, "cached_input_tokens": None, "output_tokens": None,
                    "reasoning_output_tokens": None, "repeated_reads": None,
                    "failure": None, "timeout": None, "returncode": None,
                    "provider": producer.DEFAULT_PROVIDER, "model": producer.DEFAULT_MODEL,
                    "reasoning_effort": producer.REASONING_EFFORT,
                    "telemetry_source": "codex_cli_jsonl.turn.completed+codex_user_runner.receipt",
                },
                "failure_reason": f"{type(exc).__name__}: {exc}",
            },
            "candidate": None, "candidate_errors": [f"{type(exc).__name__}: {exc}"],
            "semantic": None, "telemetry_complete": False,
        }


def _semantic_errors(run: dict) -> int | None:
    semantic = run.get("semantic") or {}
    if not isinstance(semantic, dict):
        return None
    errors = semantic.get("errors")
    return len(errors) if isinstance(errors, list) else None


def run_one(ep: Path, task: dict, index: int, run_dir: Path) -> dict:
    before = fingerprint(ep, task)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        legacy_future = pool.submit(run_producer, ep, task, "legacy_control")
        agent_future = pool.submit(run_producer, ep, task, "agent_shadow")
        legacy, agent = legacy_future.result(), agent_future.result()
    after = fingerprint(ep, task)
    le = legacy["producer"].get("model_execution") or {}
    ae = agent["producer"].get("model_execution") or {}
    same_runtime = bool(
        le.get("provider") == ae.get("provider") == producer.DEFAULT_PROVIDER
        and le.get("model") == ae.get("model") == producer.DEFAULT_MODEL
        and le.get("reasoning_effort") == ae.get("reasoning_effort") == producer.REASONING_EFFORT
        and le.get("runner_request_id") != ae.get("runner_request_id")
    )
    semantic_equivalent = bool(
        legacy.get("candidate") is not None and agent.get("candidate") is not None
        and (legacy.get("semantic") or {}).get("pass") is True
        and (agent.get("semantic") or {}).get("pass") is True
    )
    no_failures = all(
        side.get("producer", {}).get("model_execution", {}).get("failure") is False
        and side.get("producer", {}).get("model_execution", {}).get("timeout") is False
        and side.get("producer", {}).get("model_execution", {}).get("returncode") == 0
        for side in (legacy, agent)
    )
    candidate_valid = all(
        side.get("candidate") is not None and not side.get("candidate_errors")
        and not preimage_task_contract.verify_candidate(side["candidate"], task)
        for side in (legacy, agent)
    )
    authority_unchanged = before == after
    telemetry_ok = legacy.get("telemetry_complete") is True and agent.get("telemetry_complete") is True
    valid = bool(candidate_valid and telemetry_ok and semantic_equivalent and same_runtime and no_failures and authority_unchanged)
    row = {
        "pair_index": index, "valid": valid,
        "checks": {
            "candidate_valid": candidate_valid,
            "telemetry_complete": telemetry_ok,
            "semantic_equivalent": semantic_equivalent,
            "fixed_provider_model_reasoning": same_runtime,
            "no_failure_timeout": no_failures,
            "authority_zero_regression": authority_unchanged,
        },
        "snapshot_id": task.get("snapshot_id"),
        "authority_sha_before": before["authority_sha256"],
        "authority_sha_after": after["authority_sha256"],
        "legacy": _side_evidence(legacy, le),
        "agent": _side_evidence(agent, ae),
        "quality": {
            "legacy_quality_errors": _semantic_errors(legacy),
            "agent_quality_errors": _semantic_errors(agent),
            "legacy_quality_warnings": None,
            "agent_quality_warnings": None,
            "warning_source": "no warning channel in PREIMAGE Visual verifier/comparator",
        },
    }
    write_json(run_dir / f"run-{index:02d}-result.json", row)
    return row


def _side_evidence(run: dict, telemetry: dict) -> dict:
    return {
        "provider": telemetry.get("provider"), "model": telemetry.get("model"),
        "reasoning_effort": telemetry.get("reasoning_effort"),
        "real_model_execution": telemetry.get("real_model_execution"),
        "wall_seconds": telemetry.get("wall_seconds"), "input_tokens": telemetry.get("input_tokens"),
        "cached_input_tokens": telemetry.get("cached_input_tokens"), "output_tokens": telemetry.get("output_tokens"),
        "reasoning_output_tokens": telemetry.get("reasoning_output_tokens"),
        "total_tokens": (telemetry.get("input_tokens") + telemetry.get("output_tokens"))
        if type(telemetry.get("input_tokens")) is int and type(telemetry.get("output_tokens")) is int else None,
        "repeated_reads": telemetry.get("repeated_reads"),
        "repeated_reads_scope": telemetry.get("repeated_reads_scope"),
        "failure": telemetry.get("failure"), "timeout": telemetry.get("timeout"),
        "returncode": telemetry.get("returncode"),
        "candidate_valid": run.get("candidate") is not None and not run.get("candidate_errors"),
        "candidate_errors": run.get("candidate_errors"),
        "semantic_pass": (run.get("semantic") or {}).get("pass") is True,
        "semantic_errors": (run.get("semantic") or {}).get("errors"),
        "telemetry_complete": run.get("telemetry_complete") is True,
        "failure_reason": (run.get("producer") or {}).get("failure_reason"),
    }


def _median(rows: list[dict], side: str, field: str):
    values = [row[side].get(field) for row in rows]
    values = [float(value) for value in values if isinstance(value, (int, float)) and not isinstance(value, bool)]
    return statistics.median(values) if values else None


def summarize(manifest: dict, rows: list[dict]) -> dict:
    valid_rows = [row for row in rows if row.get("valid") is True]
    legacy_wall, agent_wall = _median(valid_rows, "legacy", "wall_seconds"), _median(valid_rows, "agent", "wall_seconds")
    legacy_tokens, agent_tokens = _median(valid_rows, "legacy", "total_tokens"), _median(valid_rows, "agent", "total_tokens")
    wall_regression = (agent_wall / legacy_wall - 1) if legacy_wall and agent_wall is not None else None
    token_regression = (agent_tokens / legacy_tokens - 1) if legacy_tokens and agent_tokens is not None else None
    telemetry_complete_all = bool(rows) and all(row["checks"]["telemetry_complete"] for row in rows)
    no_failures = bool(rows) and all(row["checks"]["no_failure_timeout"] for row in rows)
    authority_zero = bool(rows) and all(row["checks"]["authority_zero_regression"] for row in rows)
    fixed_runtime = bool(rows) and all(row["checks"]["fixed_provider_model_reasoning"] for row in rows)
    quality_pairs = [row for row in rows if type(row["quality"].get("legacy_quality_errors")) is int
                     and type(row["quality"].get("agent_quality_errors")) is int]
    quality_value = len(quality_pairs) >= 5 and all(
        row["quality"]["agent_quality_errors"] < row["quality"]["legacy_quality_errors"]
        for row in quality_pairs[:5]
    )
    speed_value = wall_regression is not None and wall_regression <= -SPEED_VALUE_MIN
    token_value = token_regression is not None and token_regression <= -TOKEN_VALUE_MIN
    recovery_value = False  # This benchmark does not inject matched recovery faults.
    safety_checks = {
        "minimum_valid_pairs": len(valid_rows) >= 5,
        "telemetry_complete": telemetry_complete_all,
        "all_valid_pairs_semantic_equivalent": len(valid_rows) >= 5 and all(row["checks"]["semantic_equivalent"] for row in valid_rows),
        "no_failure_timeout": no_failures,
        "authority_zero_regression": authority_zero,
        "fixed_provider_model_reasoning": fixed_runtime,
        "wall_regression_within_5pct": wall_regression is not None and wall_regression <= WALL_REGRESSION_MAX,
        "token_regression_within_10pct": token_regression is not None and token_regression <= TOKEN_REGRESSION_MAX,
    }
    value_checks = {
        "speed_value_ge_10pct": speed_value,
        "token_reduction_ge_20pct": token_value,
        "deterministic_quality_value": quality_value,
        "matched_recovery_value": recovery_value,
    }
    safety_pass = bool(rows) and all(safety_checks.values())
    measurable = any(value_checks.values())
    return {
        "schema_version": 1, "kind": "p2_visual_narrative_paired_benchmark",
        "generated_at": now(), "episode": manifest["episode"], "snapshot_id": manifest["snapshot_id"],
        "provider": manifest["provider"], "model": manifest["model"],
        "reasoning_effort": manifest["reasoning_effort"], "required_scope": manifest["authority_scope"],
        "attempted_pair_count": len(rows), "valid_pair_count": len(valid_rows),
        "telemetry_complete": telemetry_complete_all, "semantic_equivalence": safety_checks["all_valid_pairs_semantic_equivalent"],
        "authority_zero_regression": authority_zero, "safety_checks": safety_checks,
        "performance": {
            "median_legacy_wall_seconds": legacy_wall, "median_agent_wall_seconds": agent_wall,
            "median_legacy_total_tokens": legacy_tokens, "median_agent_total_tokens": agent_tokens,
            "wall_regression_fraction": wall_regression, "token_regression_fraction": token_regression,
            "distribution_policy": "median_only; p90/p95 omitted below 20 valid pairs",
        },
        "value_checks": value_checks, "measurable_value": measurable,
        "quality": {
            "legacy_quality_errors": sum(row["quality"]["legacy_quality_errors"] for row in quality_pairs),
            "agent_quality_errors": sum(row["quality"]["agent_quality_errors"] for row in quality_pairs),
            "legacy_quality_warnings": None, "agent_quality_warnings": None,
            "paired_quality_samples": len(quality_pairs), "quality_value_evidence": quality_value,
        },
        "recovery_value_evidence": recovery_value,
        "safety_pass": safety_pass,
        "production_decision": "CONDITIONAL_REVIEW" if safety_pass and measurable else "NO_GO",
        "production_cutover_performed": False,
        "runs": rows,
        "note": "Read-only paired producer execution; no canonical Candidate path, Authority, Episode State, Gate, Ledger, or image is written.",
    }


def prepare(args) -> dict:
    ep = (ROOT / args.episode).resolve()
    smoke_path = ROOT / args.smoke_report
    smoke = read_json(smoke_path, {}) or {}
    smoke_checks = smoke.get("checks") or {}
    if smoke.get("status") != "PASS" or not all(smoke_checks.get(key) is True for key in (
        "candidate_parse", "candidate_valid", "semantic_pass", "shadow_only", "allowed_tools_empty",
        "telemetry_complete", "authority_zero_regression", "episode_state_unchanged",
        "current_host_pointer_unchanged", "canonical_preimage_not_started", "image_generation_not_invoked",
    )):
        raise RuntimeError("Visual real-Episode Shadow smoke evidence is not PASS")
    state = episode_state_persistence.load(ep) or read_json(ep / "meta/episode-state.json", {}) or {}
    if state.get("current_state") != "STORYBOARD_LOCKED":
        raise ValueError(f"Episode state must remain STORYBOARD_LOCKED; got {state.get('current_state')}")
    snapshot = preimage_authority_snapshot.build(ep, write=False)
    task = preimage_task_contract.task_contract(ep, "VISUAL_NARRATIVE_PREPARE", snapshot, resume=True)
    task = producer.freeze_task(ep, task)
    initial = fingerprint(ep, task)
    manifest = {
        "schema_version": 1, "kind": "p2_visual_narrative_paired_benchmark_manifest", "created_at": now(),
        "episode": ep.relative_to(ROOT).as_posix(), "snapshot_id": task["snapshot_id"],
        "provider": producer.DEFAULT_PROVIDER, "model": producer.DEFAULT_MODEL,
        "reasoning_effort": producer.REASONING_EFFORT, "authority_scope": task["authority_scope"],
        "task": task, "initial_fingerprint": initial, "smoke_evidence": args.smoke_report,
        "run_directory": args.run_dir,
    }
    if fingerprint(ep, task) != initial:
        raise RuntimeError("benchmark prepare changed source authority")
    write_json(ROOT / args.manifest, manifest)
    return manifest


def load_manifest(args) -> dict:
    manifest = read_json(ROOT / args.manifest)
    if not isinstance(manifest, dict) or manifest.get("kind") != "p2_visual_narrative_paired_benchmark_manifest":
        raise ValueError("paired benchmark manifest missing; run prepare first")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run", "collect", "series"):
        p = sub.add_parser(name)
        p.add_argument("--episode", default=DEFAULT_EPISODE)
        p.add_argument("--smoke-report", default=DEFAULT_SMOKE_REPORT)
        p.add_argument("--manifest", default=DEFAULT_MANIFEST)
        p.add_argument("--run-dir", default=DEFAULT_RUN_DIR)
        p.add_argument("--report", default=DEFAULT_REPORT)
        if name in {"run", "series"}:
            p.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()
    if args.command == "prepare":
        manifest = prepare(args)
        print(json.dumps({"manifest": args.manifest, "snapshot_id": manifest["snapshot_id"],
                          "smoke_evidence": manifest["smoke_evidence"]}, ensure_ascii=False, indent=2))
        return 0
    manifest = load_manifest(args)
    ep = (ROOT / manifest["episode"]).resolve()
    task = manifest["task"]
    if fingerprint(ep, task) != manifest["initial_fingerprint"]:
        raise RuntimeError("frozen Visual authority changed after prepare; refusing benchmark")
    run_dir = ROOT / args.run_dir
    rows = [read_json(path) for path in sorted(run_dir.glob("run-*-result.json"))] if run_dir.exists() else []
    if args.command in {"run", "series"}:
        if args.runs <= 0:
            raise ValueError("--runs must be positive")
        run_dir.mkdir(parents=True, exist_ok=True)
        next_index = max((int(row.get("pair_index") or 0) for row in rows), default=0) + 1
        for index in range(next_index, next_index + args.runs):
            rows.append(run_one(ep, task, index, run_dir))
        report = summarize(manifest, rows)
        write_json(ROOT / args.report, report)
        print(json.dumps({"attempted_pair_count": report["attempted_pair_count"],
                          "valid_pair_count": report["valid_pair_count"], "safety_pass": report["safety_pass"],
                          "measurable_value": report["measurable_value"],
                          "performance": report["performance"]}, ensure_ascii=False, indent=2))
        return 0 if report["safety_pass"] else 3
    report = summarize(manifest, rows)
    write_json(ROOT / args.report, report)
    print(json.dumps({"attempted_pair_count": report["attempted_pair_count"],
                      "valid_pair_count": report["valid_pair_count"], "safety_pass": report["safety_pass"],
                      "measurable_value": report["measurable_value"]}, ensure_ascii=False, indent=2))
    return 0 if report["safety_pass"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
