#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V2.1.1 R3.1 runtime closure regression tests."""
from __future__ import annotations
import ast
import datetime as dt
import json
import tempfile
from pathlib import Path

import critic_runtime_v211
import performance_guard_v211
import preproduction_handoff
import speculative_production
import runtime_fault_replay_v211

ROOT = Path(__file__).resolve().parents[2]


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def test_handoff_boundary_excludes_runtime_calibration():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        p = ep / "meta/story-gates.json"
        base = {
            "story": {"status": "passed", "sha": "story"},
            "visual": {
                "environment_contract": {"status": "passed"},
                "frame_directives": {"status": "passed"},
                "calibration": {"items": [{"id": "V-B", "decision": "pending"}]},
            },
        }
        write_json(p, base)
        a = preproduction_handoff.stable_story_gate_subset(ep)
        base["visual"]["calibration"]["items"][0]["decision"] = "passed"
        write_json(p, base)
        b = preproduction_handoff.stable_story_gate_subset(ep)
        assert a == b, "Visual Lock runtime calibration must not invalidate preproduction authority"


def test_legacy_handoff_requires_auditable_sidecar_not_silent_ignore():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        write_json(ep / "meta/episode-state.json", {"current_state": "STORYBOARD_LOCKED"})
        gates = {
            "story": {"status": "passed", "sha": "story"},
            "visual": {
                "environment_contract": {"status": "passed", "sha": "env"},
                "frame_directives": {"status": "passed", "sha": "frames"},
                "calibration": {"items": [{"id": "V-B", "decision": "pending"}]},
            },
        }
        old_subset = {
            "story": gates["story"],
            "visual": {
                "environment_contract": gates["visual"]["environment_contract"],
                "frame_directives": gates["visual"]["frame_directives"],
                "calibration": gates["visual"]["calibration"],
            },
        }
        old_hash = preproduction_handoff.json_sha(old_subset)
        gates["visual"]["calibration"]["items"][0]["decision"] = "candidate"
        write_json(ep / "meta/story-gates.json", gates)
        write_json(ep / "meta/preproduction-handoff.json", {
            "schema_version": 1,
            "handoff_ready": True,
            "story_rewrite_allowed": False,
            "manifest_sha256": "legacy-manifest",
            "authority_assets": [],
            "authority_subsets": [{
                "kind": "json_subset", "path": "meta/story-gates.json",
                "name": "stable_preproduction_subset", "sha256": old_hash,
            }],
        })
        preproduction_handoff.character_contract.validate = lambda *a, **k: []
        preproduction_handoff.environment_contract.verify = lambda *a, **k: []
        preproduction_handoff.frame_contract.verify_all = lambda *a, **k: []
        preproduction_handoff.directing_quality.enabled = lambda *a, **k: False
        before = preproduction_handoff.verify(ep)
        assert "HANDOFF_LEGACY_BOUNDARY_MIGRATION_REQUIRED" in before
        side = preproduction_handoff.migrate_legacy_boundary(ep)
        assert side and side["authority_assets_verified"] is True
        after = preproduction_handoff.verify(ep)
        assert "HANDOFF_LEGACY_BOUNDARY_MIGRATION_REQUIRED" not in after
        original = json.loads((ep / "meta/preproduction-handoff.json").read_text(encoding="utf-8"))
        assert "authority_boundary_version" not in original


def _write_visual_lock_run(ep: Path, run_id: str, status: str = "RUNNING"):
    p = ep / critic_runtime_v211.EP_PERF_REL
    d = {"stages": {"VISUAL_LOCK": {"runs": [{
        "run_id": run_id, "started_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
        "status": status,
    }]}}}
    write_json(p, d)


def test_critic_technical_failure_circuit_breaker_current_run_only():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        _write_visual_lock_run(ep, "vl-1")
        d1 = critic_runtime_v211.record_technical_failure(ep, issue_codes=["INPUT_IMAGES_UNAVAILABLE"], attempt=1, log="x")
        assert d1["status"] == "TECHNICAL_BLOCKED"
        d2 = critic_runtime_v211.record_technical_failure(ep, issue_codes=["INPUT_IMAGES_UNAVAILABLE"], attempt=2, log="x")
        assert d2["status"] == "CIRCUIT_OPEN"
        assert critic_runtime_v211.speculative_allowed(ep, require_current_run=True) is True

        # Start a newer Visual Lock attempt. The old technical event must not unlock speculative work.
        p = ep / critic_runtime_v211.EP_PERF_REL
        d = json.loads(p.read_text(encoding="utf-8"))
        d["stages"]["VISUAL_LOCK"]["runs"].append({
            "run_id": "vl-2", "started_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
            "status": "RUNNING",
        })
        write_json(p, d)
        assert critic_runtime_v211.speculative_allowed(ep, require_current_run=True) is False


def test_generation_dependency_is_not_narrative_escalation():
    path = ROOT / "episodes/_system/image_scheduler.py"
    text = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(text)
    node = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "directive_dependency")
    source = "\n".join(text.splitlines()[node.lineno - 1:node.end_lineno])
    assert "generation_depends_on" in source
    assert "escalation_from" not in source


def test_performance_budget_120m():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td)
        started = (dt.datetime.now(dt.timezone.utc).astimezone() - dt.timedelta(minutes=121)).isoformat(timespec="seconds")
        write_json(ep / "meta/workflow-performance.json", {
            "schema_version": 1, "active_run_id": "r1", "runs": [{
                "run_id": "r1", "runtime": "CODEX", "mode": "image_continue",
                "started_at": started, "status": "RUNNING",
                "steps": [{"step": "VISUAL_LOCK", "status": "BLOCKED", "elapsed_seconds": 3600}],
            }],
        })
        write_json(ep / "meta/episode-performance-ledger.json", {"summary": {"images": {"image_backend_seconds": 1001}}})
        result = performance_guard_v211.observe(ep, "r1", "regression")
        assert result["performance_status"] == "PERFORMANCE_BUDGET_EXCEEDED"
        assert (ep / "meta/slow-step-report.json").is_file()


def test_speculative_bound():
    assert speculative_production.MAX_SPECULATIVE_FRAMES == 6



def test_speculative_reuses_formal_visual_lock_validator():
    text = Path(speculative_production.__file__).read_text(encoding="utf-8-sig")
    tree = ast.parse(text)
    node = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "visual_lock_candidates_ready")
    source = "\n".join(text.splitlines()[node.lineno - 1:node.end_lineno])
    assert "visual_lock_v21.calibration_assets" in source


def test_runtime_fault_replay_is_executable_and_not_hardcoded():
    result = runtime_fault_replay_v211.run_fault_path()
    assert result["passed"]
    assert result["technical_failure_content_isolation"] is True
    assert result["stale_previous_attempt_allowed"] is False
    assert 0 < len(result["selected_frames"]) <= 6


def main():
    test_handoff_boundary_excludes_runtime_calibration()
    test_legacy_handoff_requires_auditable_sidecar_not_silent_ignore()
    test_critic_technical_failure_circuit_breaker_current_run_only()
    test_generation_dependency_is_not_narrative_escalation()
    test_performance_budget_120m()
    test_speculative_bound()
    test_speculative_reuses_formal_visual_lock_validator()
    test_runtime_fault_replay_is_executable_and_not_hardcoded()
    print("V2.1.1 R3.1 RUNTIME CLOSURE REGRESSION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
