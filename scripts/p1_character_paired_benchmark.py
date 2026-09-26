#!/usr/bin/env python3
"""Paired Character legacy-control versus Agent-shadow benchmark.

prepare freezes one Episode snapshot into an isolated manifest. External Host
executions author two Candidate JSON files from the same task. collect validates
both and measures only explicit model_execution telemetry.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes/_system"
sys.path[:0] = [str(SYSTEM), str(ROOT)]

import agent_shadow_compare
import character_contract
import character_visual_contract
import episode_state_persistence
import preimage_authority_snapshot
import preimage_task_contract
import story_json
from scripts.phase9_runtime_launcher import load_runtime_env_file
from agents import character_finalize_model_producer

DEFAULT_MANIFEST = ROOT / ".storyos/tmp/p1-character-paired-benchmark.json"
DEFAULT_LEGACY = ROOT / ".storyos/tmp/p1-character-legacy-benchmark-candidate.json"
DEFAULT_SHADOW = ROOT / ".storyos/tmp/p1-character-agent-benchmark-candidate.json"
DEFAULT_REPORT = ROOT / "reports/p1-character-paired-benchmark-20260926.json"
WALL_REGRESSION_MAX = 0.05
TOKEN_REGRESSION_MAX = 0.10


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def _sha(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _source_fingerprint(ep: Path) -> dict:
    gates = story_json.read_json(ep / "meta/story-gates.json", default={}) or {}
    return {
        "episode_state": (episode_state_persistence.load(ep) or {}).get("current_state"),
        "story_gates_sha256": _sha(gates),
        "character_contract_sha256": character_contract.authority_sha256(ep),
        "character_visual_contract_sha256": character_visual_contract.authority_sha256(ep),
    }


def _run_contract(task: dict, role: str) -> dict:
    return {
        "role": role,
        "task_id": task["task_id"],
        "task_type": task["task_type"],
        "snapshot_id": task["snapshot_id"],
        "source_authority_sha256": task["input_contract"]["source_authority_sha256"],
        "authority_scope": list(task["authority_scope"]),
        "must_not_write_episode": True,
        "telemetry_required": [
            "real_model_execution", "wall_seconds", "input_tokens", "output_tokens",
            "repeated_reads", "failure", "timeout", "provider", "model", "telemetry_source"
        ],
        "missing_telemetry_must_not_be_estimated": True,
    }


def prepare(ep: Path, manifest_path: Path) -> dict:
    ep = ep.resolve()
    before = _source_fingerprint(ep)
    snapshot = preimage_authority_snapshot.build(ep, write=False)
    task = preimage_task_contract.task_contract(
        ep, "CHARACTER_FINALIZE", snapshot, resume=True
    )
    manifest = {
        "schema_version": 1,
        "kind": "p1_character_paired_benchmark",
        "prepared_at": now(),
        "source_episode": ep.relative_to(ROOT).as_posix(),
        "source_fingerprint": before,
        "snapshot_id": snapshot["snapshot_id"],
        "task": task,
        "same_input_snapshot_required": True,
        "runs": {
            "legacy_control": _run_contract(task, "legacy_control"),
            "agent_shadow": _run_contract(task, "agent_shadow"),
        },
        "thresholds": {
            "wall_regression_max": WALL_REGRESSION_MAX,
            "token_regression_max": TOKEN_REGRESSION_MAX,
        },
    }
    if _source_fingerprint(ep) != before:
        raise RuntimeError("paired benchmark prepare changed Episode authority")
    manifest["source_authority_unchanged_after_prepare"] = True
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    return manifest


def _regression(candidate: float, baseline: float) -> float | None:
    if baseline < 0 or candidate < 0:
        return None
    if baseline == 0:
        return 0.0 if candidate == 0 else None
    return (candidate - baseline) / baseline


def evaluate_pair(task: dict, legacy: dict, shadow: dict, *, source_unchanged: bool) -> dict:
    legacy_errors = preimage_task_contract.verify_candidate(legacy, task)
    shadow_errors = preimage_task_contract.verify_candidate(shadow, task)
    comparison = agent_shadow_compare.compare_preimage_candidates(task, legacy, shadow)
    legacy_exec = preimage_task_contract.model_execution_evidence(legacy)
    shadow_exec = preimage_task_contract.model_execution_evidence(shadow)
    telemetry_complete = legacy_exec["complete"] and shadow_exec["complete"]

    legacy_tokens = shadow_tokens = None
    wall_regression = token_regression = None
    if telemetry_complete:
        legacy_tokens = int(legacy_exec["input_tokens"]) + int(legacy_exec["output_tokens"])
        shadow_tokens = int(shadow_exec["input_tokens"]) + int(shadow_exec["output_tokens"])
        wall_regression = _regression(
            float(shadow_exec["wall_seconds"]), float(legacy_exec["wall_seconds"])
        )
        token_regression = _regression(float(shadow_tokens), float(legacy_tokens))

    semantic_equivalent = bool(
        comparison.get("structural_equal") is True
        or ((comparison.get("domain_semantic") or {}).get("semantic_equivalent") is True)
    )
    no_failure_timeout = bool(
        telemetry_complete
        and legacy_exec["failure"] is False
        and shadow_exec["failure"] is False
        and legacy_exec["timeout"] is False
        and shadow_exec["timeout"] is False
    )
    checks = {
        "same_contract_valid": not legacy_errors and not shadow_errors,
        "semantic_equivalent": semantic_equivalent,
        "telemetry_complete": telemetry_complete,
        "no_failure_timeout": no_failure_timeout,
        "wall_regression_within_5pct": bool(
            wall_regression is not None and wall_regression <= WALL_REGRESSION_MAX
        ),
        "token_regression_within_10pct": bool(
            token_regression is not None and token_regression <= TOKEN_REGRESSION_MAX
        ),
        "authority_zero_regression": bool(source_unchanged),
    }
    return {
        "schema_version": 1,
        "kind": "p1_character_paired_benchmark_result",
        "generated_at": now(),
        "checks": checks,
        "pass": all(checks.values()),
        "legacy_errors": legacy_errors,
        "shadow_errors": shadow_errors,
        "comparison": comparison,
        "legacy_execution": legacy_exec,
        "shadow_execution": shadow_exec,
        "metrics": {
            "legacy_wall_seconds": legacy_exec.get("wall_seconds"),
            "shadow_wall_seconds": shadow_exec.get("wall_seconds"),
            "wall_regression": wall_regression,
            "legacy_total_tokens": legacy_tokens,
            "shadow_total_tokens": shadow_tokens,
            "token_regression": token_regression,
            "legacy_repeated_reads": legacy_exec.get("repeated_reads"),
            "shadow_repeated_reads": shadow_exec.get("repeated_reads"),
        },
        "thresholds": {
            "wall_regression_max": WALL_REGRESSION_MAX,
            "token_regression_max": TOKEN_REGRESSION_MAX,
        },
        "production_cutover_performed": False,
    }


def _sample_summary(values: list[float]) -> dict:
    rows = [float(value) for value in values]
    if not rows:
        return {
            "count": 0,
            "median": None,
            "min": None,
            "max": None,
            "p90": None,
            "p95": None,
            "percentile_policy": "unavailable_no_samples",
        }
    return {
        "count": len(rows),
        "median": statistics.median(rows),
        "min": min(rows),
        "max": max(rows),
        "p90": None,
        "p95": None,
        "percentile_policy": "omitted_below_20_samples" if len(rows) < 20 else "not_implemented",
    }


def _aggregate_execution(run_reports: list[dict], side: str) -> dict:
    rows = [dict(row.get(f"{side}_execution") or {}) for row in run_reports]
    providers = {str(row.get("provider") or "") for row in rows if row.get("provider")}
    models = {str(row.get("model") or "") for row in rows if row.get("model")}
    sources = {str(row.get("telemetry_source") or "") for row in rows if row.get("telemetry_source")}
    walls = [float(row["wall_seconds"]) for row in rows]
    inputs = [int(row["input_tokens"]) for row in rows]
    outputs = [int(row["output_tokens"]) for row in rows]
    reads = [int(row["repeated_reads"]) for row in rows]
    return {
        "schema_version": 1,
        "complete": bool(rows) and all(row.get("complete") is True for row in rows),
        "real_model_execution": bool(rows) and all(row.get("real_model_execution") is True for row in rows),
        "wall_seconds": statistics.median(walls) if walls else None,
        "input_tokens": int(round(statistics.median(inputs))) if inputs else None,
        "output_tokens": int(round(statistics.median(outputs))) if outputs else None,
        "repeated_reads": int(round(statistics.median(reads))) if reads else None,
        "failure": any(row.get("failure") is True for row in rows),
        "timeout": any(row.get("timeout") is True for row in rows),
        "provider": next(iter(providers)) if len(providers) == 1 else None,
        "model": next(iter(models)) if len(models) == 1 else None,
        "telemetry_source": next(iter(sources)) if len(sources) == 1 else None,
        "sample_count": len(rows),
        "aggregation": "median_of_valid_paired_runs",
    }


def aggregate_series(run_reports: list[dict], *, requested_runs: int) -> dict:
    validity_keys = (
        "same_contract_valid",
        "semantic_equivalent",
        "telemetry_complete",
        "no_failure_timeout",
        "authority_zero_regression",
    )
    valid = [
        row for row in run_reports
        if all((row.get("checks") or {}).get(key) is True for key in validity_keys)
    ]
    legacy_walls = [float(row["legacy_execution"]["wall_seconds"]) for row in valid]
    shadow_walls = [float(row["shadow_execution"]["wall_seconds"]) for row in valid]
    legacy_tokens = [
        int(row["legacy_execution"]["input_tokens"]) + int(row["legacy_execution"]["output_tokens"])
        for row in valid
    ]
    shadow_tokens = [
        int(row["shadow_execution"]["input_tokens"]) + int(row["shadow_execution"]["output_tokens"])
        for row in valid
    ]
    legacy_wall_summary = _sample_summary(legacy_walls)
    shadow_wall_summary = _sample_summary(shadow_walls)
    legacy_token_summary = _sample_summary(legacy_tokens)
    shadow_token_summary = _sample_summary(shadow_tokens)
    wall_regression = (
        _regression(shadow_wall_summary["median"], legacy_wall_summary["median"])
        if valid else None
    )
    token_regression = (
        _regression(shadow_token_summary["median"], legacy_token_summary["median"])
        if valid else None
    )
    providers = {
        str(exec_row.get("provider") or "")
        for row in valid
        for exec_row in (row.get("legacy_execution") or {}, row.get("shadow_execution") or {})
        if exec_row.get("provider")
    }
    models = {
        str(exec_row.get("model") or "")
        for row in valid
        for exec_row in (row.get("legacy_execution") or {}, row.get("shadow_execution") or {})
        if exec_row.get("model")
    }
    checks = {
        "minimum_valid_runs": len(valid) >= int(requested_runs) and int(requested_runs) >= 5,
        "all_valid_runs_semantic_equivalent": bool(valid) and all(
            (row.get("checks") or {}).get("semantic_equivalent") is True for row in valid
        ),
        "telemetry_complete": bool(valid) and all(
            (row.get("checks") or {}).get("telemetry_complete") is True for row in valid
        ),
        "no_failure_timeout": bool(valid) and all(
            (row.get("checks") or {}).get("no_failure_timeout") is True for row in valid
        ),
        "authority_zero_regression": bool(valid) and all(
            (row.get("checks") or {}).get("authority_zero_regression") is True for row in valid
        ),
        "fixed_provider_model": len(providers) == 1 and len(models) == 1,
        "wall_regression_within_5pct": bool(
            wall_regression is not None and wall_regression <= WALL_REGRESSION_MAX
        ),
        "token_regression_within_10pct": bool(
            token_regression is not None and token_regression <= TOKEN_REGRESSION_MAX
        ),
    }
    report = {
        "schema_version": 2,
        "kind": "p1_character_paired_benchmark_series_result",
        "generated_at": now(),
        "requested_valid_runs": int(requested_runs),
        "attempted_run_count": len(run_reports),
        "valid_run_count": len(valid),
        "checks": checks,
        "pass": all(checks.values()),
        "legacy_execution": _aggregate_execution(valid, "legacy") if valid else {},
        "shadow_execution": _aggregate_execution(valid, "shadow") if valid else {},
        "metrics": {
            "legacy_wall_seconds": legacy_wall_summary["median"],
            "shadow_wall_seconds": shadow_wall_summary["median"],
            "wall_regression": wall_regression,
            "legacy_total_tokens": legacy_token_summary["median"],
            "shadow_total_tokens": shadow_token_summary["median"],
            "token_regression": token_regression,
            "legacy_wall_samples": legacy_wall_summary,
            "shadow_wall_samples": shadow_wall_summary,
            "legacy_token_samples": legacy_token_summary,
            "shadow_token_samples": shadow_token_summary,
            "individual_wall_regressions": [
                (row.get("metrics") or {}).get("wall_regression") for row in run_reports
            ],
            "individual_token_regressions": [
                (row.get("metrics") or {}).get("token_regression") for row in run_reports
            ],
        },
        "thresholds": {
            "wall_regression_max": WALL_REGRESSION_MAX,
            "token_regression_max": TOKEN_REGRESSION_MAX,
            "minimum_valid_runs": 5,
        },
        "runs": run_reports,
        "production_cutover_performed": False,
        "note": (
            "Acceptance uses medians across at least five valid paired runs. "
            "Every raw run remains in the report; provider jitter is not discarded."
        ),
    }
    return report


def run_real_pair(
    ep: Path,
    manifest_path: Path,
    legacy_path: Path,
    shadow_path: Path,
    report_path: Path,
    *,
    timeout_seconds: int = 900,
    model: str | None = None,
) -> dict:
    import concurrent.futures as cf

    ep = ep.resolve()
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.is_file()
        else prepare(ep, manifest_path)
    )
    task = manifest["task"]
    source_before = _source_fingerprint(ep)

    def invoke(role: str):
        return character_finalize_model_producer.run(
            ep, task, role=role, timeout_seconds=timeout_seconds, model=model
        )

    with cf.ThreadPoolExecutor(max_workers=2, thread_name_prefix="p1-character-pair") as pool:
        future_legacy = pool.submit(invoke, "legacy_control")
        future_shadow = pool.submit(invoke, "agent_shadow")
        legacy = future_legacy.result()
        shadow = future_shadow.result()

    if _source_fingerprint(ep) != source_before:
        raise RuntimeError("real paired benchmark changed Episode authority")
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_path.write_text(
        json.dumps(legacy, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    shadow_path.parent.mkdir(parents=True, exist_ok=True)
    shadow_path.write_text(
        json.dumps(shadow, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    return collect(ep, manifest_path, legacy_path, shadow_path, report_path)


def run_real_series(
    ep: Path,
    manifest_path: Path,
    report_path: Path,
    *,
    runs: int = 5,
    timeout_seconds: int = 900,
    model: str | None = None,
) -> dict:
    import concurrent.futures as cf

    if int(runs) < 5:
        raise ValueError("formal paired benchmark requires at least 5 runs")
    ep = ep.resolve()
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.is_file()
        else prepare(ep, manifest_path)
    )
    task = manifest["task"]
    source_before = _source_fingerprint(ep)
    run_dir = ROOT / ".storyos/tmp/p1-character-paired-runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []

    def invoke(role: str):
        return character_finalize_model_producer.run(
            ep, task, role=role, timeout_seconds=timeout_seconds, model=model
        )

    for index in range(1, int(runs) + 1):
        with cf.ThreadPoolExecutor(max_workers=2, thread_name_prefix=f"p1-character-pair-{index}") as pool:
            future_legacy = pool.submit(invoke, "legacy_control")
            future_shadow = pool.submit(invoke, "agent_shadow")
            legacy = future_legacy.result()
            shadow = future_shadow.result()
        source_unchanged = _source_fingerprint(ep) == source_before == manifest.get("source_fingerprint")
        if not source_unchanged:
            raise RuntimeError(f"real paired benchmark changed Episode authority during run {index}")
        legacy_path = run_dir / f"run-{index:02d}-legacy.json"
        shadow_path = run_dir / f"run-{index:02d}-shadow.json"
        legacy_path.write_text(
            json.dumps(legacy, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n",
        )
        shadow_path.write_text(
            json.dumps(shadow, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n",
        )
        row = evaluate_pair(task, legacy, shadow, source_unchanged=source_unchanged)
        row.update({
            "run_index": index,
            "legacy_candidate_path": legacy_path.relative_to(ROOT).as_posix(),
            "shadow_candidate_path": shadow_path.relative_to(ROOT).as_posix(),
        })
        results.append(row)

    report = aggregate_series(results, requested_runs=int(runs))
    report.update({
        "source_episode": manifest["source_episode"],
        "snapshot_id": manifest["snapshot_id"],
        "model_requested": model,
        "reasoning_effort": "medium",
        "provider": "codex_cli_subscription",
        "same_input_snapshot": True,
    })
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def collect(ep: Path, manifest_path: Path, legacy_path: Path, shadow_path: Path, report_path: Path) -> dict:
    ep = ep.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_episode") != ep.relative_to(ROOT).as_posix():
        raise ValueError("benchmark manifest episode mismatch")
    task = manifest["task"]
    if task.get("snapshot_id") != manifest.get("snapshot_id"):
        raise ValueError("benchmark manifest snapshot mismatch")
    legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
    shadow = json.loads(shadow_path.read_text(encoding="utf-8"))
    source_unchanged = _source_fingerprint(ep) == manifest.get("source_fingerprint")
    report = evaluate_pair(task, legacy, shadow, source_unchanged=source_unchanged)
    report.update({
        "source_episode": manifest["source_episode"],
        "snapshot_id": manifest["snapshot_id"],
        "legacy_candidate_path": legacy_path.relative_to(ROOT).as_posix(),
        "shadow_candidate_path": shadow_path.relative_to(ROOT).as_posix(),
    })
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def _load_runtime_env() -> None:
    path = ROOT / ".storyos/runtime-launcher/runtime.env"
    if not path.is_file():
        return
    env, _meta = load_runtime_env_file(path, dict(os.environ))
    os.environ.update(env)


def main() -> int:
    _load_runtime_env()
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("episode_dir")
    p.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    p = sub.add_parser("collect")
    p.add_argument("episode_dir")
    p.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    p.add_argument("--legacy", default=str(DEFAULT_LEGACY))
    p.add_argument("--shadow", default=str(DEFAULT_SHADOW))
    p.add_argument("--report", default=str(DEFAULT_REPORT))
    p = sub.add_parser("run")
    p.add_argument("episode_dir")
    p.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    p.add_argument("--legacy", default=str(DEFAULT_LEGACY))
    p.add_argument("--shadow", default=str(DEFAULT_SHADOW))
    p.add_argument("--report", default=str(DEFAULT_REPORT))
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("--model", default=None)
    p.add_argument("--runs", type=int, default=5)
    args = ap.parse_args()
    ep = Path(args.episode_dir).resolve()
    if args.cmd == "prepare":
        row = prepare(ep, Path(args.manifest).resolve())
        print(json.dumps({
            "manifest": Path(args.manifest).resolve().relative_to(ROOT).as_posix(),
            "snapshot_id": row["snapshot_id"],
            "source_authority_unchanged": row["source_authority_unchanged_after_prepare"],
        }, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "run":
        if int(args.runs) == 1:
            report = run_real_pair(
                ep,
                Path(args.manifest).resolve(),
                Path(args.legacy).resolve(),
                Path(args.shadow).resolve(),
                Path(args.report).resolve(),
                timeout_seconds=int(args.timeout),
                model=args.model,
            )
        else:
            report = run_real_series(
                ep,
                Path(args.manifest).resolve(),
                Path(args.report).resolve(),
                runs=int(args.runs),
                timeout_seconds=int(args.timeout),
                model=args.model,
            )
        return 0 if report["pass"] else 3
    report = collect(
        ep, Path(args.manifest).resolve(), Path(args.legacy).resolve(),
        Path(args.shadow).resolve(), Path(args.report).resolve()
    )
    return 0 if report["pass"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
