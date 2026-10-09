"""Quarantine transitions must survive a disk reload even with no runnable task."""
from __future__ import annotations

import asyncio
import copy
from contextlib import nullcontext
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SYS = ROOT / "episodes" / "_system"
if str(SYS) not in sys.path:
    sys.path.insert(0, str(SYS))

import review_queue
import scheduler_core


def _persistence(monkeypatch, queue):
    durable = copy.deepcopy(queue)
    saves = []
    monkeypatch.setattr(scheduler_core, "queue_transaction", lambda _ep: nullcontext())
    monkeypatch.setattr(scheduler_core, "load_queue", lambda _ep: copy.deepcopy(durable))

    def save(_ep, q):
        durable.clear()
        durable.update(copy.deepcopy(q))
        saves.append(copy.deepcopy(q))
    monkeypatch.setattr(scheduler_core, "save_queue", save)
    return durable, saves


def test_quarantine_without_claim_is_persisted(monkeypatch, tmp_path):
    q = {review_queue.QUEUE_KEY: [{
        "review_kind": review_queue.FINAL_SEMANTIC,
        "review_key": "previously-executed", "status": "queued",
        "queued_at": "2026-10-09T00:00:00+00:00",
        "receipt": {"status": "SUCCESS"}, "runner_request_id": None,
    }]}
    durable, saves = _persistence(monkeypatch, q)
    assert review_queue._claim_next_lane_item(tmp_path, scheduler_core) is None
    assert len(saves) == 1
    assert durable[review_queue.QUEUE_KEY][0]["status"] == "blocked"
    assert durable[review_queue.QUEUE_KEY][0]["technical_failure_code"] == (
        "FINAL_SEMANTIC_UNVERIFIED_INTERRUPTED_CALL")
    # Reload/restart: the blocked work is never redispatched.
    assert review_queue._claim_next_lane_item(tmp_path, scheduler_core) is None
    assert len(saves) == 1


def test_fresh_review_id_is_persisted_with_claim(monkeypatch, tmp_path):
    q = {review_queue.QUEUE_KEY: [{
        "review_kind": review_queue.FINAL_SEMANTIC,
        "review_key": "new-review", "status": "queued",
        "queued_at": "2026-10-09T00:00:00+00:00",
        "receipt": None,
    }]}
    durable, saves = _persistence(monkeypatch, q)
    row = review_queue._claim_next_lane_item(tmp_path, scheduler_core)
    assert row["status"] == "running"
    assert len(row["runner_request_id"]) == 32
    assert len(saves) == 1
    assert durable[review_queue.QUEUE_KEY][0]["runner_request_id"] == row["runner_request_id"]


def test_stopped_lane_drains_quarantined_old_item_without_model_call(monkeypatch, tmp_path):
    q = {review_queue.QUEUE_KEY: [{
        "review_kind": review_queue.FINAL_SEMANTIC,
        "review_key": "old-review", "status": "queued",
        "queued_at": "2026-10-09T00:00:00+00:00",
        "receipt": {"status": "SUCCESS"},
    }]}
    durable, saves = _persistence(monkeypatch, q)
    stop = asyncio.Event()
    stop.set()

    async def run():
        await asyncio.wait_for(review_queue.run_lane(
            tmp_path, changed=asyncio.Event(), progress=asyncio.Event(),
            stop=stop, codex=None, timeout=5, max_inflight=1),
            timeout=1.0)

    asyncio.run(run())
    assert len(saves) == 1
    assert durable[review_queue.QUEUE_KEY][0]["status"] == "blocked"
