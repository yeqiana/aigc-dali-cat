"""Show unreconciled technical Generation Attempts without dispatching images.

The scheduler's legacy blocked list is for *queued dependencies*. This tests a
separate, read-only authority projection for tech_failed rows.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path
from unittest.mock import patch

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import image_scheduler


def _item(frame=6, code="IMAGE_TOOL_NO_ARTIFACT", status="tech_failed"):
    return {"frame": frame, "status": status,
            "technical_failure_code": code}


def test_outcome_unknown_appears_as_explicit_authority_block_not_ready_work():
    q = {"items": [_item()]}
    before = copy.deepcopy(q)
    with patch.object(image_scheduler, "_technical_retry_budget",
                      return_value=(False, {"attempts_consumed": 1},
                                    "previous_generation_attempt_unverified")) as budget:
        result = image_scheduler.unresolved_generation_evidence_for_plan(
            Path("episode"), q)
    assert result == [{
        "frame": 6,
        "technical_failure_code": "IMAGE_TOOL_NO_ARTIFACT",
        "reason": "previous_generation_attempt_unverified",
        "action": "VERIFY_TECHNICAL_GENERATION_EVIDENCE",
        "retry_permitted": False,
    }]
    assert q == before
    budget.assert_called_once()


def test_multiple_unknown_frames_are_sorted_and_keep_original_error_code():
    q = {"items": [
        _item(24, "ASPECT_RATIO_MISMATCH"),
        _item(6, "IMAGE_TOOL_NO_ARTIFACT"),
    ]}
    with patch.object(image_scheduler, "_technical_retry_budget",
                      return_value=(False, {}, "previous_generation_attempt_unverified")):
        result = image_scheduler.unresolved_generation_evidence_for_plan(
            Path("episode"), q)
    assert [r["frame"] for r in result] == [6, 24]
    assert [r["technical_failure_code"] for r in result] == [
        "IMAGE_TOOL_NO_ARTIFACT", "ASPECT_RATIO_MISMATCH"
    ]
    assert all(r["retry_permitted"] is False for r in result)


def test_authority_unavailable_remains_visible_and_does_not_grant_retry():
    q = {"items": [_item()]}
    before = copy.deepcopy(q)
    with patch.object(image_scheduler, "_technical_retry_budget",
                      side_effect=RuntimeError("mysql unavailable")):
        result = image_scheduler.unresolved_generation_evidence_for_plan(
            Path("episode"), q)
    assert len(result) == 1
    assert result[0]["frame"] == 6
    assert result[0]["reason"] == "generation_attempt_authority_unavailable"
    assert result[0]["retry_permitted"] is False
    assert q == before


def test_proven_failed_after_dispatch_is_not_reported_as_unverified():
    q = {"items": [_item()]}
    with patch.object(image_scheduler, "_technical_retry_budget",
                      return_value=(True, {"remaining_attempts": 1},
                                    "shared_generation_attempt_budget_available")):
        assert image_scheduler.unresolved_generation_evidence_for_plan(
            Path("episode"), q) == []


def test_plan_matches_next_action_evidence_blocking_contract():
    # Keep both existing read-only entrypoints aligned on the same MySQL
    # Attempt authority, without promoting either to an execution gate.
    import next_action

    ep = Path("episode")
    q = {"items": [_item(24, "ASPECT_RATIO_MISMATCH"), _item(6)]}
    with patch.object(
        image_scheduler, "_technical_retry_budget",
        return_value=(False, {"attempts_consumed": 1},
                      "previous_generation_attempt_unverified")
    ):
        scheduled = image_scheduler.unresolved_generation_evidence_for_plan(ep, q)
        canonical = next_action._unsafe_technical_generation_retries(ep, q)
    assert [
        (x["frame"], x["technical_failure_code"], x["reason"])
        for x in scheduled
    ] == [
        (x["frame"], x["technical_failure_code"], x["reason"])
        for x in canonical
    ]
    assert all(x["retry_permitted"] is False for x in scheduled)


def test_exhausted_shared_budget_remains_a_visible_non_retry_blocker():
    q = {"items": [_item()]}
    with patch.object(
        image_scheduler, "_technical_retry_budget",
        return_value=(False, {"remaining_attempts": 0},
                      "shared_generation_attempt_budget_exhausted")
    ):
        blocked = image_scheduler.unresolved_generation_evidence_for_plan(
            Path("episode"), q
        )
    assert blocked[0]["reason"] == "shared_generation_attempt_budget_exhausted"
    assert blocked[0]["retry_permitted"] is False


def test_queued_generated_and_review_rows_do_not_become_attempt_blockers():
    q = {"items": [
        _item(1, status="queued"),
        _item(2, status="generated"),
        {"frame": 3, "status": "running"},
    ], "review_work_items": [
        {"frame": 4, "status": "blocked", "review_kind": "FINAL_SEMANTIC"}
    ]}
    with patch.object(image_scheduler, "_technical_retry_budget") as budget:
        assert image_scheduler.unresolved_generation_evidence_for_plan(
            Path("episode"), q) == []
    budget.assert_not_called()


def test_plan_snapshot_retains_dependency_blockers_and_progress():
    ep = Path("episode")
    q = {"items": [_item()]}
    ready = [{"frame": 1, "priority": 9, "scope": "batch"}]
    dependencies = [{"frame": 2, "depends_on": [1]}]
    progress = {"generated_frames": 2, "budget": {"available": 36}}
    with (
        patch.object(image_scheduler, "ready_items",
                     return_value=(ready, dependencies)),
        patch.object(image_scheduler.scheduler_core, "progress",
                     return_value=progress),
        patch.object(image_scheduler, "_technical_retry_budget",
                     return_value=(False, {}, "previous_generation_attempt_unverified")),
    ):
        result = image_scheduler.plan_snapshot(ep, q)
    assert result["ready"] == [{"frame": 1, "priority": 9, "scope": "batch"}]
    assert result["blocked"] == [{"frame": 2, "depends_on": [1]}]
    assert result["progress"] == progress
    assert result["requires_evidence_verification"] is True
    assert result["authority_blocked"][0]["frame"] == 6


def test_empty_ready_and_dependency_lists_still_explain_hard_stop():
    q = {"items": [_item(6), _item(24, "ASPECT_RATIO_MISMATCH")]}
    with (
        patch.object(image_scheduler, "ready_items", return_value=([], [])),
        patch.object(image_scheduler.scheduler_core, "progress",
                     return_value={"generated_frames": 2}),
        patch.object(image_scheduler, "_technical_retry_budget",
                     return_value=(False, {}, "previous_generation_attempt_unverified")),
        patch.object(image_scheduler, "retry_tech",
                     side_effect=AssertionError("must not retry")),
        patch.object(image_scheduler, "save_queue",
                     side_effect=AssertionError("must not persist")),
    ):
        result = image_scheduler.plan_snapshot(Path("episode"), q)
    assert result["ready"] == []
    assert result["blocked"] == []
    assert [x["frame"] for x in result["authority_blocked"]] == [6, 24]
    assert result["requires_evidence_verification"] is True


def test_no_unknown_attempts_means_no_authority_stop():
    q = {"items": []}
    with (
        patch.object(image_scheduler, "ready_items", return_value=([], [])),
        patch.object(image_scheduler.scheduler_core, "progress",
                     return_value={}),
        patch.object(image_scheduler, "_technical_retry_budget") as budget,
    ):
        result = image_scheduler.plan_snapshot(Path("episode"), q)
    assert result["authority_blocked"] == []
    assert result["requires_evidence_verification"] is False
    budget.assert_not_called()
