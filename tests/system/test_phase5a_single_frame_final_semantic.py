from __future__ import annotations

import sys
import json
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
import review_queue


def test_reviewable_subset_ignores_pending_non_target_frames(tmp_path, monkeypatch):
    candidate = tmp_path / "01.png"
    candidate.write_bytes(b"frame-one")
    ledger = {
        "frames": {
            "01": {
                "status": "ORIGINAL_READY",
                "current_candidate": {
                    "path": str(candidate),
                    "sha256": "a" * 64,
                    "generation_key": "ga-one",
                },
            },
            "02": {"status": "PENDING"},
        }
    }
    monkeypatch.setattr(
        frame_semantic_review.production_ledger, "load_authority",
        lambda *_a, **_k: ledger,
    )
    monkeypatch.setattr(frame_semantic_review, "repo_path",
                        lambda raw, *_a, **_k: Path(raw))
    monkeypatch.setattr(frame_semantic_review, "repo_rel",
                        lambda p: str(Path(p)).replace("\\", "/"))

    rows = frame_semantic_review.reviewable_frame_records(
        tmp_path, require_files=False, only_frames=[1])
    assert [row["frame"] for row in rows] == ["01"]
    assert rows[0]["generation_key"] == "ga-one"

    with pytest.raises(ValueError, match="frame 02 has no reviewable production asset"):
        frame_semantic_review.reviewable_frame_records(
            tmp_path, require_files=False)


def test_scoped_current_candidate_match_requests_only_target_frame(monkeypatch, tmp_path):
    seen = {}

    def rows(_ep, *, require_files, only_frames=None):
        seen["only_frames"] = only_frames
        return [{
            "frame": "01",
            "logical_asset_key": "asset-1",
            "generation_key": "ga-1",
            "sha256": "b" * 64,
        }]

    monkeypatch.setattr(frame_semantic_review, "reviewable_frame_records", rows)
    item = {
        "frame": 1,
        "review_scope": review_queue.PHASE5A_SINGLE_FRAME,
        "logical_asset_key": "asset-1",
        "generation_key": "ga-1",
        "artifact_sha256": "b" * 64,
    }
    assert review_queue._current_final_candidate_matches(tmp_path, item) is True
    assert seen["only_frames"] == [1]


def test_stale_final_review_is_requeued_in_place_for_phase5a_scope(
        monkeypatch, tmp_path):
    # Import modules with import-time policy resolution before substituting the
    # scoped reviewer binding below.
    import production_recovery  # noqa: F401
    artifact = tmp_path / "candidate.png"
    artifact.write_bytes(b"candidate")
    existing = {
        "review_key": "same-key",
        "status": "stale",
        "receipt": {"status": "STALE_EVIDENCE"},
        "claim_token": "old",
        "lease_expires_at": "old",
    }
    monkeypatch.setattr(
        review_queue, "enqueue",
        lambda *_a, **_k: {"status": "ALREADY_ENQUEUED", "item": existing},
    )
    import model_policy
    import fast_frame_scout
    monkeypatch.setattr(model_policy, "resolve", lambda *_a, **_k: {
        "role": "vision.final", "model": "gpt-6-luna",
        "profile": "vision_final", "reasoning_effort": "high",
        "model_policy_sha256": "f" * 64,
    })
    monkeypatch.setattr(fast_frame_scout, "sha256_file", lambda _p: "b" * 64)
    result = review_queue.enqueue_final_semantic(
        {"review_work_items": [existing]},
        episode=tmp_path,
        source_item={"frame": 1, "generation_key": "ga-1", "attempt_index": 1},
        artifact=artifact,
        artifact_path=str(artifact),
        review_scope=review_queue.PHASE5A_SINGLE_FRAME,
    )
    assert result["status"] == "REENQUEUED_STALE"
    assert result["item"] is existing
    assert existing["status"] == "queued"
    assert existing["receipt"] is None
    assert existing["review_scope"] == review_queue.PHASE5A_SINGLE_FRAME


def test_scoped_candidate_gate_closes_only_reviewed_frame(monkeypatch):
    state = {"status": "ORIGINAL_READY"}
    reviewed = [{
        "frame": "01", "path_rel": "candidate/01.png",
        "path": Path("candidate/01.png"), "sha256": "c" * 64,
    }]
    data = {
        "frames": [{
            "frame": "01", "decision": "pass",
            "checks": {}, "issue_codes": [], "notes": "ok",
        }],
        "issue_codes": [],
        "summary": {"passed": True},
    }
    ledger = {
        "policy": {"max_content_repairs_per_frame": 1},
        "frames": {
            "01": {"status": "ORIGINAL_READY"},
            "02": {"status": "PENDING"},
        },
    }
    approved = [{
        "frame": "01", "path_rel": "approved/01.png",
        "path": Path("approved/01.png"), "sha256": "c" * 64,
    }]

    def ledger_frame(*_a, **_k):
        return {"status": state["status"]}

    def review(args):
        state["status"] = "PASSED"

    def lock(args):
        state["status"] = "LOCKED"

    frame_records = mock.Mock(return_value=approved)
    persist = mock.Mock(return_value=0)
    with mock.patch.object(frame_semantic_review, "validate_candidate_gate_rows",
                           return_value=[]), \
         mock.patch.object(frame_semantic_review, "episode_contract_version",
                           return_value="test"), \
         mock.patch.object(frame_semantic_review, "directing_v3_required",
                           return_value=False), \
         mock.patch.object(frame_semantic_review.production_ledger,
                           "load_authority", return_value=ledger), \
         mock.patch.object(frame_semantic_review.production_ledger,
                           "content_repair_limit", return_value=1), \
         mock.patch.object(frame_semantic_review, "_ledger_frame",
                           side_effect=ledger_frame), \
         mock.patch.object(frame_semantic_review.production_ledger,
                           "cmd_review", side_effect=review), \
         mock.patch.object(frame_semantic_review.production_ledger,
                           "cmd_promote"), \
         mock.patch.object(frame_semantic_review.production_ledger,
                           "cmd_lock", side_effect=lock), \
         mock.patch.object(frame_semantic_review, "write_json"), \
         mock.patch.object(frame_semantic_review, "frame_records",
                           frame_records), \
         mock.patch.object(frame_semantic_review, "phase4_binding_errors",
                           return_value=[]), \
         mock.patch.object(frame_semantic_review, "review_source_bindings",
                           return_value={}), \
         mock.patch.object(frame_semantic_review, "prepare_review_commit",
                           return_value={"review_item_id": "test-item"}), \
         mock.patch.object(frame_semantic_review, "perceptual_rows",
                           return_value=[]), \
         mock.patch.object(frame_semantic_review, "_persist_candidate", persist):
        rc = frame_semantic_review._apply_candidate_gate(
            Path("ep"), data=data, reviewed=reviewed, contexts={},
            provenance={"review_source_bindings": {}}, attempt=1,
            review_scope=frame_semantic_review.PHASE5A_SINGLE_FRAME_SCOPE,
        )

    assert rc == 0
    assert state["status"] == "LOCKED"
    frame_records.assert_called_once_with(
        Path("ep"), require_files=True, only_frames=["01"])
    assert persist.call_args.kwargs["verification_scope"] == \
        frame_semantic_review.PHASE5A_SINGLE_FRAME_SCOPE


def test_pending_scoped_review_recovers_only_bound_frames(monkeypatch, tmp_path):
    episode = tmp_path / "episode"
    meta = episode / "meta"
    meta.mkdir(parents=True)
    pending_path = meta / "frame-semantic-pending-attempt-1.json"
    candidate_path = meta / ".frame-semantic-review.candidate.json"
    log_path = meta / "frame-semantic-critic-attempt-1.jsonl"
    marker_path = meta / "phase5a-canary.json"
    asset = {
        "frame": "01",
        "path": "candidate/01.png",
        "sha256": "d" * 64,
    }
    pending_path.write_text(json.dumps({
        "schema_version": 1,
        "attempt": 1,
        "contexts": {"story_sha256": "s", "storyboard_sha256": "b",
                     "visual_contract_sha256": "v"},
        "assets": [asset],
    }), encoding="utf-8")
    candidate_path.write_text(json.dumps({"frames": [], "issue_codes": [],
                                          "summary": {"passed": True}}), encoding="utf-8")
    log_path.write_text("{}\n", encoding="utf-8")
    marker_path.write_text(json.dumps({
        "workspace_class": "TEST_ONLY",
        "promotion_class": "NON_PROMOTABLE",
        "canary_type": "PHASE5A_COLLABORATIVE_REGRESSION",
    }), encoding="utf-8")
    monkeypatch.setattr(frame_semantic_review, "ROOT", tmp_path)
    monkeypatch.setattr(frame_semantic_review, "pending_request_path",
                        lambda _ep, _attempt: pending_path)
    selected = []
    monkeypatch.setattr(
        frame_semantic_review, "reviewable_frame_records",
        lambda _ep, *, require_files, only_frames=None: (
            selected.append(only_frames) or [{
                "frame": "01", "path_rel": asset["path"],
                "path": tmp_path / asset["path"], "sha256": asset["sha256"],
            }]),
    )
    monkeypatch.setattr(frame_semantic_review, "context_hashes",
                        lambda _ep: {"story_sha256": "s", "storyboard_sha256": "b",
                                     "visual_contract_sha256": "v"})
    monkeypatch.setattr(frame_semantic_review, "reviewable_phase4_binding_errors",
                        lambda *_a, **_k: [])
    monkeypatch.setattr(
        frame_semantic_review.runtime_provenance, "build_vision_critic_provenance",
        lambda **_k: {"runtime": "CODEX_ISOLATED", "review_scope": "FULL_FRAME_SET"},
    )
    applied = mock.Mock(return_value=0)
    monkeypatch.setattr(frame_semantic_review, "_apply_candidate_gate", applied)

    assert frame_semantic_review.apply_pending_candidate(episode, attempt=1) == 0
    assert selected == [["01"]]
    assert applied.call_args.kwargs["review_scope"] == \
        frame_semantic_review.PHASE5A_SINGLE_FRAME_SCOPE
