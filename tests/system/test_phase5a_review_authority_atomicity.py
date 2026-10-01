from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import frame_semantic_review
import production_queue_store


POLICY_SHA = "a" * 64
CANDIDATE_SHA = "b" * 64
FRAME_CONTRACT_SHA = "c" * 64
PROMPT_PACKAGE_SHA = "d" * 64
EVIDENCE_FINGERPRINT = "e" * 64
GENERATION_KEY = "ga1-test-a1"
LOGICAL_ASSET_KEY = "_external/test/frame-01"
REVIEW_ITEM_ID = "review-item-01"


def _identity() -> dict:
    return {
        "receipt_schema_version": 2,
        "status": "SUCCESS",
        "review_item_id": REVIEW_ITEM_ID,
        "logical_asset_key": LOGICAL_ASSET_KEY,
        "generation_key": GENERATION_KEY,
        "attempt_index": 1,
        "candidate_sha256": CANDIDATE_SHA,
        "frame_contract_sha256": FRAME_CONTRACT_SHA,
        "prompt_package_sha256": PROMPT_PACKAGE_SHA,
        "model_policy_sha256": POLICY_SHA,
        "model_role": "vision.final",
        "requested_model": "gpt-6-luna",
        "effective_model": "gpt-6-luna",
        "profile": "vision_final",
        "reasoning_effort": "high",
        "effective_model_source": "EXPLICIT_RUNTIME_BINDING",
        "runner_request_id": "runner-request-01",
        "returncode": 0,
        "turn_completed": True,
        "result_sha256": "f" * 64,
        "result_ref": "meta/runtime/results/final-semantic.json",
        "evidence_fingerprint": EVIDENCE_FINGERPRINT,
        "created_at": "2026-10-01T10:00:00+08:00",
    }


def _frame() -> dict:
    return {
        "frame": "01",
        "attempt_index": 1,
        "logical_asset_key": LOGICAL_ASSET_KEY,
        "generation_key": GENERATION_KEY,
        "sha256": CANDIDATE_SHA,
        "source_binding": {
            "frame_contract_sha256": FRAME_CONTRACT_SHA,
            "prompt_package_sha256": PROMPT_PACKAGE_SHA,
        },
    }


def _receipt_and_expected() -> tuple[dict, dict]:
    receipt = _identity()
    # The validator compares the durable execution receipt against the
    # independently bound queue/candidate identity. Keep the expected object
    # free of receipt-only execution facts such as runner request id/result ref.
    expected = {
        key: receipt[key]
        for key in (
            "review_item_id", "logical_asset_key", "generation_key",
            "attempt_index", "candidate_sha256", "frame_contract_sha256",
            "prompt_package_sha256", "model_policy_sha256", "model_role",
            "requested_model", "effective_model", "reasoning_effort",
            "evidence_fingerprint",
        )
    }
    return receipt, expected


def test_final_semantic_receipt_accepts_only_complete_bound_execution():
    receipt, expected = _receipt_and_expected()

    assert frame_semantic_review.validate_final_semantic_execution_receipt(
        receipt, expected
    ) == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", "FAILED"),
        ("model_role", "image.controller"),
        ("requested_model", "gpt-5.6-luna"),
        ("effective_model", "gpt-5.6-luna"),
        ("reasoning_effort", "low"),
        ("model_policy_sha256", "0" * 64),
        ("review_item_id", "other-review-item"),
        ("logical_asset_key", "other-asset"),
        ("generation_key", "other-generation"),
        ("attempt_index", 2),
        ("candidate_sha256", "0" * 64),
        ("frame_contract_sha256", "0" * 64),
        ("prompt_package_sha256", "0" * 64),
        ("evidence_fingerprint", "0" * 64),
        ("returncode", 1),
        ("turn_completed", False),
        ("runner_request_id", ""),
        ("result_sha256", ""),
        ("result_ref", ""),
    ],
)
def test_final_semantic_receipt_rejects_missing_or_drifted_authority(field, value):
    receipt, expected = _receipt_and_expected()
    receipt[field] = value

    errors = frame_semantic_review.validate_final_semantic_execution_receipt(
        receipt, expected
    )

    assert errors, f"drifted receipt field {field!r} must fail closed"


def test_pending_final_semantic_receipt_is_adopted_only_for_exact_review_identity(tmp_path):
    directory = tmp_path / "meta/provider-receipts/model-executions"
    directory.mkdir(parents=True)
    receipt = {
        "status": "PENDING_VALIDATION",
        "model_role": "vision.final",
        "profile": "vision_final",
        "requested_model": "gpt-6-luna",
        "effective_model": "gpt-6-luna",
        "reasoning_effort": "high",
        "model_policy_sha256": POLICY_SHA,
        "logical_asset_key": LOGICAL_ASSET_KEY,
        "generation_key": GENERATION_KEY,
        "attempt_index": 1,
        "artifact_sha256": CANDIDATE_SHA,
        "review_item_id": REVIEW_ITEM_ID,
        "runner_request_id": "durable-request-01",
    }
    path = directory / "call-01.json"
    path.write_text(__import__("json").dumps(receipt), encoding="utf-8")

    with mock.patch.object(frame_semantic_review, "bound_review_policy_sha256",
                           return_value=POLICY_SHA):
        found, found_path = frame_semantic_review._find_pending_final_semantic_receipt(
            tmp_path,
            review_item={"review_key": REVIEW_ITEM_ID},
            frame=_frame(),
            attempt=1,
        )

    assert found["runner_request_id"] == "durable-request-01"
    assert found_path == path
    with pytest.raises(RuntimeError, match="NOT_UNIQUE"):
        with mock.patch.object(frame_semantic_review, "bound_review_policy_sha256",
                               return_value=POLICY_SHA):
            frame_semantic_review._find_pending_final_semantic_receipt(
                tmp_path,
                review_item={"review_key": "other-review"},
                frame=_frame(),
                attempt=1,
            )


def test_success_receipt_commit_requires_validated_provisional_receipt(tmp_path):
    path = tmp_path / "execution.json"
    stored = {"status": "PENDING_VALIDATION", "call_id": "call-01"}
    validated = {"status": "SUCCESS", "call_id": "call-01", "turn_completed": True}
    with mock.patch.object(frame_semantic_review, "_read_model_execution_receipt",
                           return_value=(stored, path)), \
         mock.patch.object(frame_semantic_review, "write_json") as write_json:
        frame_semantic_review._commit_final_semantic_execution_receipt(
            tmp_path, receipt_ref="meta/execution.json", validated_receipt=validated)

    write_json.assert_called_once_with(path, validated)

    with mock.patch.object(frame_semantic_review, "_read_model_execution_receipt",
                           return_value=({"status": "SUCCESS", "call_id": "wrong"}, path)), \
         mock.patch.object(frame_semantic_review, "write_json") as write_json:
        with pytest.raises(RuntimeError, match="MISMATCH"):
            frame_semantic_review._commit_final_semantic_execution_receipt(
                tmp_path, receipt_ref="meta/execution.json", validated_receipt=validated)

    write_json.assert_not_called()


def test_missing_final_semantic_receipt_is_rejected_before_any_commit_mutation(tmp_path):
    frame = _frame()
    provenance = {"model_execution_receipt": None}

    with mock.patch.object(frame_semantic_review, "phase3_context_hashes", return_value={
             "frame_contract_sha256": FRAME_CONTRACT_SHA,
             "prompt_package_sha256": PROMPT_PACKAGE_SHA,
         }), \
         mock.patch.object(frame_semantic_review, "bound_review_policy_sha256", return_value=POLICY_SHA), \
         mock.patch.object(frame_semantic_review, "source_binding", return_value=_frame()["source_binding"]), \
         mock.patch.object(frame_semantic_review.production_ledger, "cmd_review") as review, \
         mock.patch.object(frame_semantic_review.production_ledger, "cmd_promote") as promote, \
         mock.patch.object(frame_semantic_review.production_ledger, "cmd_lock") as lock, \
         mock.patch.object(frame_semantic_review.frame_review_persistence, "save") as save, \
         mock.patch.object(frame_semantic_review, "write_json") as write_json:
        with pytest.raises(RuntimeError):
            frame_semantic_review.prepare_review_commit(
                tmp_path,
                data={"frames": [{"frame": "01", "decision": "pass"}],
                      "issue_codes": [], "summary": {"passed": True}},
                reviewed=[frame],
                contexts={},
                provenance=provenance,
                attempt=1,
                review_scope=frame_semantic_review.PHASE5A_SINGLE_FRAME_SCOPE,
                review_item={"id": REVIEW_ITEM_ID},
            )

    review.assert_not_called()
    promote.assert_not_called()
    lock.assert_not_called()
    save.assert_not_called()
    write_json.assert_not_called()
    assert not (tmp_path / "media" / "approved" / "01.png").exists()


def test_apply_candidate_gate_stops_before_ledger_or_projection_writes_on_invalid_receipt(tmp_path):
    frame = _frame()
    data = {
        "frames": [{"frame": "01", "decision": "pass", "checks": {},
                    "issue_codes": [], "notes": "ok"}],
        "issue_codes": [],
        "summary": {"passed": True},
    }
    with mock.patch.object(frame_semantic_review, "episode_contract_version", return_value="test"), \
         mock.patch.object(frame_semantic_review, "directing_v3_required", return_value=False), \
         mock.patch.object(frame_semantic_review, "validate_candidate_gate_rows", return_value=[]), \
         mock.patch.object(frame_semantic_review, "prepare_review_commit",
                           side_effect=RuntimeError("invalid final receipt")) as prepare, \
         mock.patch.object(frame_semantic_review.production_ledger, "load_authority",
                           return_value={"frames": {"01": {"status": "ORIGINAL_READY"}}}), \
         mock.patch.object(frame_semantic_review.production_ledger, "cmd_review") as review, \
         mock.patch.object(frame_semantic_review.production_ledger, "cmd_promote") as promote, \
         mock.patch.object(frame_semantic_review.production_ledger, "cmd_lock") as lock, \
         mock.patch.object(frame_semantic_review, "_persist_candidate") as persist, \
         mock.patch.object(frame_semantic_review,
                           "_commit_final_semantic_execution_receipt") as commit_receipt:
        with pytest.raises(RuntimeError, match="invalid final receipt"):
            frame_semantic_review._apply_candidate_gate(
                tmp_path, data=data, reviewed=[frame], contexts={},
                provenance={"model_execution_receipt": None}, attempt=1,
                review_scope=frame_semantic_review.PHASE5A_SINGLE_FRAME_SCOPE,
                review_item={"id": REVIEW_ITEM_ID},
            )

    prepare.assert_called_once()
    review.assert_not_called()
    promote.assert_not_called()
    lock.assert_not_called()
    persist.assert_not_called()
    commit_receipt.assert_not_called()
    assert not (tmp_path / "media" / "approved" / "01.png").exists()


def test_valid_receipt_builds_pure_review_commit_plan(tmp_path):
    receipt, _expected = _receipt_and_expected()
    frame = _frame()
    contexts = {"story_sha256": "1" * 64}
    phase3 = {
        "frame_contract_sha256": FRAME_CONTRACT_SHA,
        "prompt_package_sha256": PROMPT_PACKAGE_SHA,
    }
    item = {
        "id": REVIEW_ITEM_ID,
        "logical_asset_key": LOGICAL_ASSET_KEY,
        "generation_key": GENERATION_KEY,
        "attempt_index": 1,
        "artifact_sha256": CANDIDATE_SHA,
        "prompt_package_sha256": PROMPT_PACKAGE_SHA,
    }
    bound_frame = {**frame, "source_binding": frame["source_binding"]}
    receipt["evidence_fingerprint"] = frame_semantic_review.review_evidence_fingerprint(
        bound_frame, contexts=contexts, phase3_contexts=phase3,
        policy_sha256=POLICY_SHA, review_item_id=REVIEW_ITEM_ID,
        attempt_index=1, frame_contract_sha256=FRAME_CONTRACT_SHA,
        prompt_package_sha256=PROMPT_PACKAGE_SHA,
    )
    provenance = {
        "model_execution_receipt": receipt,
        "frozen_source_bindings": {},
        "prompt_package_sha256": PROMPT_PACKAGE_SHA,
    }

    with mock.patch.object(frame_semantic_review.production_ledger, "cmd_review") as review, \
         mock.patch.object(frame_semantic_review.production_ledger, "cmd_promote") as promote, \
         mock.patch.object(frame_semantic_review.production_ledger, "cmd_lock") as lock, \
         mock.patch.object(frame_semantic_review.frame_review_persistence, "save") as save, \
         mock.patch.object(frame_semantic_review, "write_json") as write_json:
        with mock.patch.object(frame_semantic_review, "episode_contract_version", return_value="test"), \
             mock.patch.object(frame_semantic_review, "directing_v3_required", return_value=False), \
             mock.patch.object(frame_semantic_review, "validate_candidate_gate_rows", return_value=[]), \
             mock.patch.object(frame_semantic_review.runtime_provenance, "validate_critic_provenance", return_value=[]), \
             mock.patch.object(frame_semantic_review, "review_source_bindings", return_value={}), \
             mock.patch.object(frame_semantic_review, "source_binding", return_value=frame["source_binding"]), \
             mock.patch.object(frame_semantic_review, "phase3_context_hashes", return_value=phase3), \
             mock.patch.object(frame_semantic_review, "bound_review_policy_sha256", return_value=POLICY_SHA):
            plan = frame_semantic_review.prepare_review_commit(
            tmp_path,
            data={"frames": [{"frame": "01", "decision": "pass",
                               "checks": {key: True for key in frame_semantic_review.checks_for_version("test", False)},
                               "issue_codes": [], "notes": "ok"}],
                  "issue_codes": [], "summary": {"passed": True}},
            reviewed=[frame],
            contexts=contexts,
            provenance=provenance,
            attempt=1,
            review_scope=frame_semantic_review.PHASE5A_SINGLE_FRAME_SCOPE,
            review_item=item,
            )

    assert plan["review_item_id"] == REVIEW_ITEM_ID
    assert plan["frames"] == ["01"]
    assert plan["candidate_sha256"] == [CANDIDATE_SHA]
    assert plan["ledger_actions"] == "prevalidated"
    review.assert_not_called()
    promote.assert_not_called()
    lock.assert_not_called()
    save.assert_not_called()
    write_json.assert_not_called()
    assert not (tmp_path / "media" / "approved" / "01.png").exists()


def test_review_evidence_fingerprint_is_stable_and_binds_review_authority():
    frame = _frame()
    contexts = {"story_sha256": "1" * 64, "storyboard_sha256": "2" * 64}
    phase3_contexts = {
        "frame_contract_sha256": FRAME_CONTRACT_SHA,
        "prompt_package_sha256": PROMPT_PACKAGE_SHA,
    }

    fingerprint = frame_semantic_review.review_evidence_fingerprint(
        frame, contexts=contexts, phase3_contexts=phase3_contexts,
        policy_sha256=POLICY_SHA, review_item_id=REVIEW_ITEM_ID,
        attempt_index=1, frame_contract_sha256=FRAME_CONTRACT_SHA,
        prompt_package_sha256=PROMPT_PACKAGE_SHA,
        reviewer_role="vision.final",
    )
    again = frame_semantic_review.review_evidence_fingerprint(
        dict(frame), contexts=dict(contexts), phase3_contexts=dict(phase3_contexts),
        policy_sha256=POLICY_SHA, review_item_id=REVIEW_ITEM_ID,
        attempt_index=1, frame_contract_sha256=FRAME_CONTRACT_SHA,
        prompt_package_sha256=PROMPT_PACKAGE_SHA,
        reviewer_role="vision.final",
    )
    assert fingerprint and fingerprint == again

    mutations = [
        (dict(frame, sha256="0" * 64), contexts, phase3_contexts, POLICY_SHA, REVIEW_ITEM_ID, 1, FRAME_CONTRACT_SHA, PROMPT_PACKAGE_SHA, "vision.final"),
        (dict(frame, logical_asset_key="other-asset"), contexts, phase3_contexts, POLICY_SHA, REVIEW_ITEM_ID, 1, FRAME_CONTRACT_SHA, PROMPT_PACKAGE_SHA, "vision.final"),
        (dict(frame, generation_key="other-generation"), contexts, phase3_contexts, POLICY_SHA, REVIEW_ITEM_ID, 1, FRAME_CONTRACT_SHA, PROMPT_PACKAGE_SHA, "vision.final"),
        (frame, contexts, phase3_contexts, POLICY_SHA, REVIEW_ITEM_ID, 2, FRAME_CONTRACT_SHA, PROMPT_PACKAGE_SHA, "vision.final"),
        (frame, contexts, {**phase3_contexts, "frame_contract_sha256": "0" * 64}, POLICY_SHA, REVIEW_ITEM_ID, 1, "0" * 64, PROMPT_PACKAGE_SHA, "vision.final"),
        (frame, contexts, {**phase3_contexts, "prompt_package_sha256": "0" * 64}, POLICY_SHA, REVIEW_ITEM_ID, 1, FRAME_CONTRACT_SHA, "0" * 64, "vision.final"),
        (frame, {**contexts, "story_sha256": "0" * 64}, phase3_contexts, POLICY_SHA, REVIEW_ITEM_ID, 1, FRAME_CONTRACT_SHA, PROMPT_PACKAGE_SHA, "vision.final"),
        (frame, contexts, phase3_contexts, "0" * 64, REVIEW_ITEM_ID, 1, FRAME_CONTRACT_SHA, PROMPT_PACKAGE_SHA, "vision.final"),
        (frame, contexts, phase3_contexts, POLICY_SHA, "other-review-item", 1, FRAME_CONTRACT_SHA, PROMPT_PACKAGE_SHA, "vision.final"),
        (frame, contexts, phase3_contexts, POLICY_SHA, REVIEW_ITEM_ID, 1, FRAME_CONTRACT_SHA, PROMPT_PACKAGE_SHA, "vision.critic"),
    ]
    for (changed_frame, changed_contexts, changed_phase3, policy, item_id,
         attempt_index, contract_sha, prompt_sha, role) in mutations:
        changed = frame_semantic_review.review_evidence_fingerprint(
            changed_frame, contexts=changed_contexts, phase3_contexts=changed_phase3,
            policy_sha256=policy, review_item_id=item_id,
            attempt_index=attempt_index, frame_contract_sha256=contract_sha,
            prompt_package_sha256=prompt_sha, reviewer_role=role,
        )
        assert changed != fingerprint


def test_unreceipted_locked_projection_is_classified_unverified_idempotently(tmp_path, monkeypatch):
    locked_ledger = {
        "frames": {
            "01": {
                "status": "LOCKED",
                "logical_asset_key": LOGICAL_ASSET_KEY,
                "generation_key": GENERATION_KEY,
                "current_candidate": {"path": "media/approved/01.png", "sha256": CANDIDATE_SHA},
            },
        },
    }
    monkeypatch.setattr(frame_semantic_review.production_ledger, "load_authority",
                        lambda *_args, **_kwargs: locked_ledger)
    monkeypatch.setattr(production_queue_store, "read_path",
                        lambda _ep: tmp_path / "missing-review-queue.json")
    monkeypatch.setattr(frame_semantic_review.frame_review_persistence, "load",
                        lambda *_args, **_kwargs: None)

    first = frame_semantic_review.reconcile_review_projection(tmp_path)
    second = frame_semantic_review.reconcile_review_projection(tmp_path)

    assert first == second
    assert first["status"] == "UNVERIFIED_REVIEW_PROJECTION"
    assert first["projections"][0]["classification"] == "UNVERIFIED_REVIEW_PROJECTION"
    assert first["model_dispatch_count"] == 0
    assert first["provider_dispatch_count"] == 0
    assert locked_ledger["frames"]["01"]["status"] == "LOCKED"
    assert not (tmp_path / "media" / "approved" / "01.png").exists()


def test_bound_review_verifier_fails_closed_when_provenance_missing(tmp_path, monkeypatch):
    frame = {
        "frame": "01",
        "sha256": CANDIDATE_SHA,
        "path_rel": "media/approved/01.png",
        "path": tmp_path / "media/approved/01.png",
        "logical_asset_key": LOGICAL_ASSET_KEY,
        "generation_key": GENERATION_KEY,
    }
    monkeypatch.setattr(frame_semantic_review.phase4_contract, "required", lambda _ep: True)
    monkeypatch.setattr(frame_semantic_review.phase4_contract, "verify_approved_asset_binding", lambda *_args: [])
    monkeypatch.setattr(frame_semantic_review, "source_binding", lambda *_args: {})
    monkeypatch.setattr(frame_semantic_review, "bound_review_policy_sha256", lambda _ep: POLICY_SHA)
    errors = frame_semantic_review.validate_bound_review(
        {}, frame=frame, contexts={}, version="test", metadata_only=True,
        phase3_contexts={"frame_contract_sha256": FRAME_CONTRACT_SHA}, ep=tmp_path,
    )
    assert any("evidence_fingerprint" in error for error in errors)
