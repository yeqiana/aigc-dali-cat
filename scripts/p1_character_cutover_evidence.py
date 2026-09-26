#!/usr/bin/env python3
"""Reconstruct immutable P1 pre-cutover evidence and report post-cutover health."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes/_system"
sys.path[:0] = [str(SYSTEM), str(ROOT)]

import runtime_atomic_store as atomic
import storyos_config


DEFAULT_PRE_GATE = ROOT / "reports/p1-character-pre-cutover-gate-20260926.json"
DEFAULT_RECORD = ROOT / "reports/p1-character-production-cutover-20260926.json"
DEFAULT_HISTORICAL_RECORD = ROOT / "reports/p1-character-cutover-record-pre-repair-20260926.json"
DEFAULT_HEALTH = ROOT / "reports/p1-character-post-cutover-health-20260926.json"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source(path: Path) -> dict:
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)}


def write_immutable_pre_gate(path: Path, report: dict) -> None:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"immutable pre-cutover gate already exists: {path}")
    atomic.atomic_write_json(path, report)


def reconstruct_pre_cutover_gate(
    *, p0: dict, p0_baseline: dict, probe: dict, shadow_smoke: dict,
    paired: dict, original_cutover_record: dict,
) -> dict:
    """Re-evaluate genuine prerequisite evidence; never trust edited gate values."""
    p0_summary = p0_baseline.get("summary") or {}
    checks = {
        "p0_commit_gate": p0.get("commit_gate_ready") is True,
        "clean_head_protocol_baseline": bool(
            p0_baseline.get("git_worktree_clean") is True
            and int(p0_summary.get("successful_runs") or 0) >= 5
            and int(p0_summary.get("failed_runs") or 0) == 0
        ),
        "shadow_probe_valid": bool(
            probe.get("source_authority_unchanged") is True
            and not (probe.get("verifier_errors") or [])
            and (probe.get("comparison") or {}).get("legacy_valid") is True
            and (probe.get("comparison") or {}).get("shadow_valid") is True
            and (probe.get("comparison") or {}).get("canonical_side_effect") is False
        ),
        "shadow_smoke_valid": bool(
            shadow_smoke.get("authority_unchanged") is True
            and (shadow_smoke.get("comparison") or {}).get("canonical_side_effect") is False
            and (shadow_smoke.get("comparison") or {}).get("structural_equal") is True
        ),
    }
    paired_checks = paired.get("checks") or {}
    required = (
        "minimum_valid_runs", "all_valid_runs_semantic_equivalent", "telemetry_complete",
        "no_failure_timeout", "authority_zero_regression", "fixed_provider_model",
        "wall_regression_within_5pct", "token_regression_within_10pct",
    )
    checks["paired_benchmark_pass"] = bool(
        paired.get("schema_version", 0) >= 2
        and paired.get("pass") is True
        and paired.get("valid_run_count", 0) >= 5
        and all(paired_checks.get(key) is True for key in required)
    )
    record_checks = original_cutover_record.get("checks") or {}
    checks["historical_cutover_gate_was_ready"] = bool(
        original_cutover_record.get("production_cutover_performed") is True
        and record_checks.get("cutover_gate_ready") is True
        and record_checks.get("paired_benchmark_pass") is True
        and record_checks.get("paired_authority_zero_regression") is True
    )
    checks["historical_production_smoke_pass"] = bool(
        record_checks.get("production_smoke_pass") is True
        and record_checks.get("receipt_committed") is True
        and record_checks.get("legacy_fallback_not_used") is True
    )
    blockers = [key.upper() for key, passed in checks.items() if not passed]
    passed = not blockers
    return {
        "schema_version": 1,
        "kind": "p1_character_pre_cutover_gate",
        "immutable": True,
        "generated_at": now(),
        "status": "PASS" if passed else "BLOCKED",
        "checks": checks,
        "blockers": blockers,
        "adapter_state_at_gate": {"shadow_enabled": True, "production_enabled": False},
        "proof": {
            "method": "recomputed_from_preserved_prerequisite_evidence",
            "historical_state_source": "original_production_cutover_record",
            "original_gate_was_overwritten": True,
            "note": "The overwritten gate is not treated as PASS. Every prerequisite below is rechecked; the original cutover record is used only to establish that the cutover consumed a ready gate.",
        },
    }


def post_cutover_health(*, config: dict, record: dict, pre_gate: dict, smoke: dict,
                        record_gate_sha256: str, pre_gate_sha256: str | None = None) -> dict:
    adapters = config.get("agent_runtime", {}).get("adapters", {})
    state = adapters.get("character_finalize", {})
    checks = {
        "production_enabled": state.get("production_enabled") is True,
        "shadow_disabled_in_production": state.get("shadow_enabled") is False,
        "legacy_fallback_available": state.get("legacy_fallback_on_technical") is True,
        "cutover_record_success": record.get("production_cutover_performed") is True
        and record.get("status") == "PRODUCTION_ENABLED",
        "pre_cutover_gate_pass": pre_gate.get("kind") == "p1_character_pre_cutover_gate"
        and pre_gate.get("immutable") is True and pre_gate.get("status") == "PASS",
        "record_references_pre_cutover_gate": bool(pre_gate_sha256)
        and record_gate_sha256 == pre_gate_sha256,
        "production_smoke_pass": smoke.get("pass") is True
        and smoke.get("receipt_status") == "COMMITTED"
        and smoke.get("legacy_fallback_active") is False,
    }
    blockers = [key.upper() for key, passed in checks.items() if not passed]
    return {
        "schema_version": 1,
        "kind": "p1_character_post_cutover_health",
        "generated_at": now(),
        "status": "PASS" if not blockers else "BLOCKED",
        "checks": checks,
        "blockers": blockers,
        "adapter_state": {
            "production_enabled": state.get("production_enabled"),
            "shadow_enabled": state.get("shadow_enabled"),
            "legacy_fallback_on_technical": state.get("legacy_fallback_on_technical"),
        },
        "note": "shadow_enabled=false is the expected production state and does not invalidate the pre-cutover gate.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-pre-cutover-gate", action="store_true")
    parser.add_argument("--write-post-cutover-health", action="store_true")
    parser.add_argument("--pre-gate", type=Path, default=DEFAULT_PRE_GATE)
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    parser.add_argument("--historical-record", type=Path, default=DEFAULT_HISTORICAL_RECORD)
    parser.add_argument("--smoke", type=Path, default=ROOT / "reports/p1-character-production-cutover-smoke-20260926.json")
    args = parser.parse_args()
    if args.write_pre_cutover_gate:
        paths = {
            "p0": ROOT / "reports/p0-agent-acceptance-20260926.json",
            "p0_baseline": ROOT / "reports/p0-preimage-agent-baseline-20260926.json",
            "probe": ROOT / "reports/p1-character-shadow-probe-20260926.json",
            "shadow_smoke": ROOT / "reports/p1-character-shadow-smoke-20260926.json",
            "paired": ROOT / "reports/p1-character-paired-benchmark-20260926.json",
            "original_cutover_record": args.historical_record,
        }
        report = reconstruct_pre_cutover_gate(**{k: read_json(v) for k, v in paths.items()})
        report["source_evidence"] = {k: _source(v) for k, v in paths.items()}
        try:
            write_immutable_pre_gate(args.pre_gate, report)
        except FileExistsError as exc:
            print(str(exc), file=sys.stderr)
            return 4
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "PASS" else 3
    if args.write_post_cutover_health:
        record = read_json(args.record)
        record_gate = (record.get("evidence") or {}).get("pre_cutover_gate") or {}
        report = post_cutover_health(
            config=storyos_config.load_config(), record=record,
            pre_gate=read_json(args.pre_gate), smoke=read_json(args.smoke),
            record_gate_sha256=record_gate.get("sha256", ""),
            pre_gate_sha256=sha256_file(args.pre_gate),
        )
        report["evidence"] = {
            "pre_cutover_gate": _source(args.pre_gate),
            "production_cutover_record": _source(args.record),
            "production_smoke": _source(args.smoke),
        }
        atomic.atomic_write_json(DEFAULT_HEALTH, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "PASS" else 3
    parser.error("choose a report mode")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
