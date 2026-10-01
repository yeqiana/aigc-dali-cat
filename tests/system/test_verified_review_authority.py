from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import verified_review_authority as gate


def _fixture(*, queue_status="finalized", queue_outcome="PASS", with_receipt=True):
    receipt = {
        "receipt_schema_version": 2, "status": "SUCCESS",
        "model_role": "vision.final", "profile": "vision_final",
        "requested_model": "gpt-6-luna", "effective_model": "gpt-6-luna",
        "reasoning_effort": "high", "effective_model_source": "EXPLICIT_RUNTIME_BINDING",
        "returncode": 0, "turn_completed": True,
        "review_item_id": "review-1", "logical_asset_key": "asset-1",
        "generation_key": "generation-1", "attempt_index": 1,
        "candidate_sha256": "a" * 64, "frame_contract_sha256": "b" * 64,
        "prompt_package_sha256": "c" * 64, "model_policy_sha256": "d" * 64,
        "evidence_fingerprint": "e" * 64, "runner_request_id": "request-1",
        "result_sha256": "f" * 64, "result_ref": "meta/result.json", "created_at": "now",
    }
    frame_review = {
        "review_item_id": "review-1", "attempt_index": 1,
        "evidence_fingerprint": "e" * 64,
        "critic_provenance": {"model_execution_receipt": receipt if with_receipt else None},
    }
    q_receipt = {
        "status": "SUCCESS", "review_outcome": queue_outcome,
        "critic_receipt": receipt,
    }
    queue = {"review_work_items": [{
        "review_key": "review-1", "review_kind": "FINAL_SEMANTIC",
        "logical_asset_key": "asset-1", "generation_key": "generation-1",
        "artifact_sha256": "a" * 64, "attempt_index": 1,
        "frame_contract_sha256": "b" * 64, "prompt_package_sha256": "c" * 64,
        "status": queue_status, "receipt": q_receipt,
    }]}
    patches = [
        patch.object(gate.frame_semantic_review.phase4_contract, "required", return_value=True),
        patch.object(gate.production_ledger, "load_authority", return_value={"frames": {
            "01": {"status": "LOCKED", "approved_asset": {"sha256": "a" * 64, "path": "media/approved/01.png"}}
        }}),
        patch.object(gate.frame_semantic_review, "verify_episode", return_value=[]),
        patch.object(gate.frame_semantic_review, "current_generation_binding", return_value={
            "logical_asset_key": "asset-1", "generation_key": "generation-1"
        }),
        patch.object(gate.frame_review_persistence, "load", return_value=frame_review),
        patch.object(gate.scheduler_core, "load_queue", return_value=queue),
        patch.object(gate.frame_semantic_review, "phase3_context_hashes", return_value={"frame_contract_sha256": "b" * 64}),
        patch.object(gate.frame_semantic_review, "source_binding", return_value={"source": "bound"}),
        patch.object(gate.frame_semantic_review, "context_hashes", return_value={}),
        patch.object(gate.frame_semantic_review, "bound_review_policy_sha256", return_value="d" * 64),
        patch.object(gate.frame_semantic_review, "review_evidence_fingerprint", return_value="e" * 64),
        patch.object(gate.frame_semantic_review, "validate_final_semantic_execution_receipt", return_value=[]),
        patch("final_acceptance.visual_asset_for_frame", return_value=None),
    ]
    return receipt, patches


def _run(patches):
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8], patches[9], patches[10], patches[11], patches[12]:
        return gate.verify_episode_review_authority(Path("episode"))


def test_matching_receipt_and_terminal_queue_are_verified():
    _receipt, patches = _fixture()
    result = _run(patches)
    assert result == {"status": "VERIFIED", "errors": [], "frames": ["01"]}


def test_approved_locked_projection_without_receipt_is_blocked():
    _receipt, patches = _fixture(with_receipt=False)
    result = _run(patches)
    assert result["status"] == "BLOCKED"
    assert any("Model Execution Receipt missing" in error for error in result["errors"])


def test_nonterminal_queue_cannot_authorize_projection():
    _receipt, patches = _fixture(queue_status="running")
    result = _run(patches)
    assert result["status"] == "BLOCKED"
    assert any("terminal successful" in error for error in result["errors"])


def test_queue_findings_cannot_authorize_pass_projection():
    _receipt, patches = _fixture(queue_outcome="REPAIR_NEEDED")
    result = _run(patches)
    assert result["status"] == "BLOCKED"

