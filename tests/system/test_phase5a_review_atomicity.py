from __future__ import annotations

import hashlib
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


def test_candidate_contract_failure_happens_before_any_success_projection(tmp_path):
    candidate = tmp_path / "candidate.png"
    candidate.write_bytes(b"already-existing-test-candidate")
    candidate_sha = "0" * 64
    frame = {
        "frame": "01",
        "path": candidate,
        "path_rel": "episodes/_canary/test/candidate.png",
        "sha256": candidate_sha,
        "logical_asset_key": "_external/test/frame-01",
        "generation_key": "generation-test-a1",
    }
    data = {
        "frames": [{"frame": "01", "decision": "pass", "checks": {},
                    "issue_codes": [], "notes": "ok"}],
        "issue_codes": [],
        "summary": {"passed": True},
    }
    ledger = {"frames": {"01": {
        "status": "ORIGINAL_READY",
        "attempts": [{"candidate": {"sha256": candidate_sha}, "request": {"frame_contract": {}}}],
    }}}

    with mock.patch.object(frame_semantic_review, "episode_contract_version", return_value="test"), \
         mock.patch.object(frame_semantic_review, "directing_v3_required", return_value=False), \
         mock.patch.object(frame_semantic_review, "validate_candidate_gate_rows", return_value=[]), \
         mock.patch.object(frame_semantic_review, "prepare_review_commit", return_value={"ledger_actions": "prevalidated"}), \
         mock.patch.object(frame_semantic_review.production_ledger, "load_authority", return_value=ledger), \
         mock.patch.object(frame_semantic_review.production_ledger, "content_repair_limit", return_value=1), \
         mock.patch.object(frame_semantic_review, "review_source_bindings", return_value={"frames": {"01": {}}}), \
         mock.patch.object(frame_semantic_review.phase4_contract, "required", return_value=True), \
         mock.patch.object(frame_semantic_review.phase4_contract, "verify_recorded_provenance", return_value=[]), \
         mock.patch.object(frame_semantic_review, "_commit_final_semantic_execution_receipt") as receipt_commit, \
         mock.patch.object(frame_semantic_review.production_ledger, "cmd_review") as ledger_review, \
         mock.patch.object(frame_semantic_review.production_ledger, "cmd_promote") as promote, \
         mock.patch.object(frame_semantic_review.production_ledger, "cmd_lock") as lock, \
         mock.patch.object(frame_semantic_review.frame_review_persistence, "save") as save_review, \
         mock.patch.object(frame_semantic_review, "write_json") as write_json:
        with pytest.raises(RuntimeError, match="candidate changed before Review commit"):
            frame_semantic_review._apply_candidate_gate(
                tmp_path,
                data=data,
                reviewed=[frame],
                contexts={},
                provenance={"review_source_bindings": {"frames": {"01": {}}}},
                attempt=1,
                review_scope=frame_semantic_review.PHASE5A_SINGLE_FRAME_SCOPE,
                review_item={"id": "review-item-01"},
            )

    receipt_commit.assert_not_called()
    ledger_review.assert_not_called()
    promote.assert_not_called()
    lock.assert_not_called()
    save_review.assert_not_called()
    write_json.assert_not_called()
    assert ledger["frames"]["01"]["status"] == "ORIGINAL_READY"
    assert not (tmp_path / "media" / "approved" / "01.png").exists()



def test_approved_asset_recovers_generation_key_only_by_exact_unique_sha(tmp_path, monkeypatch):
    sha = "a" * 64
    ledger = {"frames": {"01": {
        "approved_asset": {"sha256": sha, "path": "approved/01.png"},
        "current_candidate": {"sha256": sha, "generation_key": "generation-01-a1"},
        "attempts": [{"generation_key": "generation-01-a1", "candidate": {
            "sha256": sha, "generation_key": "generation-01-a1"}}],
    }}}
    monkeypatch.setattr(frame_semantic_review.generation_attempt_authority,
                        "frame_key", lambda *_a, **_k: "asset-01")
    binding = frame_semantic_review.current_generation_binding(
        tmp_path, "01", asset=ledger["frames"]["01"]["approved_asset"], ledger=ledger)
    assert binding == {"logical_asset_key": "asset-01", "generation_key": "generation-01-a1"}


def test_approved_asset_generation_recovery_fails_closed_on_ambiguous_sha(tmp_path, monkeypatch):
    sha = "a" * 64
    ledger = {"frames": {"01": {
        "approved_asset": {"sha256": sha, "path": "approved/01.png"},
        "current_candidate": {"sha256": sha, "generation_key": "generation-01-a2"},
        "attempts": [{"generation_key": "generation-01-a1", "candidate": {
            "sha256": sha, "generation_key": "generation-01-a1"}}],
    }}}
    monkeypatch.setattr(frame_semantic_review.generation_attempt_authority,
                        "frame_key", lambda *_a, **_k: "asset-01")
    binding = frame_semantic_review.current_generation_binding(
        tmp_path, "01", asset=ledger["frames"]["01"]["approved_asset"], ledger=ledger)
    assert binding == {"logical_asset_key": "asset-01", "generation_key": None}


def test_pending_recovery_accepts_only_exact_candidate_to_approved_promotion():
    sha = "a" * 64
    expected = [{"frame": "01", "path": "media/candidates/01.png", "sha256": sha}]
    actual = [{"frame": "01", "path": "media/approved/01.png", "sha256": sha}]
    ledger = {"frames": {"01": {
        "status": "LOCKED",
        "current_candidate": {"path": "media/candidates/01.png", "sha256": sha},
        "approved_asset": {"path": "media/approved/01.png", "sha256": sha,
                           "source_sha256": sha},
    }}}
    assert frame_semantic_review._pending_assets_match_exact_promotion(expected, actual, ledger)

    wrong_source = {"frames": {"01": {**ledger["frames"]["01"],
        "approved_asset": {**ledger["frames"]["01"]["approved_asset"],
                           "source_sha256": "b" * 64}}}}
    assert not frame_semantic_review._pending_assets_match_exact_promotion(expected, actual, wrong_source)

    wrong_path = [{"frame": "01", "path": "media/approved/other.png", "sha256": sha}]
    assert not frame_semantic_review._pending_assets_match_exact_promotion(expected, wrong_path, ledger)


def test_pending_receipt_finder_reuses_unique_validated_success(tmp_path, monkeypatch):
    ep = tmp_path / "ep"
    directory = ep / "meta/provider-receipts/model-executions"
    directory.mkdir(parents=True)
    policy_sha = "p" * 64
    artifact_sha = "a" * 64
    review_item = {
        "review_key": "review-01", "attempt_index": 1,
        "prompt_package_sha256": "package-01",
    }
    frame = {
        "logical_asset_key": "asset-01", "generation_key": "generation-01-a1",
        "sha256": artifact_sha,
    }
    receipt = {
        "status": "SUCCESS", "durable_result_status": "VALIDATED",
        "model_role": "vision.final", "profile": "vision_final",
        "requested_model": "gpt-6-luna", "effective_model": "gpt-6-luna",
        "reasoning_effort": "high", "model_policy_sha256": policy_sha,
        "logical_asset_key": "asset-01", "generation_key": "generation-01-a1",
        "attempt_index": 1, "artifact_sha256": artifact_sha,
        "review_item_id": "review-01", "runner_request_id": "request-01",
    }
    path = directory / "call-01.json"
    path.write_text(__import__("json").dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(frame_semantic_review, "bound_review_policy_sha256",
                        lambda _ep: policy_sha)
    found, found_path = frame_semantic_review._find_pending_final_semantic_receipt(
        ep, review_item=review_item, frame=frame, attempt=1)
    assert found["status"] == "SUCCESS"
    assert found_path == path


def test_pending_receipt_finder_rejects_unvalidated_success(tmp_path, monkeypatch):
    ep = tmp_path / "ep"
    directory = ep / "meta/provider-receipts/model-executions"
    directory.mkdir(parents=True)
    policy_sha = "p" * 64
    receipt = {
        "status": "SUCCESS", "durable_result_status": "STRUCTURED_RESULT_MISSING",
        "model_role": "vision.final", "profile": "vision_final",
        "requested_model": "gpt-6-luna", "effective_model": "gpt-6-luna",
        "reasoning_effort": "high", "model_policy_sha256": policy_sha,
        "logical_asset_key": "asset-01", "generation_key": "generation-01-a1",
        "attempt_index": 1, "artifact_sha256": "a" * 64,
        "review_item_id": "review-01",
    }
    (directory / "call-01.json").write_text(
        __import__("json").dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(frame_semantic_review, "bound_review_policy_sha256",
                        lambda _ep: policy_sha)
    with pytest.raises(RuntimeError, match="PENDING_RECEIPT_NOT_UNIQUE"):
        frame_semantic_review._find_pending_final_semantic_receipt(
            ep,
            review_item={"review_key": "review-01", "attempt_index": 1},
            frame={"logical_asset_key": "asset-01", "generation_key": "generation-01-a1",
                   "sha256": "a" * 64},
            attempt=1,
        )

def test_review_commit_manifest_has_stable_identity_and_is_not_projection_completion(tmp_path):
    commit_id = frame_semantic_review.review_commit_id(
        "review-01", "generation-01-a1", 1, "a" * 64)
    same_id = frame_semantic_review.review_commit_id(
        "review-01", "generation-01-a1", 1, "a" * 64)
    assert commit_id == same_id

    plan = {
        "review_commit_id": commit_id,
        "review_item_id": "review-01",
        "generation_key": "generation-01-a1",
        "logical_asset_key": "_external/test/frame-01",
        "attempt_index": 1,
        "candidate_sha256": [hashlib.sha256(b"candidate bytes").hexdigest()],
        "frame_contract_sha256": "c" * 64,
        "prompt_package_sha256": "d" * 64,
        "model_policy_sha256": "e" * 64,
        "evidence_fingerprint": "a" * 64,
    }
    receipt = {"status": "SUCCESS", "result_sha256": "f" * 64}
    candidate = tmp_path / frame_semantic_review.CANDIDATE_REL
    request = frame_semantic_review.pending_request_path(tmp_path, 1)
    candidate.parent.mkdir(parents=True, exist_ok=True)
    request.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_bytes(b"candidate bytes")
    request.write_text('{"review_item_id":"review-01"}', encoding="utf-8")
    plan["frames"] = ["01"]
    assert frame_semantic_review._write_review_commit_decision(tmp_path, plan, receipt) == commit_id
    manifest = frame_semantic_review.load_review_commit(tmp_path, commit_id)
    assert manifest["status"] == "COMMIT_DECIDED"
    assert frame_semantic_review.review_commit_is_decided(manifest)
    assert manifest["projection_recovery"] == "REPLAY_FROM_BOUND_PENDING_CANDIDATE"
    assert "review_queue_terminal" not in manifest["target_projections"]
    assert manifest["separate_commit_required"] == ["review_queue_terminal"]
    assert frame_semantic_review.review_commit_replay_inputs_valid(tmp_path, manifest)
    found = frame_semantic_review.find_review_commit_for_item(tmp_path, "review-01")
    assert found["commit_id"] == commit_id
    assert found["manifest"] == manifest

    candidate.write_bytes(b"changed candidate")
    assert not frame_semantic_review.review_commit_replay_inputs_valid(tmp_path, manifest)

    applied = frame_semantic_review.mark_review_commit_projections_applied(tmp_path, commit_id)
    assert applied["status"] == "PROJECTIONS_APPLIED"
    assert frame_semantic_review.review_commit_is_decided(applied)
    applied_again = frame_semantic_review.mark_review_commit_projections_applied(tmp_path, commit_id)
    assert applied_again == applied


def test_pending_candidate_is_retained_until_projection_verification_succeeds(tmp_path):
    candidate = tmp_path / frame_semantic_review.CANDIDATE_REL
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text('{"frames":[]}', encoding="utf-8")
    current = [{"frame": "01", "path": tmp_path / "media/approved/01.png",
                "path_rel": "media/approved/01.png", "sha256": "a" * 64}]
    data = {"frames": [], "issue_codes": [], "summary": {"passed": True}}
    frozen = {"frames": {"01": {"source_binding": {}}}}
    with mock.patch.object(frame_semantic_review, "episode_contract_version", return_value="test"), \
         mock.patch.object(frame_semantic_review, "directing_v3_required", return_value=False), \
         mock.patch.object(frame_semantic_review, "context_hashes", return_value={}), \
         mock.patch.object(frame_semantic_review, "review_source_bindings", return_value=frozen), \
         mock.patch.object(frame_semantic_review, "phase3_context_hashes", return_value={}), \
         mock.patch.object(frame_semantic_review, "frame_evidence_fingerprint", return_value="e" * 64), \
         mock.patch.object(frame_semantic_review, "validate_candidate_rows", return_value=[]), \
         mock.patch.object(frame_semantic_review.frame_review_persistence, "save"), \
         mock.patch.object(frame_semantic_review, "write_json"), \
         mock.patch.object(frame_semantic_review, "_rebind_incremental_captions"), \
         mock.patch.object(frame_semantic_review, "verify_scoped_review", return_value=["receipt mismatch"]):
        result = frame_semantic_review._persist_candidate(
            tmp_path, data=data, current=current, contexts={}, phashes=[], provenance={},
            frozen_sources=frozen, verification_scope=frame_semantic_review.PHASE5A_SINGLE_FRAME_SCOPE,
            review_item={"review_key": "review-01", "attempt_index": 1})

    assert result == 2
    assert candidate.is_file(), "recovery input must survive failed projection verification"


def test_reconcile_decided_commit_replays_candidate_once_then_is_idempotent(tmp_path):
    commit_id = frame_semantic_review.review_commit_id(
        "review-01", "generation-01-a1", 1, "a" * 64)
    candidate = tmp_path / frame_semantic_review.CANDIDATE_REL
    request = frame_semantic_review.pending_request_path(tmp_path, 1)
    candidate.parent.mkdir(parents=True, exist_ok=True)
    request.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_bytes(b"candidate bytes")
    request.write_text('{"review_item_id":"review-01"}', encoding="utf-8")
    plan = {
        "review_commit_id": commit_id,
        "review_item_id": "review-01",
        "generation_key": "generation-01-a1",
        "logical_asset_key": "_external/test/frame-01",
        "attempt_index": 1,
        "attempt": 1,
        "frames": ["01"],
        "candidate_sha256": [hashlib.sha256(b"candidate bytes").hexdigest()],
        "frame_contract_sha256": "c" * 64,
        "prompt_package_sha256": "d" * 64,
        "model_policy_sha256": "e" * 64,
        "evidence_fingerprint": "a" * 64,
    }
    frame_semantic_review._write_review_commit_decision(
        tmp_path, plan, {"receipt_id": "receipt-01"})

    with mock.patch.object(frame_semantic_review, "apply_pending_candidate", return_value=0) as replay, \
         mock.patch.object(frame_semantic_review, "review_commit_projections_verified", return_value=True):
        recovered = frame_semantic_review.reconcile_review_commit(tmp_path, commit_id)
        assert recovered["status"] == "PROJECTIONS_APPLIED"
        assert recovered["replayed"] is True
        again = frame_semantic_review.reconcile_review_commit(tmp_path, commit_id)

    assert again["status"] == "PROJECTIONS_APPLIED"
    assert again["replayed"] is False
    replay.assert_called_once_with(tmp_path.resolve(), attempt=1)



def test_reconcile_missing_candidate_can_use_strict_bound_archive(tmp_path, monkeypatch):
    commit_id = frame_semantic_review.review_commit_id(
        "review-01", "generation-01-a1", 1, "a" * 64)
    manifest_path = frame_semantic_review.review_commit_manifest_path(tmp_path, commit_id)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": frame_semantic_review.REVIEW_COMMIT_SCHEMA,
        "status": "COMMIT_DECIDED",
        "review_commit_id": commit_id,
        "review_item_id": "review-01",
        "generation_key": "generation-01-a1",
        "logical_asset_key": "asset-01",
        "attempt_index": 1,
        "review_attempt": 1,
        "frame": "01",
        "candidate_sha256": "a" * 64,
        "projection_recovery": "REPLAY_FROM_BOUND_PENDING_CANDIDATE",
    }
    frame_semantic_review.write_json(manifest_path, manifest)
    monkeypatch.setattr(frame_semantic_review, "review_commit_projections_verified", lambda *_a, **_k: False)
    monkeypatch.setattr(frame_semantic_review, "_recover_review_commit_from_archive",
                        lambda *_a, **_k: {"status": "PROJECTIONS_APPLIED", "archive_replayed": True})
    marked = []
    monkeypatch.setattr(frame_semantic_review, "mark_review_commit_projections_applied",
                        lambda *_a, **_k: marked.append(True) or manifest)

    result = frame_semantic_review.reconcile_review_commit(tmp_path, commit_id)

    assert result["status"] == "PROJECTIONS_APPLIED"
    assert result["archive_replayed"] is True
    assert marked == [True]


def test_reconcile_missing_candidate_rejects_unbound_archive(tmp_path, monkeypatch):
    commit_id = frame_semantic_review.review_commit_id(
        "review-01", "generation-01-a1", 1, "a" * 64)
    manifest_path = frame_semantic_review.review_commit_manifest_path(tmp_path, commit_id)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": frame_semantic_review.REVIEW_COMMIT_SCHEMA,
        "status": "COMMIT_DECIDED",
        "review_commit_id": commit_id,
        "review_item_id": "review-01",
        "generation_key": "generation-01-a1",
        "attempt_index": 1,
        "evidence_fingerprint": "a" * 64,
        "projection_recovery": "REPLAY_FROM_BOUND_PENDING_CANDIDATE",
    }
    frame_semantic_review.write_json(manifest_path, manifest)
    monkeypatch.setattr(frame_semantic_review, "review_commit_projections_verified", lambda *_a, **_k: False)
    monkeypatch.setattr(frame_semantic_review, "_recover_review_commit_from_archive", lambda *_a, **_k: None)

    result = frame_semantic_review.reconcile_review_commit(tmp_path, commit_id)

    assert result["status"] == "COMMIT_INCOMPLETE"
    assert result["reason"] == "REPLAY_INPUTS_OR_VERIFIED_PROJECTIONS_MISSING"

def test_reconcile_without_replay_inputs_or_verified_projection_fails_closed(tmp_path):
    commit_id = frame_semantic_review.review_commit_id(
        "review-01", "generation-01-a1", 1, "a" * 64)
    manifest_path = frame_semantic_review.review_commit_manifest_path(tmp_path, commit_id)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text('{"schema":"phase5a-final-semantic-review-commit/v1",'
                             '"status":"COMMIT_DECIDED",'
                             '"review_commit_id":"' + commit_id + '",'
                             '"projection_recovery":"REPLAY_FROM_BOUND_PENDING_CANDIDATE"}',
                             encoding="utf-8")
    with mock.patch.object(frame_semantic_review, "apply_pending_candidate") as replay, \
         mock.patch.object(frame_semantic_review, "review_commit_projections_verified", return_value=False):
        result = frame_semantic_review.reconcile_review_commit(tmp_path, commit_id)
    assert result["status"] == "COMMIT_INCOMPLETE"
    replay.assert_not_called()


def _write_result_projection(ep: Path, *, request_id="request-01", returncode=0,
                             turn_completed=True, structured_result=None):
    payload = {
        "schema": "storyos.user_runner_result_projection.v1",
        "request_id": request_id,
        "returncode": returncode,
        "turn_completed": turn_completed,
        "structured_result": structured_result or {"decision": "pass"},
    }
    target = ep / "meta/runtime/model-execution-results/request-01.projection.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = (frame_semantic_review.json.dumps(
        payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    target.write_bytes(raw)
    receipt = {
        "durable_result_status": "VALIDATED",
        "result_ref": target.relative_to(ep).as_posix(),
        "result_sha256": hashlib.sha256(raw).hexdigest(),
        "result_sha256_source": "USER_RUNNER_DURABLE_RESULT_PROJECTION",
    }
    return target, receipt, payload["structured_result"]


def test_final_receipt_requires_and_preserves_valid_durable_result_projection(tmp_path):
    _target, receipt, structured = _write_result_projection(tmp_path)
    original_ref = receipt["result_ref"]
    original_sha = receipt["result_sha256"]
    original_source = receipt["result_sha256_source"]
    path = frame_semantic_review._validate_durable_result_projection(
        tmp_path, receipt, request_id="request-01", durable_result=structured)
    assert path.is_file()
    assert receipt["result_ref"] == original_ref
    assert receipt["result_sha256"] == original_sha
    assert receipt["result_sha256_source"] == original_source


@pytest.mark.parametrize("mutation,expected_error", [
    ("unvalidated", "NOT_VALIDATED"),
    ("missing_ref", "REF_MISSING"),
    ("path_escape", "PATH_INVALID"),
    ("bad_file_sha", "SHA_MISMATCH"),
    ("wrong_request", "BINDING_MISMATCH"),
    ("wrong_returncode", "BINDING_MISMATCH"),
    ("no_turn", "BINDING_MISMATCH"),
    ("wrong_result", "BINDING_MISMATCH"),
])
def test_final_receipt_rejects_invalid_durable_result_projection(tmp_path, mutation, expected_error):
    _target, receipt, structured = _write_result_projection(tmp_path)
    if mutation == "unvalidated":
        receipt["durable_result_status"] = "MISSING_OR_MISMATCHED"
    elif mutation == "missing_ref":
        receipt.pop("result_ref")
    elif mutation == "path_escape":
        receipt["result_ref"] = "../../outside.json"
    elif mutation == "bad_file_sha":
        receipt["result_sha256"] = "0" * 64
    else:
        projection_path = tmp_path / receipt["result_ref"]
        payload = frame_semantic_review.read_json(projection_path)
        if mutation == "wrong_request":
            payload["request_id"] = "different-request"
        elif mutation == "wrong_returncode":
            payload["returncode"] = 1
        elif mutation == "no_turn":
            payload["turn_completed"] = False
        elif mutation == "wrong_result":
            payload["structured_result"] = {"decision": "fail"}
        raw = (frame_semantic_review.json.dumps(
            payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        projection_path.write_bytes(raw)
        receipt["result_sha256"] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(RuntimeError, match=f"FINAL_SEMANTIC_DURABLE_PROJECTION_{expected_error}"):
        frame_semantic_review._validate_durable_result_projection(
            tmp_path, receipt, request_id="request-01", durable_result=structured)


def _review_projection_fixture(ep: Path):
    receipt = {
        "review_item_id": "review-01",
        "generation_key": "generation-01-a1",
        "logical_asset_key": "_external/test/frame-01",
        "attempt_index": 1,
        "candidate_sha256": "b" * 64,
        "model_policy_sha256": "c" * 64,
        "evidence_fingerprint": "d" * 64,
    }
    raw = frame_semantic_review.json.dumps(
        receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest = {
        "schema": frame_semantic_review.REVIEW_COMMIT_SCHEMA,
        "status": "COMMIT_DECIDED",
        "projection_recovery": "REPLAY_FROM_BOUND_PENDING_CANDIDATE",
        "frame": "01",
        "review_item_id": "review-01",
        "generation_key": "generation-01-a1",
        "logical_asset_key": "_external/test/frame-01",
        "attempt_index": 1,
        "candidate_sha256": "b" * 64,
        "model_policy_sha256": "c" * 64,
        "evidence_fingerprint": "d" * 64,
        "receipt_sha256": hashlib.sha256(raw).hexdigest(),
    }
    summary_path = ep / frame_semantic_review.SUMMARY_REL
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    frame_semantic_review.write_json(summary_path, {
        "critic_provenance": {"model_execution_receipt": receipt}})
    ledger = {"frames": {"01": {
        "status": "LOCKED",
        "approved_asset": {"sha256": "b" * 64},
    }}}
    return manifest, receipt, ledger


def test_review_commit_projection_verifier_accepts_matching_local_projections(tmp_path):
    manifest, _receipt, ledger = _review_projection_fixture(tmp_path)
    with mock.patch.object(frame_semantic_review, "load_review_commit", return_value=manifest), \
         mock.patch.object(frame_semantic_review.production_ledger, "load_authority", return_value=ledger), \
         mock.patch.object(frame_semantic_review, "frame_records", return_value=[{
             "frame": "01", "sha256": "b" * 64}]), \
         mock.patch.object(frame_semantic_review, "verify_scoped_review", return_value=[]):
        assert frame_semantic_review.review_commit_projections_verified(tmp_path, "commit-01") is True


@pytest.mark.parametrize("mutation", [
    "missing_receipt", "wrong_identity", "ledger_not_locked", "approved_sha_mismatch", "current_sha_mismatch",
])
def test_review_commit_projection_verifier_rejects_missing_or_mismatched_projection(tmp_path, mutation):
    manifest, receipt, ledger = _review_projection_fixture(tmp_path)
    current_rows = [{"frame": "01", "sha256": "b" * 64}]
    summary = frame_semantic_review.read_json(tmp_path / frame_semantic_review.SUMMARY_REL)
    if mutation == "missing_receipt":
        summary["critic_provenance"] = {}
    elif mutation == "wrong_identity":
        summary["critic_provenance"]["model_execution_receipt"]["generation_key"] = "other-generation"
        canonical = frame_semantic_review.json.dumps(
            summary["critic_provenance"]["model_execution_receipt"],
            ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        manifest["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
    elif mutation == "ledger_not_locked":
        ledger["frames"]["01"]["status"] = "PASSED_PENDING"
    elif mutation == "approved_sha_mismatch":
        ledger["frames"]["01"]["approved_asset"]["sha256"] = "f" * 64
    elif mutation == "current_sha_mismatch":
        current_rows = [{"frame": "01", "sha256": "f" * 64}]
    frame_semantic_review.write_json(tmp_path / frame_semantic_review.SUMMARY_REL, summary)
    with mock.patch.object(frame_semantic_review, "load_review_commit", return_value=manifest), \
         mock.patch.object(frame_semantic_review.production_ledger, "load_authority", return_value=ledger), \
         mock.patch.object(frame_semantic_review, "frame_records", return_value=current_rows), \
         mock.patch.object(frame_semantic_review, "verify_scoped_review", return_value=[]):
        assert frame_semantic_review.review_commit_projections_verified(tmp_path, "commit-01") is False

