#!/usr/bin/env python3
"""Evidence-bound Character Agent production cutover.

The command is dry-run by default. --apply is allowed only from the canonical
pre-cutover state (shadow=true, production=false), with a READY cutover gate and
a formal five-run paired benchmark. After the atomic config transition it runs
an isolated production-path smoke. Any smoke failure restores the original
config before returning failure.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes/_system"
sys.path[:0] = [str(SYSTEM), str(ROOT)]

import runtime_atomic_store as atomic
import storyos_config

CONFIG = ROOT / "config/storyos.yaml"
DEFAULT_GATE = ROOT / "reports/p1-character-pre-cutover-gate-20260926.json"
DEFAULT_BENCHMARK = ROOT / "reports/p1-character-paired-benchmark-20260926.json"
DEFAULT_RECEIPT = ROOT / "reports/p1-character-production-cutover-20260926.json"
DEFAULT_SMOKE = ROOT / "reports/p1-character-production-cutover-smoke-20260926.json"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    if not Path(path).is_file():
        return {}
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _parse_time(value) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def adapter_state() -> dict:
    cfg = storyos_config.load_config()
    return {
        "shadow_enabled": storyos_config.get_path(
            cfg, "agent_runtime.adapters.character_finalize.shadow_enabled", False
        ) is True,
        "production_enabled": storyos_config.get_path(
            cfg, "agent_runtime.adapters.character_finalize.production_enabled", False
        ) is True,
        "legacy_fallback_on_technical": storyos_config.get_path(
            cfg, "agent_runtime.adapters.character_finalize.legacy_fallback_on_technical", False
        ) is True,
    }


def validate_preflight(gate: dict, benchmark: dict, state: dict) -> list[str]:
    errors: list[str] = []
    if gate.get("kind") != "p1_character_pre_cutover_gate" or gate.get("immutable") is not True:
        errors.append("a typed immutable pre-cutover PASS evidence is required")
    if gate.get("status") != "PASS":
        errors.append("pre-cutover gate evidence is not PASS")
    gate_checks = gate.get("checks") or {}
    required_gate_checks = (
        "p0_commit_gate", "clean_head_protocol_baseline", "shadow_probe_valid",
        "shadow_smoke_valid", "paired_benchmark_pass",
        "historical_cutover_gate_was_ready", "historical_production_smoke_pass",
    )
    if any(gate_checks.get(key) is not True for key in required_gate_checks):
        errors.append("pre-cutover gate prerequisite checks are incomplete or failed")
    if (gate.get("proof") or {}).get("method") != "recomputed_from_preserved_prerequisite_evidence":
        errors.append("pre-cutover gate does not carry recomputed evidence provenance")
    if gate.get("production_cutover_performed") is True:
        errors.append("pre-cutover gate must not claim production cutover")
    if gate.get("blockers"):
        errors.append("cutover gate still has blockers")
    gate_state = gate.get("adapter_state_at_gate") or gate.get("adapter_state") or {}
    if gate_state.get("shadow_enabled") is not True:
        errors.append("gate evidence was not produced in shadow state")
    if gate_state.get("production_enabled") is not False:
        errors.append("gate evidence was not produced with production disabled")

    checks = benchmark.get("checks") or {}
    required_checks = (
        "minimum_valid_runs",
        "all_valid_runs_semantic_equivalent",
        "telemetry_complete",
        "no_failure_timeout",
        "authority_zero_regression",
        "fixed_provider_model",
        "wall_regression_within_5pct",
        "token_regression_within_10pct",
    )
    if benchmark.get("pass") is not True:
        errors.append("paired benchmark did not pass")
    if int(benchmark.get("schema_version") or 0) < 2:
        errors.append("paired benchmark is not formal series schema v2")
    if int(benchmark.get("valid_run_count") or 0) < 5:
        errors.append("paired benchmark has fewer than five valid runs")
    for key in required_checks:
        if checks.get(key) is not True:
            errors.append(f"paired benchmark check failed: {key}")

    gate_at = _parse_time(gate.get("generated_at"))
    bench_at = _parse_time(benchmark.get("generated_at"))
    if gate_at is None or bench_at is None or gate_at < bench_at:
        errors.append("cutover gate must be generated after the paired benchmark")

    sources = gate.get("source_evidence") or {}
    source_rows = [item for item in sources.values() if isinstance(item, dict)]
    if not source_rows or any(
        not (ROOT / str(item.get("path", ""))).is_file()
        or sha256_file(ROOT / str(item.get("path", ""))) != item.get("sha256")
        for item in source_rows
    ):
        errors.append("immutable pre-cutover gate source evidence is missing or changed")

    if state.get("shadow_enabled") is not True:
        errors.append("current config must have Character shadow enabled before apply")
    if state.get("production_enabled") is not False:
        errors.append("current config must have Character production disabled before apply")
    if state.get("legacy_fallback_on_technical") is not True:
        errors.append("technical legacy fallback must remain enabled for initial production cutover")
    return errors


def transition_config_text(text: str, *, shadow_enabled: bool, production_enabled: bool) -> str:
    pattern = re.compile(
        r"(?m)(^    character_finalize:\r?\n)(?P<body>(?:(?!^    [A-Za-z0-9_]+:)[^\r\n]*(?:\r?\n|$))+)"
    )
    match = pattern.search(text)
    if not match:
        raise ValueError("character_finalize adapter block not found in config/storyos.yaml")
    body = match.group("body")
    new_body, shadow_count = re.subn(
        r"(?m)^      shadow_enabled: (?:true|false)[ \t]*$",
        f"      shadow_enabled: {'true' if shadow_enabled else 'false'}",
        body,
    )
    new_body, production_count = re.subn(
        r"(?m)^      production_enabled: (?:true|false)[ \t]*$",
        f"      production_enabled: {'true' if production_enabled else 'false'}",
        new_body,
    )
    if shadow_count != 1 or production_count != 1:
        raise ValueError("character_finalize config must contain exactly one shadow/production flag")
    return text[:match.start("body")] + new_body + text[match.end("body"):]


def _write_config_text(text: str) -> None:
    atomic.atomic_write_text(CONFIG, text)
    storyos_config._CACHE.pop(storyos_config.CONFIG_PATH, None)


def _production_smoke() -> dict:
    import host_request_persistence
    import preimage_execution_persistence as execution
    import preimage_task_contract as tasks
    import product_runtime_adapter as adapter

    base = ROOT / ".storyos-tmp"
    base.mkdir(exist_ok=True)
    raw = tempfile.mkdtemp(prefix="p1-cutover-smoke-", dir=base)
    ep = Path(raw)
    old_workspace = os.environ.get("STORY_OS_RUNTIME_WORKSPACE")
    old_meta_store = host_request_persistence.storage_config.episode_meta_store_config
    old_mode = execution.mode
    try:
        os.environ["STORY_OS_RUNTIME_WORKSPACE"] = str(ep / "_runtime-workspace")
        host_request_persistence.storage_config.episode_meta_store_config = lambda: {"mode": "json"}
        execution.mode = lambda: "json"
        (ep / "meta").mkdir(parents=True, exist_ok=True)
        (ep / "meta/episode-state.json").write_text(
            json.dumps({"current_state": "STORYBOARD_LOCKED"}), encoding="utf-8"
        )
        (ep / "meta/story-gates.json").write_text(
            json.dumps({"story": {"locked": True}, "visual": {}}), encoding="utf-8"
        )

        response = adapter.build_request(
            ep, runtime="WORK", mode="full_auto", resume=True, source="p1-cutover-apply-smoke"
        )
        requests = response.get("requests") or []
        if len(requests) != 4 or response.get("shadow_requests"):
            raise RuntimeError("production smoke expected 4 canonical requests and no shadow requests")
        character = next(
            row for row in requests if (row.get("task") or {}).get("task_type") == "CHARACTER_FINALIZE"
        )
        if character.get("agent_adapter") != "CHARACTER_FINALIZE_AGENT":
            raise RuntimeError("production smoke Character request did not use Agent Adapter")
        if (character.get("agent_execution") or {}).get("shadow") is not False:
            raise RuntimeError("production smoke Character execution is not live")

        for index, request in enumerate(requests, start=1):
            adapter.mark_preimage_task_running(
                ep, request["request_id"], worker_id=f"cutover-smoke-{index}"
            )

        final_rows = []
        for request in requests:
            task = request["task"]
            candidate = tasks.candidate_template(task, tasks.valid_payload(task))
            final_rows.append(adapter.complete_preimage_task(ep, request["request_id"], candidate))

        commit_rows = [row for row in final_rows if isinstance(row.get("authority_commit"), dict)]
        if len(commit_rows) != 1:
            raise RuntimeError("production smoke expected exactly one authority commit")
        commit = commit_rows[0]["authority_commit"]
        meta = character["agent_execution"]
        record = execution.find_execution(
            ep,
            character["task"]["snapshot_id"],
            character["task"]["task_id"],
            meta["execution_id"],
        )
        saved = host_request_persistence.load(ep, character["request_id"]) or {}
        passed = bool(
            commit.get("status") == "PASS"
            and commit.get("committed") is True
            and record
            and record.get("status") == "COMMITTED"
            and record.get("eligible") is False
            and (record.get("commit_receipt") or {}).get("status") == "COMMITTED"
            and saved.get("agent_fallback_active") is not True
        )
        if not passed:
            raise RuntimeError("production smoke did not reach committed Agent receipt")
        return {
            "schema_version": 2,
            "kind": "p1_character_production_cutover_smoke",
            "generated_at": now(),
            "production_enabled": True,
            "shadow_enabled": False,
            "canonical_request_count": len(requests),
            "shadow_request_count": 0,
            "character_agent_adapter": character.get("agent_adapter"),
            "authority_commit_status": commit.get("status"),
            "authority_committed": commit.get("committed"),
            "execution_status": record.get("status"),
            "execution_eligible": record.get("eligible"),
            "receipt_status": (record.get("commit_receipt") or {}).get("status"),
            "legacy_fallback_active": bool(saved.get("agent_fallback_active")),
            "episode_state": "STORYBOARD_LOCKED",
            "isolated_temp_episode": True,
            "real_episode_authority_touched": False,
            "pass": True,
        }
    finally:
        host_request_persistence.storage_config.episode_meta_store_config = old_meta_store
        execution.mode = old_mode
        if old_workspace is None:
            os.environ.pop("STORY_OS_RUNTIME_WORKSPACE", None)
        else:
            os.environ["STORY_OS_RUNTIME_WORKSPACE"] = old_workspace
        shutil.rmtree(ep, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", default=str(DEFAULT_GATE))
    ap.add_argument("--benchmark", default=str(DEFAULT_BENCHMARK))
    ap.add_argument("--receipt", default=str(DEFAULT_RECEIPT))
    ap.add_argument("--smoke-report", default=str(DEFAULT_SMOKE))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    gate_path = Path(args.gate).resolve()
    benchmark_path = Path(args.benchmark).resolve()
    receipt_path = Path(args.receipt).resolve()
    smoke_path = Path(args.smoke_report).resolve()
    gate = read_json(gate_path)
    benchmark = read_json(benchmark_path)
    before_state = adapter_state()
    errors = validate_preflight(gate, benchmark, before_state)
    paired_source = (gate.get("source_evidence") or {}).get("paired") or {}
    if (
        paired_source.get("path") != benchmark_path.relative_to(ROOT).as_posix()
        or paired_source.get("sha256") != (sha256_file(benchmark_path) if benchmark_path.is_file() else None)
    ):
        errors.append("pre-cutover gate is not bound to the supplied paired benchmark")
    plan = {
        "schema_version": 1,
        "kind": "p1_character_production_cutover_plan",
        "generated_at": now(),
        "ready": not errors,
        "apply_requested": bool(args.apply),
        "errors": errors,
        "adapter_state_before": before_state,
        "adapter_state_after": {
            "shadow_enabled": False,
            "production_enabled": True,
            "legacy_fallback_on_technical": True,
        },
        "evidence": {
            "cutover_gate": {
                "path": gate_path.relative_to(ROOT).as_posix(),
                "sha256": sha256_file(gate_path) if gate_path.is_file() else None,
                "generated_at": gate.get("generated_at"),
            },
            "paired_benchmark": {
                "path": benchmark_path.relative_to(ROOT).as_posix(),
                "sha256": sha256_file(benchmark_path) if benchmark_path.is_file() else None,
                "generated_at": benchmark.get("generated_at"),
                "valid_run_count": benchmark.get("valid_run_count"),
            },
        },
    }
    if errors:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 3
    if not args.apply:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    original_text = CONFIG.read_text(encoding="utf-8-sig")
    production_text = transition_config_text(
        original_text, shadow_enabled=False, production_enabled=True
    )
    try:
        _write_config_text(production_text)
        after_state = adapter_state()
        if after_state != plan["adapter_state_after"]:
            raise RuntimeError(f"post-cutover config mismatch: {after_state}")
        smoke = _production_smoke()
        atomic.atomic_write_json(smoke_path, smoke)
    except Exception as exc:
        _write_config_text(original_text)
        failure = {
            **plan,
            "kind": "p1_character_production_cutover_record",
            "status": "ROLLED_BACK_AFTER_SMOKE_FAILURE",
            "production_cutover_performed": False,
            "rolled_back": True,
            "failure": f"{type(exc).__name__}: {exc}",
            "adapter_state_after_rollback": adapter_state(),
        }
        atomic.atomic_write_json(receipt_path, failure)
        print(json.dumps(failure, ensure_ascii=False, indent=2))
        return 4

    receipt = {
        "schema_version": 2,
        "kind": "p1_character_production_cutover_record",
        "generated_at": now(),
        "status": "PRODUCTION_ENABLED",
        "checks": {
            "cutover_gate_ready": True,
            "formal_five_run_benchmark_pass": True,
            "paired_authority_zero_regression": True,
            "production_enabled": True,
            "shadow_disabled": True,
            "production_smoke_pass": True,
            "receipt_committed": True,
            "legacy_fallback_not_used": smoke.get("legacy_fallback_active") is False,
        },
        "adapter_state_before": before_state,
        "adapter_state_after": adapter_state(),
        "evidence": {
            **plan["evidence"],
            "production_smoke": {
                "path": smoke_path.relative_to(ROOT).as_posix(),
                "sha256": sha256_file(smoke_path),
                "generated_at": smoke.get("generated_at"),
            },
            "production_runtime_adapter": {
                "path": "episodes/_system/product_runtime_adapter.py",
                "sha256": sha256_file(ROOT / "episodes/_system/product_runtime_adapter.py"),
            },
            "cutover_apply": {
                "path": "scripts/p1_character_cutover_apply.py",
                "sha256": sha256_file(Path(__file__).resolve()),
            },
        },
        "rollback": {
            "production_enabled": False,
            "shadow_enabled": True,
            "legacy_fallback_preserved": True,
        },
        "production_cutover_performed": True,
    }
    atomic.atomic_write_json(receipt_path, receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
