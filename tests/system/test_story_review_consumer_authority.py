from __future__ import annotations

import copy
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
import storyos_config  # noqa: E402


POLICY_SHA = "a" * 64


def _frozen_policy():
    return {
        "schema_version": 1,
        "policy_version": "fixture-v1",
        "policy_sha256": POLICY_SHA,
        "role_aliases": {"critic.story": "semantic_critic"},
        "profiles": {"semantic_critic": {"model": "gpt-6-luna", "reasoning_effort": "high"}},
    }


def test_approval_lock_binds_story_review_authority(monkeypatch, tmp_path):
    monkeypatch.setattr(approval_lock, "review_authority_sha256", lambda _ep: "a" * 64)
    row = approval_lock.row_for_story_review_authority(tmp_path)
    assert row["kind"] == "authority"
    assert row["sha256"] == "a" * 64
    assert row["path"] == "meta/story-semantic-review.json"


def test_incremental_closure_detects_story_review_from_owner(monkeypatch, tmp_path):
    global_config_drift = copy.deepcopy(storyos_config.load_config())
    global_config_drift["models"]["profiles"]["semantic_critic"]["model"] = "global-drift-model"
    monkeypatch.setattr(
        incremental_closure.episode_state_persistence,
        "load",
        lambda _ep: {"current_state": "STORYBOARD_LOCKED"},
    )
    monkeypatch.setattr(
        incremental_closure.story_review,
        "load_review",
        lambda _ep: {
            "schema_version": 1,
            "story_os_version": "2.1.0",
            "story_sha256": "b" * 64,
            "storyboard_sha256": "c" * 64,
            "model_policy_sha256": POLICY_SHA,
            "critic_provenance": {"model_policy_sha256": POLICY_SHA},
            "issue_codes": [],
            "summary": {"passed": True},
        },
    )
    monkeypatch.setattr(
        incremental_closure.model_policy_persistence,
        "load",
        lambda _ep: _frozen_policy(),
    )
    monkeypatch.setattr(
        storyos_config,
        "load_config",
        lambda: global_config_drift,
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
        assert result["evidence_plan"]["story"]["policy_sha256"] == POLICY_SHA
    finally:
        import shutil
        shutil.rmtree(ep, ignore_errors=True)


def test_unbound_policy_cannot_be_resolved_from_global_config(monkeypatch, tmp_path):
    monkeypatch.setattr(incremental_closure.model_policy_persistence, "load", lambda _ep: None)
    monkeypatch.setattr(
        storyos_config,
        "load_config",
        lambda: (_ for _ in ()).throw(AssertionError("global config must not supply frozen policy SHA")),
    )
    assert incremental_closure._bound_policy_sha(tmp_path, "critic.story") is None


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
