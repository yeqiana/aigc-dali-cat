from __future__ import annotations
import sys
from pathlib import Path
SYSTEM=Path(__file__).resolve().parents[2]/"episodes"/"_system"
if str(SYSTEM) not in sys.path: sys.path.insert(0,str(SYSTEM))
import review_queue

def _row(kind, receipt=None):
    return {"review_kind":kind,"review_key":"rid","status":"running",
            "claim_token":"old","lease_expires_at":"2000-01-01T00:00:00+00:00",
            "queued_at":"2000-01-01T00:00:00+00:00","receipt":receipt}

def test_recover_interrupted_final_semantic_without_receipt_is_fail_closed():
    q={review_queue.QUEUE_KEY:[_row(review_queue.FINAL_SEMANTIC)]}
    assert review_queue.recover_claims(q)==1
    row=q[review_queue.QUEUE_KEY][0]
    assert row["status"]=="blocked"
    assert row["technical_failure_code"]=="FINAL_SEMANTIC_UNVERIFIED_INTERRUPTED_CALL"
    assert row["recovery_action"]=="VERIFY_FINAL_SEMANTIC_EXECUTION_BEFORE_RETRY"
    assert review_queue.depth(q)==0
    assert review_queue.claim(q) is None

def test_claim_does_not_duplicate_live_or_expired_semantic_model():
    q={review_queue.QUEUE_KEY:[_row(review_queue.FINAL_SEMANTIC)]}
    assert review_queue.claim(q) is None
    assert q[review_queue.QUEUE_KEY][0]["status"]=="running"

def test_other_review_work_still_requeues_after_restart():
    q={review_queue.QUEUE_KEY:[_row(review_queue.FAST_SCOUT)]}
    assert review_queue.recover_claims(q)==1
    assert q[review_queue.QUEUE_KEY][0]["status"]=="queued"
    assert review_queue.claim(q)["status"]=="running"

def test_committed_receipt_can_be_adopted_on_restart():
    q={review_queue.QUEUE_KEY:[_row(review_queue.FINAL_SEMANTIC,{"status":"SUCCESS"})]}
    assert review_queue.recover_claims(q)==1
    assert q[review_queue.QUEUE_KEY][0]["status"]=="queued"
    assert review_queue.claim(q)["status"]=="running"
def test_recover_preserves_valid_final_semantic_lease():
    row = _row(review_queue.FINAL_SEMANTIC)
    row["lease_expires_at"] = "2050-01-01T00:00:00+00:00"
    q = {review_queue.QUEUE_KEY: [row]}
    assert review_queue.recover_claims(q, at="2026-10-09T00:00:00+00:00") == 0
    assert row["status"] == "running"
    assert row["claim_token"] == "old"
    assert review_queue.claim(q, at="2026-10-09T00:00:00+00:00") is None


def test_recover_preserves_valid_fast_scout_lease():
    row = _row(review_queue.FAST_SCOUT)
    row["lease_expires_at"] = "2050-01-01T00:00:00+00:00"
    q = {review_queue.QUEUE_KEY: [row]}
    assert review_queue.recover_claims(q, at="2026-10-09T00:00:00+00:00") == 0
    assert row["status"] == "running"


def test_recover_quarantines_final_semantic_with_unknown_expiry():
    for expiry in (None, "bad-timestamp", "2050-01-01T00:00:00"):
        row = _row(review_queue.FINAL_SEMANTIC)
        row["lease_expires_at"] = expiry
        q = {review_queue.QUEUE_KEY: [row]}
        assert review_queue.recover_claims(q, at="2026-10-09T00:00:00+00:00") == 1
        assert row["status"] == "blocked"
        assert review_queue.claim(q, at="2026-10-09T00:00:00+00:00") is None
