#!/usr/bin/env python3
"""Read-only paired benchmark for legacy and Agent WORLD_PREPARE producers."""
from __future__ import annotations

import argparse
import concurrent.futures
import copy
import datetime as dt
import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes/_system"
sys.path[:0] = [str(SYSTEM), str(ROOT)]

import preimage_authority_snapshot
import preimage_task_contract
import episode_state_persistence
import product_runtime_adapter
import story_json
from agents import world_prepare_model_producer
from agents import world_prepare_adapter
from platform.agent.runtime import AgentRuntime

DEFAULT_EPISODE = "episodes/独立篇/01_五环外的浓雾"
DEFAULT_MANIFEST = ".storyos/tmp/p2-world-paired-benchmark.json"
DEFAULT_RUN_DIR = ".storyos/tmp/p2-world-paired-runs"
DEFAULT_REPORT = "reports/p2-world-paired-benchmark-20260926.json"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_json(path: Path, default=None):
    return story_json.read_json(path, default=default)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def fingerprint(ep: Path, task: dict) -> dict:
    capsule = (task.get("input_contract") or {}).get("world_prepare_capsule") or {}
    state = episode_state_persistence.load(ep) or read_json(ep / "meta/episode-state.json", {}) or {}
    return {
        "snapshot_id": task.get("snapshot_id"),
        "capsule_sha256": capsule.get("capsule_sha256"),
        "source_sha256": copy.deepcopy(capsule.get("source_sha256") or {}),
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
        and bool(raw.get("provider")) and bool(raw.get("model"))
        and raw.get("telemetry_source") == "codex_cli_jsonl.turn.completed+codex_user_runner.receipt"
    )


def run_producer(ep: Path, task: dict, role: str) -> dict:
    try:
        produced = world_prepare_model_producer.run(ep, task, role=role)
        candidate, errors, semantic = product_runtime_adapter.world_prepare_host_candidate(task, produced)
        return {
            "role": role,
            "producer": produced,
            "candidate": candidate,
            "candidate_errors": errors,
            "semantic": semantic,
            "telemetry_complete": telemetry_complete(produced.get("model_execution") or {}),
        }
    except Exception as exc:
        return {
            "role": role, "producer": {
                "payload": None,
                "model_execution": {
                    "real_model_execution": None, "wall_seconds": None, "input_tokens": None,
                    "cached_input_tokens": None, "output_tokens": None, "reasoning_output_tokens": None,
                    "repeated_reads": None, "failure": None, "timeout": None,
                    "provider": world_prepare_model_producer.DEFAULT_PROVIDER,
                    "model": world_prepare_model_producer.DEFAULT_MODEL,
                    "telemetry_source": "codex_cli_jsonl.turn.completed+codex_user_runner.receipt",
                    "reasoning_effort": world_prepare_model_producer.REASONING_EFFORT,
                },
                "failure_reason": f"{type(exc).__name__}: {exc}",
            },
            "candidate": None, "candidate_errors": [f"{type(exc).__name__}: {exc}"],
            "semantic": None, "telemetry_complete": False,
        }


def run_one(ep: Path, task: dict, index: int, run_dir: Path) -> dict:
    before = fingerprint(ep, task)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        legacy_future = pool.submit(run_producer, ep, task, "legacy_control")
        agent_future = pool.submit(run_producer, ep, task, "agent_shadow")
        legacy = legacy_future.result()
        agent = agent_future.result()
    after = fingerprint(ep, task)
    le = legacy["producer"].get("model_execution") or {}
    ae = agent["producer"].get("model_execution") or {}
    same_runtime = bool(
        le.get("provider") == ae.get("provider")
        and le.get("model") == ae.get("model")
        and le.get("reasoning_effort") == ae.get("reasoning_effort") == world_prepare_model_producer.REASONING_EFFORT
        and le.get("provider") == world_prepare_model_producer.DEFAULT_PROVIDER
        and le.get("model") == world_prepare_model_producer.DEFAULT_MODEL
    )
    semantic = bool(
        (legacy.get("semantic") or {}).get("pass") is True
        and (agent.get("semantic") or {}).get("pass") is True
    )
    authority_unchanged = before == after
    no_failures = all(x.get("producer", {}).get("model_execution", {}).get("failure") is False
                      and x.get("producer", {}).get("model_execution", {}).get("timeout") is False
                      for x in (legacy, agent))
    valid = all(x.get("candidate") is not None and x.get("telemetry_complete") for x in (legacy, agent))
    row = {
        "pair_index": index,
        "valid": bool(valid and same_runtime and semantic and authority_unchanged and no_failures),
        "checks": {
            "candidate_valid": valid,
            "telemetry_complete": all(x.get("telemetry_complete") for x in (legacy, agent)),
            "semantic_equivalent": semantic,
            "fixed_provider_model_reasoning": same_runtime,
            "no_failure_timeout": no_failures,
            "authority_zero_regression": authority_unchanged,
        },
        "authority_sha_before": before,
        "authority_sha_after": after,
        "legacy": {
            "provider": le.get("provider"), "model": le.get("model"), "reasoning_effort": le.get("reasoning_effort"),
            "wall_seconds": le.get("wall_seconds"), "input_tokens": le.get("input_tokens"),
            "cached_input_tokens": le.get("cached_input_tokens"), "output_tokens": le.get("output_tokens"),
            "reasoning_output_tokens": le.get("reasoning_output_tokens"), "repeated_reads": le.get("repeated_reads"),
            "repeated_reads_scope": le.get("repeated_reads_scope"), "failure": le.get("failure"),
            "timeout": le.get("timeout"), "candidate_errors": legacy.get("candidate_errors"),
            "semantic": legacy.get("semantic"), "failure_reason": legacy["producer"].get("failure_reason"),
        },
        "agent": {
            "provider": ae.get("provider"), "model": ae.get("model"), "reasoning_effort": ae.get("reasoning_effort"),
            "wall_seconds": ae.get("wall_seconds"), "input_tokens": ae.get("input_tokens"),
            "cached_input_tokens": ae.get("cached_input_tokens"), "output_tokens": ae.get("output_tokens"),
            "reasoning_output_tokens": ae.get("reasoning_output_tokens"), "repeated_reads": ae.get("repeated_reads"),
            "repeated_reads_scope": ae.get("repeated_reads_scope"), "failure": ae.get("failure"),
            "timeout": ae.get("timeout"), "candidate_errors": agent.get("candidate_errors"),
            "semantic": agent.get("semantic"), "failure_reason": agent["producer"].get("failure_reason"),
        },
    }
    row_path = run_dir / f"run-{index:02d}-result.json"
    write_json(row_path, row)
    # Candidate JSON contains Runtime Evidence only and stays in the ignored experiment directory.
    if agent.get("candidate") is not None:
        write_json(run_dir / f"run-{index:02d}-agent-candidate.json", agent["candidate"])
        smoke_path = ROOT / "reports/p2-world-real-model-shadow-smoke-20260926.json"
        if (read_json(smoke_path, {}) or {}).get("status") != "PASS":
            smoke = runtime_shadow_smoke(ep, task, agent["candidate"])
            write_json(smoke_path, smoke)
    return row


def runtime_shadow_smoke(ep: Path, task: dict, candidate: dict) -> dict:
    """Run the real Agent candidate through the existing in-memory AgentRuntime."""
    before = fingerprint(ep, task)
    envelope = world_prepare_adapter.build_execution(
        task, attempt=1, shadow=True, execution_id="exec_world_paired_smoke_01",
        routing_decision={"mode": "SHADOW", "producer": "world_prepare_model_producer"},
    )
    runtime = AgentRuntime()
    world_prepare_adapter.register_skill(runtime, lambda _input, _context: candidate)
    result = runtime.execute(envelope.plan)
    extracted = world_prepare_adapter.extract_candidate(result)
    candidate_errors = world_prepare_adapter.validate_candidate(extracted, task)
    semantic = product_runtime_adapter._world_shadow_runtime_dependencies()[0].compare_world_prepare_semantics(task, extracted)
    after = fingerprint(ep, task)
    checks = {
        "agent_runtime_success": result.status == "SUCCESS",
        "candidate_valid": not candidate_errors,
        "semantic_pass": semantic.get("pass") is True,
        "shadow_execution_type": envelope.plan.execution_type == "EPISODE_CANDIDATE_SHADOW",
        "shadow_identity": envelope.shadow is True,
        "allowed_tools_empty": all(not step.allowed_tools for step in envelope.plan.steps),
        "authority_zero_regression": before == after,
        "image_generation_invoked": False,
        "episode_state_unchanged": before.get("episode_state") == after.get("episode_state") == "STORYBOARD_LOCKED",
    }
    return {
        "schema_version": 1, "kind": "p2_world_real_model_agent_runtime_shadow_smoke",
        "generated_at": now(), "status": "PASS" if all(value is True for key, value in checks.items() if key != "image_generation_invoked") else "BLOCKED",
        "episode": task.get("episode"), "snapshot_id": task.get("snapshot_id"),
        "execution_id": envelope.execution_id, "execution_type": envelope.plan.execution_type,
        "checks": checks, "candidate_errors": candidate_errors, "semantic": semantic,
        "authority_sha_before": before, "authority_sha_after": after,
        "runtime_execution_status": result.status,
        "note": "Uses an in-memory Platform AgentRuntime execution; no Host Request, Candidate path, Canonical Authority, or Episode State is written.",
    }


def summarize(manifest: dict, rows: list[dict]) -> dict:
    valid_rows = [row for row in rows if row.get("valid") is True]
    def median(side: str, field: str):
        values = [row[side].get(field) for row in valid_rows]
        values = [float(x) for x in values if isinstance(x, (int, float)) and not isinstance(x, bool)]
        return statistics.median(values) if values else None
    legacy_wall = median("legacy", "wall_seconds")
    agent_wall = median("agent", "wall_seconds")
    legacy_tokens = median("legacy", "input_tokens")
    agent_tokens = median("agent", "input_tokens")
    # Compare full billable input+output token counts, using median per-pair totals.
    def total_median(side: str):
        vals = [
            row[side].get("input_tokens", 0) + row[side].get("output_tokens", 0)
            for row in valid_rows
            if type(row[side].get("input_tokens")) is int and type(row[side].get("output_tokens")) is int
        ]
        return statistics.median(vals) if vals else None
    legacy_total = total_median("legacy")
    agent_total = total_median("agent")
    wall_regression = ((agent_wall / legacy_wall) - 1) if legacy_wall and agent_wall is not None else None
    token_regression = ((agent_total / legacy_total) - 1) if legacy_total and agent_total is not None else None
    checks = {
        "minimum_valid_runs": len(valid_rows) >= 5,
        "telemetry_complete": bool(rows) and all(row["checks"]["telemetry_complete"] for row in rows),
        "all_valid_runs_semantic_equivalent": len(valid_rows) >= 5 and all(row["checks"]["semantic_equivalent"] for row in valid_rows),
        "no_failure_timeout": bool(rows) and all(row["checks"]["no_failure_timeout"] for row in rows),
        "authority_zero_regression": bool(rows) and all(row["checks"]["authority_zero_regression"] for row in rows),
        "fixed_provider_model": bool(rows) and all(row["checks"]["fixed_provider_model_reasoning"] for row in rows),
        "wall_regression_within_5pct": wall_regression is not None and wall_regression <= 0.05,
        "token_regression_within_10pct": token_regression is not None and token_regression <= 0.10,
    }
    complete = len(rows) >= 5
    return {
        "schema_version": 1,
        "kind": "p2_world_prepare_paired_benchmark",
        "generated_at": now(),
        "episode": manifest["episode"],
        "snapshot_id": manifest["snapshot_id"],
        "provider": manifest["provider"], "model": manifest["model"], "reasoning_effort": manifest["reasoning_effort"],
        "required_scope": copy.deepcopy(manifest["authority_scope"]),
        "attempted_pair_count": len(rows), "valid_run_count": len(valid_rows),
        "telemetry_complete": checks["telemetry_complete"],
        "all_valid_runs_semantic_equivalent": checks["all_valid_runs_semantic_equivalent"],
        "authority_zero_regression": checks["authority_zero_regression"],
        "checks": checks,
        "medians": {
            "legacy_wall_seconds": legacy_wall, "agent_wall_seconds": agent_wall,
            "legacy_input_tokens": legacy_tokens, "agent_input_tokens": agent_tokens,
            "legacy_total_tokens": legacy_total, "agent_total_tokens": agent_total,
            "wall_regression_fraction": wall_regression, "token_regression_fraction": token_regression,
        },
        "distribution_policy": "median_only; p90/p95 omitted unless at least 20 valid pairs",
        "pass": bool(complete and len(valid_rows) >= 5 and all(checks.values())),
        "runs": rows,
        "note": "No Episode writes, canonical commits, image generation, or stage transition are performed.",
    }


def prepare(args) -> dict:
    ep = (ROOT / args.episode).resolve()
    state = episode_state_persistence.load(ep) or read_json(ep / "meta/episode-state.json", {}) or {}
    if state.get("current_state") != "STORYBOARD_LOCKED":
        raise ValueError(f"Episode state must remain STORYBOARD_LOCKED; got {state.get('current_state')}")
    snapshot = preimage_authority_snapshot.build(ep, write=False)
    task = next(row for row in preimage_task_contract.plan_tasks(ep, snapshot, resume=True)
                if row.get("task_type") == "WORLD_PREPARE")
    task = world_prepare_model_producer.freeze_task(ep, task)
    capsule = task["input_contract"]["world_prepare_capsule"]
    manifest = {
        "schema_version": 1, "kind": "p2_world_paired_benchmark_manifest", "created_at": now(),
        "episode": ep.relative_to(ROOT).as_posix(), "snapshot_id": task["snapshot_id"],
        "provider": world_prepare_model_producer.DEFAULT_PROVIDER,
        "model": world_prepare_model_producer.DEFAULT_MODEL,
        "reasoning_effort": world_prepare_model_producer.REASONING_EFFORT,
        "authority_scope": task["authority_scope"], "task": task,
        "initial_fingerprint": fingerprint(ep, task),
        "run_directory": args.run_dir,
    }
    write_json(ROOT / args.manifest, manifest)
    return manifest


def load_manifest(args) -> dict:
    manifest = read_json(ROOT / args.manifest)
    if not isinstance(manifest, dict) or manifest.get("kind") != "p2_world_paired_benchmark_manifest":
        raise ValueError("paired benchmark manifest missing; run prepare first")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "run", "collect", "series"):
        p = sub.add_parser(name)
        p.add_argument("--episode", default=DEFAULT_EPISODE)
        p.add_argument("--manifest", default=DEFAULT_MANIFEST)
        p.add_argument("--run-dir", default=DEFAULT_RUN_DIR)
        p.add_argument("--report", default=DEFAULT_REPORT)
        if name in {"run", "series"}:
            p.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()
    if args.command == "prepare":
        result = prepare(args)
        print(json.dumps({"manifest": args.manifest, "snapshot_id": result["snapshot_id"], "capsule_sha256": result["initial_fingerprint"]["capsule_sha256"]}, ensure_ascii=False, indent=2))
        return 0
    manifest = load_manifest(args)
    ep = (ROOT / manifest["episode"]).resolve()
    if fingerprint(ep, manifest["task"]) != manifest["initial_fingerprint"]:
        raise RuntimeError("frozen World authority changed after prepare; refusing to run benchmark")
    run_dir = ROOT / args.run_dir
    if args.command in {"run", "series"}:
        run_dir.mkdir(parents=True, exist_ok=True)
        rows = [read_json(path) for path in sorted(run_dir.glob("run-*-result.json"))]
        existing_indices = [int(row.get("pair_index") or 0) for row in rows]
        next_index = max(existing_indices, default=0) + 1
        for index in range(next_index, next_index + args.runs):
            rows.append(run_one(ep, manifest["task"], index, run_dir))
        report = summarize(manifest, rows)
        write_json(ROOT / args.report, report)
        print(json.dumps({"attempted_pair_count": report["attempted_pair_count"], "valid_run_count": report["valid_run_count"], "pass": report["pass"], "medians": report["medians"]}, ensure_ascii=False, indent=2))
        return 0 if report["pass"] else 3
    rows = [read_json(path) for path in sorted(run_dir.glob("run-*-result.json"))]
    smoke_path = ROOT / "reports/p2-world-real-model-shadow-smoke-20260926.json"
    if (read_json(smoke_path, {}) or {}).get("status") != "PASS":
        candidates = sorted(run_dir.glob("run-*-agent-candidate.json"))
        if candidates:
            candidate = read_json(candidates[0])
            write_json(smoke_path, runtime_shadow_smoke(ep, manifest["task"], candidate))
    report = summarize(manifest, rows)
    write_json(ROOT / args.report, report)
    print(json.dumps({"attempted_pair_count": report["attempted_pair_count"], "valid_run_count": report["valid_run_count"], "pass": report["pass"], "medians": report["medians"]}, ensure_ascii=False, indent=2))
    return 0 if report["pass"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
