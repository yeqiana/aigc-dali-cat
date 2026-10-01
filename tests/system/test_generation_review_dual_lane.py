"""Phase 2 contracts for independent generation and review work."""
from __future__ import annotations

import asyncio
from contextlib import ExitStack
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes" / "_system"))

import review_queue
import image_scheduler
import scheduler_core
from test_repair_concurrency_lane import make_episode


def source(frame: int, generation_key: str = "GK-1") -> dict:
    return {"frame": frame, "generation_key": generation_key, "attempt_index": 1}


def test_review_enqueue_is_generation_and_sha_scoped(tmp_path):
    q = {"items": []}
    policy = {"model": "gpt-6-luna", "model_policy_sha256": "a" * 64}
    first = review_queue.enqueue(q, episode=tmp_path, source_item=source(1),
                                 artifact_path="episodes/e/media/a.png",
                                 artifact_sha256="b" * 64, policy=policy)
    again = review_queue.enqueue(q, episode=tmp_path, source_item=source(1),
                                 artifact_path="episodes/e/media/a.png",
                                 artifact_sha256="b" * 64, policy=policy)
    other_attempt = review_queue.enqueue(q, episode=tmp_path,
        source_item=source(1, "GK-2"), artifact_path="episodes/e/media/b.png",
        artifact_sha256="c" * 64, policy=policy)
    assert first["status"] == "ENQUEUED"
    assert again["status"] == "ALREADY_ENQUEUED"
    assert other_attempt["status"] == "ENQUEUED"
    assert first["item"]["logical_asset_key"] == other_attempt["item"]["logical_asset_key"]
    assert first["item"]["review_key"] != other_attempt["item"]["review_key"]


def test_review_claim_is_single_and_recoverable():
    q = {"review_work_items": [{"review_key": "R1", "queued_at": review_queue.now(),
                                "status": "queued"}]}
    first = review_queue.claim(q)
    first_token = first["claim_token"]
    assert first and first["status"] == "running"
    assert review_queue.claim(q) is None
    assert review_queue.recover_claims(q) == 1
    recovered = review_queue.claim(q)
    assert recovered and recovered["claim_token"] != first_token
    assert review_queue.finish(q, "R1", first_token, status="finalized") is False
    assert review_queue.finish(q, "R1", recovered["claim_token"], status="finalized",
                              receipt={"decision": "PASS_FAST"}) is True
    assert review_queue.claim(q) is None


def test_generated_without_enqueue_is_reconciled_once(tmp_path):
    artifact = tmp_path / "candidate.png"
    artifact.write_bytes(b"synthetic pixels")
    q = {"items": [{"status": "generated", "frame": 1,
                    "generation_key": "GK-1", "attempt_index": 1,
                    "output_path": str(artifact)}]}
    policy = {"model": "gpt-6-luna", "model_policy_sha256": "a" * 64}
    with patch.object(review_queue, "telemetry") as telemetry:
        first = review_queue.reconcile_generated(
            q, episode=tmp_path, policy=policy, sha256_file=lambda path: __import__("hashlib").sha256(path.read_bytes()).hexdigest())
        second = review_queue.reconcile_generated(
            q, episode=tmp_path, policy=policy, sha256_file=lambda path: __import__("hashlib").sha256(path.read_bytes()).hexdigest())
    assert len(first) == 1
    assert second == []
    assert len(q["review_work_items"]) == 1
    telemetry.assert_called_once()


def test_saved_receipt_survives_claim_recovery_without_re_review():
    receipt = {"decision": "PASS_FAST", "generation_key": "GK-1",
               "asset_sha256": "b" * 64, "model_policy_sha256": "a" * 64}
    q = {"review_work_items": [{"review_key": "R1", "queued_at": review_queue.now(),
                                "status": "running", "claim_token": "old",
                                "receipt": receipt}]}
    assert review_queue.recover_claims(q) == 1
    row = review_queue.claim(q)
    assert row and row["receipt"] == receipt
    assert row["status"] == "running"


def test_receipt_before_queue_completion_is_adopted_without_model_call(tmp_path):
    import hashlib
    artifact = tmp_path / "frame.png"
    artifact.write_bytes(b"reviewed pixels")
    sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
    receipt = {"decision": "PASS_FAST", "generation_key": "GK-1",
               "asset_sha256": sha, "model_policy_sha256": "a" * 64}
    row = {"review_key": "R1", "episode_id": "E", "logical_asset_key": "E/frame-01",
           "generation_key": "GK-1", "frame": 1, "attempt_index": 1,
           "artifact_path": str(artifact), "artifact_sha256": sha,
           "model_policy_sha256": "a" * 64, "review_kind": "FAST_SCOUT",
           "queued_at": review_queue.now(), "status": "running", "claim_token": "old",
           "receipt": receipt}
    q = {"review_work_items": [row]}
    from contextlib import nullcontext
    with patch.object(scheduler_core, "queue_transaction", lambda _ep: nullcontext()), \
         patch.object(scheduler_core, "load_queue", lambda _ep: q), \
         patch.object(scheduler_core, "save_queue", lambda _ep, _q: None), \
         patch("production_ledger.load_authority", return_value={"frames": {"01": {
             "current_candidate": {"path": str(artifact), "sha256": sha}}}}), \
         patch("frame_scout_persistence.save") as projection, \
         patch("fast_frame_scout.evaluate_candidate", side_effect=AssertionError("must reuse receipt")), \
         patch.object(review_queue, "telemetry"):
        review_queue.recover_claims(q)
        stop = asyncio.Event(); stop.set()
        asyncio.run(review_queue.run_lane(tmp_path, changed=asyncio.Event(),
            progress=asyncio.Event(), stop=stop, codex=None, timeout=10, max_inflight=1))
    assert row["status"] == "finalized"
    assert row["receipt"]["review_outcome"] == "PASS"
    projection.assert_called_once()


def test_stale_attempt_review_is_preserved_without_overwriting_current_projection(tmp_path):
    import hashlib
    old = tmp_path / "old.png"; old.write_bytes(b"attempt one")
    current = tmp_path / "current.png"; current.write_bytes(b"attempt two")
    old_sha = hashlib.sha256(old.read_bytes()).hexdigest()
    current_sha = hashlib.sha256(current.read_bytes()).hexdigest()
    receipt = {"decision": "PASS_FAST", "generation_key": "GK-1",
               "asset_sha256": old_sha, "model_policy_sha256": "a" * 64}
    row = {"review_key": "R1", "episode_id": "E", "logical_asset_key": "E/frame-01",
           "generation_key": "GK-1", "frame": 1, "attempt_index": 1,
           "artifact_path": str(old), "artifact_sha256": old_sha,
           "model_policy_sha256": "a" * 64, "review_kind": "FAST_SCOUT",
           "queued_at": review_queue.now(), "status": "running", "claim_token": "old",
           "receipt": receipt}
    q = {"review_work_items": [row]}
    from contextlib import nullcontext
    with patch.object(scheduler_core, "queue_transaction", lambda _ep: nullcontext()), \
         patch.object(scheduler_core, "load_queue", lambda _ep: q), \
         patch.object(scheduler_core, "save_queue", lambda _ep, _q: None), \
         patch("production_ledger.load_authority", return_value={"frames": {"01": {
             "current_candidate": {"path": str(current), "sha256": current_sha}}}}), \
         patch("frame_scout_persistence.save") as projection, \
         patch("fast_frame_scout.evaluate_candidate", side_effect=AssertionError("must reuse receipt")), \
         patch.object(review_queue, "telemetry"):
        review_queue.recover_claims(q)
        stop = asyncio.Event(); stop.set()
        asyncio.run(review_queue.run_lane(tmp_path, changed=asyncio.Event(),
            progress=asyncio.Event(), stop=stop, codex=None, timeout=10, max_inflight=1))
    assert row["status"] == "stale"
    assert row["receipt"]["review_outcome"] == "STALE_EVIDENCE"
    projection.assert_not_called()


def test_backpressure_has_hysteresis():
    q = {"review_work_items": [{"status": "queued"} for _ in range(6)]}
    paused, transition = review_queue.backpressure(q, high=6, low=2)
    assert paused and transition == "PAUSED"
    q["review_work_items"] = [{"status": "queued"} for _ in range(3)]
    paused, transition = review_queue.backpressure(q, high=6, low=2)
    assert paused and transition is None
    q["review_work_items"] = [{"status": "queued"} for _ in range(2)]
    paused, transition = review_queue.backpressure(q, high=6, low=2)
    assert not paused and transition == "RESUMED"
    q["review_work_items"] = [{"status": "queued"} for _ in range(5)]
    paused, transition = review_queue.backpressure(q, high=6, low=2)
    assert not paused and transition is None


def test_slow_review_pauses_refill_then_resumes_without_canceling_active_generation():
    td, ep = make_episode([{"frame": i} for i in range(1, 9)])
    try:
        q = scheduler_core.load_queue(ep)
        for row in q["items"]:
            row.update(scope="repair", generation_key=f"TEST-{row['frame']}", attempt_index=1)
        scheduler_core.save_queue(ep, q)
        started = []
        events = []

        async def generation(_ep, row, *_args):
            started.append(row["frame"])
            await asyncio.sleep(.008)
            out = ep / f"fake-{row['frame']}.png"
            out.write_bytes(f"fake-{row['frame']}".encode())
            return {"returncode": 0, "output": str(out), "payload": {}}

        def slow_review(*_args, **_kwargs):
            time.sleep(.08)
            return {"decision": "DEFER_TO_FINAL", "issue_codes": [],
                    "scout_status": "model_complete", "model_called": True}

        cfg = {**image_scheduler._CONFIG, "production": {
            **image_scheduler._CONFIG["production"],
            "review": {"max_inflight": 2, "queue_high_watermark": 3,
                       "queue_low_watermark": 1}}}
        triage = SimpleNamespace(
            inspect_candidate=lambda *_a, **_k: {"status": "PASS", "block_commit": False,
                "issue_codes": [], "candidate_sha256": "0" * 64, "diagnostic_path": None},
            queue_summary=lambda report: {"status": report["status"], "block_commit": False,
                "failure_code": None, "issue_codes": [], "diagnostic_path": None,
                "candidate_sha256": report["candidate_sha256"]})
        with ExitStack() as stack:
            stack.enter_context(patch.object(image_scheduler, "_CONFIG", cfg))
            stack.enter_context(patch.object(image_scheduler.resource_library, "ensure_fresh", lambda *_a: None))
            stack.enter_context(patch.object(image_scheduler.runtime_router, "detect", lambda: ("CODEX", "test")))
            stack.enter_context(patch.object(image_scheduler.runtime_router, "image_execution_runtime", lambda: ("CODEX", "test")))
            stack.enter_context(patch.object(image_scheduler, "async_backend_worker", generation))
            stack.enter_context(patch.object(image_scheduler, "ledger_begin", lambda *_a: (True, "")))
            stack.enter_context(patch.object(image_scheduler, "ledger_success", lambda *_a: (True, "")))
            stack.enter_context(patch.object(
                image_scheduler, "_persist_generation_identity",
                lambda _ep, item, _result=None: {
                    "ok": True,
                    "generation_key": item.get("generation_key"),
                    "attempt_index": item.get("attempt_index") or 1,
                    "reason": "synthetic_dual_lane_fixture",
                }))
            stack.enter_context(patch.object(image_scheduler, "ledger_tech_fail", lambda *_a: None))
            stack.enter_context(patch.object(image_scheduler.raw_candidate_budget, "summary", lambda *_a, **_k: {"available": 99}))
            stack.enter_context(patch.object(image_scheduler.frame_scout, "required", lambda *_a: True))
            stack.enter_context(patch.object(image_scheduler.frame_scout, "evaluate_candidate", slow_review))
            stack.enter_context(patch.object(image_scheduler.model_policy, "resolve", lambda *_a, **_k: {
                "model": "gpt-6-luna", "model_policy_sha256": "a" * 64}))
            stack.enter_context(patch.object(image_scheduler, "local_visual_triage", triage))
            stack.enter_context(patch.object(image_scheduler.runtime_observability, "safe_record_runtime_event",
                                               lambda _ep, event, **fields: events.append((event, fields))))
            rc = image_scheduler.run_scheduler_async(ep, 3, 30, None)
        assert rc == 0
        assert len(started) == 8
        transitions = [event for event, _fields in events
                       if event in {"GENERATION_REFILL_PAUSED", "GENERATION_REFILL_RESUMED"}]
        assert len(transitions) >= 2 and len(transitions) % 2 == 0, events
        assert all(transitions[index] != transitions[index - 1]
                   for index in range(1, len(transitions)))
        assert len(transitions) <= 6, events
        pauses = [fields for event, fields in events if event == "GENERATION_REFILL_PAUSED"]
        resumes = [fields for event, fields in events if event == "GENERATION_REFILL_RESUMED"]
        assert all(row["review_queue_depth"] >= 3 for row in pauses)
        assert all(row["review_queue_depth"] <= 1 for row in resumes)
        dispatches = [fields for event, fields in events if event == "GENERATION_WORK_DISPATCHED"]
        assert len(dispatches) == 8
        assert all("review_queue_depth_at_dispatch" in row for row in dispatches)
    finally:
        td.cleanup()


def test_synthetic_dual_lane_overlaps_review_with_next_generation():
    async def pipeline(serial: bool) -> float:
        started = time.perf_counter()
        reviews = []
        review_slots = asyncio.Semaphore(2)
        async def review():
            async with review_slots:
                await asyncio.sleep(.35)  # fake review, independent worker pool
        for _ in range(4):
            await asyncio.sleep(.12)  # fake generation
            if serial:
                await asyncio.sleep(.35)  # fake review on the same worker
            else:
                reviews.append(asyncio.create_task(review()))
        if reviews:
            await asyncio.gather(*reviews)
        return time.perf_counter() - started

    serial_wall = asyncio.run(pipeline(True))
    dual_wall = asyncio.run(pipeline(False))
    assert dual_wall < serial_wall * .75
