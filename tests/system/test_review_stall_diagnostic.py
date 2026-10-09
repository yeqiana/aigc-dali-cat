from __future__ import annotations
import json
import sys
from pathlib import Path
import pytest
SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path: sys.path.insert(0, str(SYSTEM))
from review_stall_diagnostic import diagnose

def test_candidate_pass_never_becomes_review_authority(tmp_path):
    meta = tmp_path / "meta"
    meta.mkdir()
    (meta / ".frame-semantic-review.candidate.json").write_text(
        json.dumps({"summary":{"passed":True}}), encoding="utf-8")
    (meta / "frame-semantic-pending-attempt-1.json").write_text("{}", encoding="utf-8")
    (meta / "frame-semantic-critic-attempt-1.jsonl").touch()
    row = diagnose(tmp_path)
    assert row["code"] == "FINAL_SEMANTIC_CANDIDATE_UNVERIFIED"
    assert row["critic_log_bytes"] == 0
    assert row["review_authority_granted"] is False
    assert row["model_dispatch_performed"] is False
    assert not (meta / "runtime").exists()

def test_pending_only_exposes_action_without_retry(tmp_path):
    meta=tmp_path / "meta"
    meta.mkdir()
    (meta / "frame-semantic-pending-attempt-1.json").write_text("{}", encoding="utf-8")
    row=diagnose(tmp_path)
    assert row["code"] == "FINAL_SEMANTIC_PENDING_NO_MODEL_RECEIPT"
    assert "VERIFY_CRITIC" in row["recovery_action"]

def test_receipt_and_commit_still_need_canonical_authority(tmp_path):
    d=tmp_path / "meta/provider-receipts/model-executions"
    d.mkdir(parents=True)
    (d / "a.json").write_text(json.dumps({"model_role":"vision.final","status":"PENDING_VALIDATION"}), encoding="utf-8")
    assert diagnose(tmp_path)["code"] == "FINAL_SEMANTIC_EXECUTION_RECEIPT_REQUIRES_REVIEW_COMMIT"
    commits=tmp_path/"meta/runtime/review-commits"
    commits.mkdir(parents=True)
    (commits/"a.json").write_text('{"status":"DECIDED"}', encoding="utf-8")
    assert diagnose(tmp_path)["code"] == "FINAL_SEMANTIC_COMMIT_REQUIRES_AUTHORITY_VERIFICATION"

@pytest.mark.parametrize("bad_attempt",[-1,0,4])
def test_attempt_bounded(tmp_path,bad_attempt):
    with pytest.raises(ValueError,match="REVIEW_ATTEMPT_OUT_OF_BOUNDS"):
        diagnose(tmp_path,bad_attempt)
