#!/usr/bin/env python3
"""Offline decision/applicability fixture smoke for Final Semantic Critic Shadow."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "episodes/_system"))
sys.path.insert(0, str(ROOT / "episodes/_system/agents"))

import final_semantic_critic_adapter as critic
import frame_semantic_review

FIXTURE = ROOT / "tests/fixtures/p3_final_semantic_critic/cases.json"
DEFAULT_OUTPUT = ROOT / "reports/p3-final-semantic-critic-shadow-fixture-20260928.json"


def run() -> dict:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    allowed_codes = frame_semantic_review.ISSUE_CODES | frame_semantic_review.GLOBAL_CLOSURE_ISSUE_CODES
    known_checks = set(frame_semantic_review.CHECKS)
    known_checks.update(frame_semantic_review.V21_PHASE3_CHECKS)
    known_checks.update(frame_semantic_review.V22_VISUAL_NARRATIVE_CHECKS)
    known_checks.update(frame_semantic_review.V221_WORLD_IDENTITY_CHECKS)
    known_checks.update(frame_semantic_review.DIRECTING_V3_CHECKS)
    known_checks.add(frame_semantic_review.ANATOMY_CHECK)
    known_checks.update(frame_semantic_review.GLOBAL_CLOSURE_CHECKS)
    results = []
    for case in fixture["cases"]:
        expected = case["reference_issue_codes"]
        if not set(expected).issubset(allowed_codes):
            raise ValueError(f"fixture {case['sample_id']} uses an unknown canonical issue code")
        scopes = case.get("applicability") or []
        excluded = case.get("not_applicable") or []
        if not set(scopes + excluded).issubset(known_checks):
            raise ValueError(f"fixture {case['sample_id']} references a non-canonical check")
        decision = {
            "decision": "ACCEPT_CANDIDATE" if case["reference_label"] == "PASS" else "REPAIR",
            "issue_codes": expected,
            "severity": "LOW" if case["reference_label"] == "PASS" else "MEDIUM",
            "repair_scope": [] if case["reference_label"] == "PASS" else ["frame-set"],
            "evidence": [f"deterministic fixture reference: {case['sample_id']}"],
        }
        critic.validate_decision(decision)
        results.append({
            "sample_id": case["sample_id"],
            "reference_label": case["reference_label"],
            "decision_schema_valid": True,
            "issue_taxonomy_valid": True,
            "applicability_contract_valid": True,
            "model_execution": False,
        })
    return {
        "schema_version": 1,
        "kind": "p3_final_semantic_critic_shadow_fixture",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
        "fixture_only": True,
        "model_execution": False,
        "canonical_review_invoked": False,
        "authority_write": False,
        "production_ledger_write": False,
        "gate_pass": False,
        "episode_transition": False,
        "image_generation_invoked": False,
        "case_count": len(results),
        "cases": results,
        "coverage": ["decision schema", "canonical issue taxonomy", "versioned applicability names", "pass/fail/repair fixture labels"],
        "limitations": ["Does not claim image semantic quality or real-model telemetry; real smoke remains required."],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run()
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("xb") as handle:
            handle.write(raw)
    except FileExistsError:
        print(f"refusing to overwrite fixture evidence: {args.output}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
