from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import approval_lock  # noqa: E402
import golden_episode_regression as golden  # noqa: E402
import incremental_closure  # noqa: E402
import propagation_core_gate  # noqa: E402


def test_approval_lock_binds_story_review_authority(monkeypatch, tmp_path):
    monkeypatch.setattr(approval_lock, "review_authority_sha256", lambda _ep: "a" * 64)
    row = approval_lock.row_for_story_review_authority(tmp_path)
    assert row["kind"] == "authority"
    assert row["sha256"] == "a" * 64
    assert row["path"] == "meta/story-semantic-review.json"


def test_incremental_closure_detects_story_review_from_owner(monkeypatch, tmp_path):
    monkeypatch.setattr(
        incremental_closure.episode_state_persistence,
        "load",
        lambda _ep: {"current_state": "STORYBOARD_LOCKED"},
    )
    monkeypatch.setattr(
        incremental_closure.story_review,
        "load_review",
        lambda _ep: {"summary": {"passed": True}},
    )
    monkeypatch.setattr(
        incremental_closure,
        "command_ok",
        lambda *_args: (True, ""),
    )
    ep = ROOT / "episodes" / "_tests" / "story-review-owner-plan"
    ep.mkdir(parents=True, exist_ok=True)
    try:
        result = incremental_closure.plan(ep)
        assert result["story"] == "CLEAN"
    finally:
        import shutil
        shutil.rmtree(ep, ignore_errors=True)


def test_propagation_core_reads_story_review_owner(monkeypatch, tmp_path):
    payload = {
        "retell_sentence": "普通人做了动作，异常立刻回应。",
        "protagonist_action": "按开关",
        "abnormal_response": "灯反向亮起",
        "consequence": "门打开",
        "response_latency": "immediate",
        "visual_causality": "strong",
        "retellable_in_10s": True,
        "social_send_impulse": "strong",
        "trigger_frame": 1,
        "response_frame": 1,
        "payoff_frame": 1,
        "late_trigger_exception_reason": "single-frame fixture",
        "surface_copy_guard": {
            "structural_reference_only": True,
            "copied_surface_elements": [],
        },
    }
    monkeypatch.setattr(
        propagation_core_gate.review_record_persistence,
        "load_latest",
        lambda *_args, **_kwargs: {"propagation_core": payload},
    )
    monkeypatch.setattr(propagation_core_gate, "frame_count", lambda _ep: 1)
    assert propagation_core_gate.verify(tmp_path, force=True) == []


def test_golden_reads_episode_state_authority(monkeypatch, tmp_path):
    monkeypatch.setattr(
        golden.episode_state_persistence,
        "load",
        lambda _ep: {"current_state": "PUBLISH_READY"},
    )
    monkeypatch.setattr(golden, "metrics", lambda _ep: {})
    monkeypatch.setattr(golden, "rel", lambda _ep: "episodes/_tests/golden-owner")
    monkeypatch.setattr(
        __import__("final_candidate_snapshot"),
        "verify",
        lambda _ep: [],
    )
    # Qualification may have additional release evidence blockers, but state must
    # not be reported missing merely because episode-state.json is absent.
    result = golden.qualification(tmp_path)
    assert not any(str(x).startswith("state=UNKNOWN") for x in result.get("blockers", []))
