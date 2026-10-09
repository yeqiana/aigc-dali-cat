from __future__ import annotations

import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
import next_action


def test_final_semantic_blocked_produces_explicit_hard_stop_without_image_retry():
    queue = {
        "items": [{"frame": 1, "status": "generated"}],
        "review_work_items": [
            {"review_key": "fast", "review_kind": "FAST_SCOUT", "status": "finalized", "frame": 1},
            {"review_key": "semantic-one", "review_kind": "FINAL_SEMANTIC", "status": "blocked", "frame": 1},
        ],
    }
    before_image_status = queue["items"][0]["status"]
    result = next_action.blocked_final_semantic_recovery(queue)
    assert result is not None
    assert result["action"] == "VERIFY_FINAL_SEMANTIC_EXECUTION_BEFORE_RETRY"
    assert result["hard_stop"] is True
    assert result["auto_recoverable"] is False
    assert result["frames"] == [1]
    assert result["review_keys"] == ["semantic-one"]
    assert queue["items"][0]["status"] == before_image_status


def test_finished_or_running_review_does_not_create_false_blocker():
    queue = {"review_work_items": [
        {"review_key": "a", "review_kind": "FINAL_SEMANTIC", "status": "finalized", "frame": 1},
        {"review_key": "b", "review_kind": "FINAL_SEMANTIC", "status": "running", "frame": 2},
        {"review_key": "c", "review_kind": "FAST_SCOUT", "status": "blocked", "frame": 3},
    ]}
    assert next_action.blocked_final_semantic_recovery(queue) is None


def test_blocked_recovery_deduplicates_frame_and_review_key():
    queue = {"review_work_items": [
        {"review_key": "r2", "review_kind": "FINAL_SEMANTIC", "status": "blocked", "frame": 2},
        {"review_key": "r1", "review_kind": "FINAL_SEMANTIC", "status": "blocked", "frame": 1},
        {"review_key": "r1", "review_kind": "FINAL_SEMANTIC", "status": "blocked", "frame": 1},
    ]}
    result = next_action.blocked_final_semantic_recovery(queue)
    assert result["frames"] == [1, 2]
    assert result["review_keys"] == ["r1", "r2"]
def test_derive_routes_quarantined_final_review_to_explicit_verification(monkeypatch, tmp_path):
    import image_scheduler

    ep = tmp_path / "episode"
    ep.mkdir()
    queue = {"items": [{"frame": 1, "status": "generated"}],
             "review_work_items": [
                 {"review_kind": "FINAL_SEMANTIC", "status": "blocked",
                  "frame": 1, "review_key": "review-id"}]}
    monkeypatch.setattr(next_action.runtime_portability, "assert_episode_directory", lambda _ep: None)
    monkeypatch.setattr(next_action.runtime_portability, "episode_label", lambda _ep: "test-only")
    monkeypatch.setattr(next_action.runtime_router, "detect", lambda: ("WORK", {}))
    monkeypatch.setattr(next_action.runtime_router, "image_execution_runtime", lambda: ("CODEX", {}))
    monkeypatch.setattr(next_action.runtime_router, "vision_review_runtime", lambda: ("CODEX", {}))
    monkeypatch.setattr(next_action.runtime_execution, "effective_mode", lambda _ep: "COLLABORATIVE")
    monkeypatch.setattr(next_action, "state", lambda _ep: "STORYBOARD_LOCKED")
    monkeypatch.setattr(next_action.episode_lifecycle, "disposition", lambda _ep: "ACTIVE")
    monkeypatch.setattr(next_action, "pending_product_review", lambda *_a, **_k: None)
    monkeypatch.setattr(next_action, "redundant_product_review_residue", lambda *_a, **_k: [])
    monkeypatch.setattr(next_action, "host_loop", lambda _ep: {"host_loop": "IDLE"})
    monkeypatch.setattr(next_action, "product_review_lifecycle_events", lambda _ep: [])
    monkeypatch.setattr(next_action.scheduler_core, "load_queue", lambda _ep: queue)
    monkeypatch.setattr(next_action.scheduler_core, "progress", lambda *_a, **_k: {})
    monkeypatch.setattr(next_action.production_ledger, "load_authority", lambda *_a, **_k: {"frames": {}})
    monkeypatch.setattr(next_action, "_handoff_valid", lambda _ep: True)
    monkeypatch.setattr(next_action, "queue_summary", lambda _ep: {
        "raw": queue, "blocked_items": [], "queued_frames": [], "counts": {}})
    monkeypatch.setattr(next_action.visual_lock_baseline_gate, "awaiting_review", lambda *_a: False)
    monkeypatch.setattr(next_action.visual_lock_candidate_pool, "weak_pass_eligible_frames", lambda *_a: [])
    monkeypatch.setattr(next_action.visual_lock_candidate_pool, "prepareable_frames", lambda *_a: [])
    monkeypatch.setattr(next_action.visual_lock_candidate_pool, "exhausted_frames", lambda *_a: [])
    monkeypatch.setattr(image_scheduler, "ready_items", lambda *_a: ([], []))
    result = next_action.derive(ep)
    assert result["action"] == "VERIFY_FINAL_SEMANTIC_EXECUTION_BEFORE_RETRY"
    assert result["blocking"] is True
    assert result["hard_stop"] is True
    assert result["auto_recoverable"] is False
    assert result["frames"] == [1]
    assert result["review_keys"] == ["review-id"]
