#!/usr/bin/env python3
"""Read-only post-cutover health for Visual Narrative Agent production."""
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
import episode_state_persistence

GATE = Path("reports/p2-visual-narrative-pre-cutover-gate-retry1-20260927.json")
RECORD = Path("reports/p2-visual-narrative-production-cutover-retry1-20260927.json")
SMOKE = Path("reports/p2-visual-narrative-production-cutover-smoke-retry1-20260927.json")
CHARACTER_HEALTH = Path("reports/p1-character-post-cutover-health-20260926.json")
WORLD_GATE = Path("reports/p2-world-pre-cutover-gate-v2-20260927.json")
WORLD_PROBE = Path("reports/p2-world-value-probe-20260927.json")
SMOKE_EPISODE = "episodes/独立篇/01_五环外的浓雾"
OUTPUT = ROOT / "reports/p2-visual-narrative-post-cutover-health-20260927.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(root: Path, path: Path) -> dict:
    data = json.loads((root / path).read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def evaluate(root: Path = ROOT) -> dict:
    root = Path(root).resolve()
    required = {"pre_cutover_gate": GATE, "production_cutover_record": RECORD,
                "production_smoke": SMOKE, "character_health": CHARACTER_HEALTH,
                "world_gate": WORLD_GATE, "world_value_probe": WORLD_PROBE}
    docs = {}
    evidence = {}
    blockers = []
    for name, rel in required.items():
        path = root / rel
        if not path.is_file():
            blockers.append(f"MISSING_EVIDENCE:{rel.as_posix()}")
            docs[name] = {}
        else:
            docs[name] = _read(root, rel)
            evidence[name] = {"path": rel.as_posix(), "sha256": _sha(path)}
    cfg = storyos_config._load(root / "config/storyos.yaml")
    errors = storyos_config.validate(cfg)
    visual_state = {key: storyos_config.get_path(cfg, f"agent_runtime.adapters.visual_narrative_prepare.{key}", False) is True
                    for key in ("shadow_enabled", "production_enabled", "legacy_fallback_on_technical")}
    world_state = {key: storyos_config.get_path(cfg, f"agent_runtime.adapters.world_prepare.{key}", False) is True
                   for key in ("shadow_enabled", "production_enabled", "legacy_fallback_on_technical")}
    gate, record, smoke = docs["pre_cutover_gate"], docs["production_cutover_record"], docs["production_smoke"]
    gate_path = root / GATE
    smoke_path = root / SMOKE
    episode = episode_state_persistence.load(root / SMOKE_EPISODE) or {}
    checks = {
        "config_valid": not errors,
        "production_flags_healthy": visual_state == {"shadow_enabled": False, "production_enabled": True,
                                                       "legacy_fallback_on_technical": True},
        "pre_cutover_gate_immutable_ready": gate.get("kind") == "p2_visual_narrative_pre_cutover_gate" and gate.get("immutable") is True and gate.get("status") == "READY",
        "pre_cutover_gate_sha_unchanged": record.get("pre_cutover_gate_sha256") == (_sha(gate_path) if gate_path.is_file() else None),
        "cutover_record_success": record.get("status") == "PRODUCTION_ENABLED" and record.get("production_cutover_performed") is True,
        "record_references_gate": record.get("pre_cutover_gate_path") == GATE.as_posix(),
        "record_references_smoke": record.get("production_smoke_path") == SMOKE.as_posix() and record.get("production_smoke_sha256") == (_sha(smoke_path) if smoke_path.is_file() else None),
        "production_smoke_pass": smoke.get("pass") is True and smoke.get("receipt_status") == "COMMITTED",
        "canonical_receipt_committed": smoke.get("authority_commit_status") == "PASS" and smoke.get("authority_committed") is True,
        "legacy_fallback_available_and_unused": visual_state.get("legacy_fallback_on_technical") is True and smoke.get("legacy_fallback_active") is False,
        "authority_zero_regression_during_validation": smoke.get("real_episode_authority_touched") is False,
        "character_production_health_unchanged": docs["character_health"].get("status") == "PASS",
        "world_no_go_unchanged": docs["world_gate"].get("status") == "BLOCKED" and "WORLD_NO_MEASURABLE_AGENT_VALUE" in (docs["world_gate"].get("blockers") or []) and docs["world_value_probe"].get("final_decision") == "WORLD_PRODUCTION_NO_GO" and world_state == {"shadow_enabled": True, "production_enabled": False, "legacy_fallback_on_technical": True},
        "episode_state_unchanged": episode.get("current_state") == "STORYBOARD_LOCKED" and smoke.get("episode_state") == "STORYBOARD_LOCKED",
        "image_generation_not_invoked": smoke.get("image_generation_invoked") is False,
    }
    blockers.extend(name.upper() for name, passed in checks.items() if passed is not True)
    return {
        "schema_version": 1, "kind": "p2_visual_narrative_post_cutover_health",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "status": "PASS" if not blockers else "FAIL", "checks": checks, "blockers": blockers,
        "adapter_state": visual_state, "world_adapter_state": world_state,
        "episode_state": episode.get("current_state"), "image_generation_invoked": False,
        "evidence": evidence,
        "note": "shadow_enabled=false is the expected Production state; health evidence is separate from immutable pre-cutover Gate.",
    }


def write_immutable(report: dict, path: Path = OUTPUT) -> None:
    if path.exists():
        raise FileExistsError(f"post-cutover health evidence already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    report = evaluate(ROOT)
    write_immutable(report, args.output)
    print(json.dumps({"status": report["status"], "blockers": report["blockers"], "path": str(args.output)}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
