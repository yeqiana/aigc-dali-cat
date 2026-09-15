from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import frame_semantic_review as review


VERSION = "2.0.3.6"


def _checks() -> dict[str, bool]:
    return {name: True for name in review.checks_for_version(VERSION)}


def test_new_frame_review_requires_anatomy_limb_hand_integrity():
    checks = _checks()
    checks.pop(review.ANATOMY_CHECK)
    rows = [{"frame": "01", "checks": checks, "issue_codes": [], "decision": "pass"}]
    errors = review.validate_candidate_gate_rows(rows, [{"frame": "01"}], VERSION, False)
    assert any(review.ANATOMY_CHECK in error for error in errors)


def test_anatomy_failure_can_enter_repair_flow_but_cannot_pass():
    checks = _checks()
    checks[review.ANATOMY_CHECK] = False
    failed = [{
        "frame": "01",
        "checks": checks,
        "issue_codes": ["HAND_INTEGRITY_FAILURE"],
        "decision": "fail",
    }]
    assert review.validate_candidate_gate_rows(failed, [{"frame": "01"}], VERSION, False) == []

    passed = [dict(failed[0], decision="pass")]
    assert review.validate_candidate_gate_rows(passed, [{"frame": "01"}], VERSION, False)


def test_legacy_bound_review_is_not_falsely_backfilled_with_anatomy_pass():
    legacy_checks = {
        name: True
        for name in review.checks_for_version(VERSION, anatomy_required=False)
    }
    frame = {
        "frame": "01",
        "sha256": "a" * 64,
        "path_rel": "media/final/01.png",
        "path": Path("media/final/01.png"),
    }
    data = {
        "schema_version": review.SCHEMA_VERSION,
        "story_os_version": VERSION,
        "frame": "01",
        "asset_sha256": "a" * 64,
        "asset_path": "media/final/01.png",
        "critic_provenance": {
            "schema_version": 1,
            "runtime": "CODEX_ISOLATED",
            "isolated_session": True,
            "review_scope": "FULL_FRAME_SET",
            "attempt": 1,
        },
        "checks": legacy_checks,
        "issue_codes": [],
        "decision": "pass",
    }
    assert review.validate_bound_review(
        data, frame=frame, contexts={}, version=VERSION,
        metadata_only=True, ep=None,
    ) == []


def test_critic_prompt_defines_anatomy_as_a_hard_failure_dimension():
    source = (SYSTEM / "frame_semantic_review.py").read_text(encoding="utf-8")
    assert "anatomy_limb_hand_integrity" in source
    assert "Extra/missing/fused limbs" in source
    assert "HAND_INTEGRITY_FAILURE" in review.ISSUE_CODES
