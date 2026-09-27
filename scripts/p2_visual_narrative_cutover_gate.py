#!/usr/bin/env python3
"""Read-only, fail-closed Visual Narrative production cutover gate."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import storyos_config

REPORT = Path("reports/p2-visual-narrative-pre-cutover-gate-20260927.json")
SOURCES = {
    "p0": Path("reports/p0-agent-acceptance-20260926.json"),
    "character_cutover": Path("reports/p1-character-production-cutover-20260926.json"),
    "character_health": Path("reports/p1-character-post-cutover-health-20260926.json"),
    "world_gate": Path("reports/p2-world-pre-cutover-gate-v2-20260927.json"),
    "world_value_probe": Path("reports/p2-world-value-probe-20260927.json"),
    "visual_smoke": Path("reports/p2-visual-narrative-shadow-smoke-retry3-20260927.json"),
    "visual_benchmark": Path("reports/p2-visual-narrative-paired-benchmark-schema-v2-20260927.json"),
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(root: Path, rel: Path) -> dict:
    path = root / rel
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _episode_state(root: Path, smoke: dict) -> str | None:
    rel = smoke.get("episode")
    if not isinstance(rel, str) or not rel:
        return None
    episode = root / rel
    path = episode / "meta/episode-state.json"
    if path.is_file():
        value = json.loads(path.read_text(encoding="utf-8"))
        return value.get("current_state") if isinstance(value, dict) else None
    # Episode state may be owned by the configured metadata store. Read it
    # through its existing persistence boundary; never infer it from reports.
    try:
        import episode_state_persistence
        value = episode_state_persistence.load(episode) or {}
        return value.get("current_state")
    except Exception:
        return None


def evaluate(root: Path = ROOT, *, generated_at: str | None = None) -> dict:
    root = Path(root).resolve()
    blockers: list[str] = []
    sources: dict[str, dict] = {}
    source_docs: dict[str, dict] = {}
    for name, rel in SOURCES.items():
        path = root / rel
        if path.is_file():
            sources[name] = {"path": rel.as_posix(), "sha256": _sha(path)}
            try:
                source_docs[name] = _json(root, rel)
            except (OSError, json.JSONDecodeError):
                source_docs[name] = {}
        else:
            blockers.append(f"MISSING_EVIDENCE:{rel.as_posix()}")
            source_docs[name] = {}

    checks: dict[str, bool] = {}
    p0 = source_docs["p0"]
    checks["p0_commit_gate"] = p0.get("kind") == "p0_agent_protocol_acceptance" and p0.get("commit_gate_ready") is True
    char_record = source_docs["character_cutover"]
    char_health = source_docs["character_health"]
    checks["character_production_health"] = (
        char_record.get("status") == "PRODUCTION_ENABLED"
        and char_record.get("production_cutover_performed") is True
        and char_health.get("status") == "PASS"
        and (char_health.get("adapter_state") or {}).get("production_enabled") is True
        and (char_health.get("adapter_state") or {}).get("shadow_enabled") is False
    )
    world_gate = source_docs["world_gate"]
    world_probe = source_docs["world_value_probe"]
    try:
        cfg = storyos_config._load(root / "config/storyos.yaml")
        config_errors = storyos_config.validate(cfg)
    except Exception:
        cfg = {}
        config_errors = ["config_load_failed"]
    checks["storyos_config_valid"] = not config_errors
    world_cfg = {
        "shadow_enabled": storyos_config.get_path(cfg, "agent_runtime.adapters.world_prepare.shadow_enabled", False) is True,
        "production_enabled": storyos_config.get_path(cfg, "agent_runtime.adapters.world_prepare.production_enabled", False) is True,
        "legacy_fallback_on_technical": storyos_config.get_path(cfg, "agent_runtime.adapters.world_prepare.legacy_fallback_on_technical", False) is True,
    }
    checks["world_no_go_state_preserved"] = (
        world_gate.get("status") == "BLOCKED"
        and "WORLD_NO_MEASURABLE_AGENT_VALUE" in (world_gate.get("blockers") or [])
        and world_probe.get("final_decision") == "WORLD_PRODUCTION_NO_GO"
        and world_cfg == {"shadow_enabled": True, "production_enabled": False, "legacy_fallback_on_technical": True}
    )
    visual_state = {
        "shadow_enabled": storyos_config.get_path(cfg, "agent_runtime.adapters.visual_narrative_prepare.shadow_enabled", False) is True,
        "production_enabled": storyos_config.get_path(cfg, "agent_runtime.adapters.visual_narrative_prepare.production_enabled", False) is True,
        "legacy_fallback_on_technical": storyos_config.get_path(cfg, "agent_runtime.adapters.visual_narrative_prepare.legacy_fallback_on_technical", False) is True,
    }
    checks["visual_shadow_enabled"] = visual_state["shadow_enabled"] is True
    checks["visual_production_disabled"] = visual_state["production_enabled"] is False
    checks["legacy_fallback_available"] = visual_state["legacy_fallback_on_technical"] is True

    smoke = source_docs["visual_smoke"]
    smoke_checks = smoke.get("checks") or {}
    checks["real_shadow_smoke_pass"] = smoke.get("status") == "PASS"
    checks["candidate_parse"] = smoke_checks.get("candidate_parse") is True
    checks["candidate_valid"] = smoke_checks.get("candidate_valid") is True
    checks["semantic_pass"] = smoke_checks.get("semantic_pass") is True
    telemetry = smoke.get("telemetry") or {}
    checks["real_model_telemetry_complete"] = telemetry.get("complete") is True and telemetry.get("real_model_execution") is True
    checks["no_failure_timeout"] = telemetry.get("failure") is False and telemetry.get("timeout") is False and telemetry.get("returncode") == 0
    checks["current_host_pointer_unchanged"] = smoke_checks.get("current_host_pointer_unchanged") is True
    checks["image_generation_not_invoked"] = smoke_checks.get("image_generation_not_invoked") is True
    checks["episode_state_storyboard_locked"] = _episode_state(root, smoke) == "STORYBOARD_LOCKED"

    benchmark = source_docs["visual_benchmark"]
    safety = benchmark.get("safety_checks") or {}
    performance = benchmark.get("performance") or {}
    value_checks = benchmark.get("value_checks") or {}
    checks["minimum_five_valid_pairs"] = int(benchmark.get("valid_pair_count") or 0) >= 5
    checks["paired_semantic_equivalence"] = benchmark.get("semantic_equivalence") is True and safety.get("all_valid_pairs_semantic_equivalent") is True
    checks["paired_authority_zero_regression"] = benchmark.get("authority_zero_regression") is True and safety.get("authority_zero_regression") is True
    checks["fixed_provider_model_reasoning"] = (
        all(isinstance(benchmark.get(key), str) and benchmark.get(key) for key in ("provider", "model", "reasoning_effort"))
        and safety.get("fixed_provider_model_reasoning") is True
    )
    wall_regression = performance.get("wall_regression_fraction")
    token_regression = performance.get("token_regression_fraction")
    checks["wall_regression_within_5pct"] = isinstance(wall_regression, (int, float)) and wall_regression <= 0.05 and safety.get("wall_regression_within_5pct") is True
    checks["token_regression_within_10pct"] = isinstance(token_regression, (int, float)) and token_regression <= 0.10 and safety.get("token_regression_within_10pct") is True
    checks["measurable_value"] = benchmark.get("measurable_value") is True
    checks["speed_value_ge_10pct"] = value_checks.get("speed_value_ge_10pct") is True
    checks["benchmark_no_failure_timeout"] = safety.get("no_failure_timeout") is True
    checks["benchmark_telemetry_complete"] = benchmark.get("telemetry_complete") is True and safety.get("telemetry_complete") is True

    for name, passed in checks.items():
        if passed is not True:
            blockers.append(name.upper())
    status = "READY" if not blockers else "BLOCKED"
    return {
        "schema_version": 1,
        "kind": "p2_visual_narrative_pre_cutover_gate",
        "generated_at": generated_at or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "immutable": True,
        "production_cutover_performed": False,
        "checks": checks,
        "blockers": blockers,
        "adapter_state_at_gate": visual_state,
        "world_adapter_state": world_cfg,
        "benchmark_medians": {
            key: performance.get(key) for key in (
                "median_legacy_wall_seconds", "median_agent_wall_seconds",
                "median_legacy_total_tokens", "median_agent_total_tokens",
                "wall_regression_fraction", "token_regression_fraction",
            )
        },
        "source_evidence": sources,
        "git_head": _git_head(root),
        "note": "Read-only fail-closed gate; never mutates config, authority, candidates, episode state, or invokes a model/image provider.",
    }


def _git_head(root: Path) -> str | None:
    import subprocess
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def write_immutable(report: dict, path: Path) -> None:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"immutable Visual pre-cutover Gate already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    # Exclusive creation prevents a concurrent Gate run from overwriting evidence.
    with path.open("xb") as stream:
        stream.write(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / REPORT)
    args = parser.parse_args()
    report = evaluate(ROOT)
    write_immutable(report, args.output)
    print(json.dumps({"status": report["status"], "blockers": report["blockers"], "path": str(args.output)}, ensure_ascii=False))
    return 0 if report["status"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
