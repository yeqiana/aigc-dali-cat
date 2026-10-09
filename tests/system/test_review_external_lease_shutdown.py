"""No duplicate Final Semantic model call from a foreign active lease."""
from __future__ import annotations

import asyncio
from contextlib import nullcontext
from pathlib import Path
import sys

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import review_queue
import scheduler_core


def test_existing_foreign_review_lease_does_not_hang_stopped_scheduler(monkeypatch, tmp_path):
    q = {review_queue.QUEUE_KEY: [{
        "review_kind": review_queue.FINAL_SEMANTIC,
        "review_key": "old-review", "status": "running",
        "claim_token": "outside-worker",
        "lease_expires_at": "2050-01-01T00:00:00+00:00",
        "queued_at": "2026-10-09T00:00:00+00:00",
        "receipt": None,
    }]}
    monkeypatch.setattr(scheduler_core, "queue_transaction", lambda _ep: nullcontext())
    monkeypatch.setattr(scheduler_core, "load_queue", lambda _ep: q)
    monkeypatch.setattr(scheduler_core, "save_queue", lambda *_a: None)
    stop = asyncio.Event()
    stop.set()

    async def run():
        await asyncio.wait_for(review_queue.run_lane(
            tmp_path,
            changed=asyncio.Event(), progress=asyncio.Event(), stop=stop,
            codex=None, timeout=5, max_inflight=1,
        ), timeout=0.7)

    asyncio.run(run())
    assert q[review_queue.QUEUE_KEY][0]["status"] == "running"
    assert q[review_queue.QUEUE_KEY][0]["claim_token"] == "outside-worker"


def test_preexisting_unverified_receipt_never_uses_fresh_runner_id():
    q = {review_queue.QUEUE_KEY: [{
        "review_kind": review_queue.FINAL_SEMANTIC,
        "review_key": "prior-review", "status": "queued",
        "queued_at": "2026-10-09T00:00:00+00:00",
        "receipt": {"status": "TECH_FAILED", "evidence": "unverified"},
        "runner_request_id": None,
    }]}
    assert review_queue.claim(q) is None
    row = q[review_queue.QUEUE_KEY][0]
    assert row["status"] == "blocked"
    assert row["runner_request_id"] is None
    assert row["technical_failure_code"] == "FINAL_SEMANTIC_UNVERIFIED_INTERRUPTED_CALL"
