from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import frame_review_persistence
import frame_semantic_review
import model_policy
import review_queue


@pytest.mark.parametrize("manifest_status", ["COMMIT_DECIDED", "PROJECTIONS_APPLIED"])
def test_existing_review_commit_with_failed_adoption_never_redispatches_critic(
    tmp_path: Path, manifest_status: str,
) -> None:
    """A durable commit means the model already ran; bad projection must fail closed."""
    episode = tmp_path / "episode"
    item = {
        "review_key": "review-item-01",
        "frame": 1,
        "review_scope": review_queue.PHASE5A_SINGLE_FRAME,
        "attempt_index": 1,
        "logical_asset_key": "_external/test/frame-01",
        "generation_key": "generation-test-a1",
        "artifact_sha256": "a" * 64,
        "model_policy_sha256": "b" * 64,
        "model": "gpt-6-luna",
    }
    manifest = {"status": manifest_status}

    with patch.object(model_policy, "resolve", return_value={
            "model": "gpt-6-luna", "model_policy_sha256": "b" * 64}), \
         patch.object(review_queue, "_current_final_candidate_matches", return_value=True), \
         patch.object(frame_semantic_review, "find_review_commit_for_item",
                      return_value={"commit_id": "commit-01", "manifest": manifest}), \
         patch.object(frame_semantic_review, "review_commit_is_decided", return_value=True), \
         patch.object(frame_semantic_review, "reconcile_review_commit",
                      return_value={"status": "PROJECTIONS_APPLIED"}) as reconcile, \
         patch.object(frame_semantic_review, "load_review_commit",
                      return_value={"status": "PROJECTIONS_APPLIED"}), \
         patch.object(frame_semantic_review, "review_commit_projections_verified",
                      return_value=True), \
         patch.object(frame_semantic_review, "frame_records", return_value=[]), \
         patch.object(frame_semantic_review, "verify_scoped_review",
                      return_value=["invalid bound receipt"]), \
         patch.object(frame_review_persistence, "load", return_value=None), \
         patch.object(frame_semantic_review, "run_critic") as run_critic:
        with pytest.raises(RuntimeError, match="FINAL_SEMANTIC_REVIEW_COMMIT_INCOMPLETE"):
            review_queue._final_semantic_receipt(
                episode, item, codex=None, timeout=10)

    if manifest_status == "COMMIT_DECIDED":
        reconcile.assert_called_once_with(episode, "commit-01")
    else:
        reconcile.assert_not_called()
    run_critic.assert_not_called()
