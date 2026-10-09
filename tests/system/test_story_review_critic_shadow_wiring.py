from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
AGENTS = SYSTEM / "agents"
if str(AGENTS) not in sys.path:
    sys.path.insert(0, str(AGENTS))

import product_review_adapter
import runtime_router
import story_review
import story_semantic_critic_adapter


def _files(tmp_path: Path):
    episode = tmp_path / "episode"
    (episode / "meta").mkdir(parents=True)
    story = tmp_path / "story.md"
    board = tmp_path / "storyboard.md"
    story.write_text("frozen story", encoding="utf-8")
    board.write_text("frozen storyboard", encoding="utf-8")
    return episode, story, board


def test_existing_story_review_auto_schedules_separate_critic_shadow_request(monkeypatch, tmp_path, capsys):
    episode, story, board = _files(tmp_path)
    canonical_prepare = Mock(return_value={"request_id": "canonical-story-review"})
    shadow_prepare = Mock(return_value={
        "request_id": "story-semantic-shadow-a2",
        "request_path": "episode/meta/runtime/reviews/story-semantic-critic-shadow-attempt-2-request.json",
    })
    monkeypatch.setattr(story_review, "story_paths", lambda _ep: (story, board))
    monkeypatch.setattr(story_review, "critic_prompt", lambda *_args: "canonical review prompt")
    monkeypatch.setattr(runtime_router, "detect", lambda: ("WORK", {}))
    monkeypatch.setattr(product_review_adapter, "prepare", canonical_prepare)
    monkeypatch.setattr(story_semantic_critic_adapter, "prepare_shadow_request", shadow_prepare)
    monkeypatch.setattr(story_semantic_critic_adapter, "frozen_applicability_context", lambda _ep: {
        "source_path": "episode/meta/shot-progression-review.json",
        "source_sha256": "a" * 64,
        "status": "LOCKED", "anomaly_applicable": False,
        "anomaly_exception_reason": "fixture ordinary-life story",
    })
    monkeypatch.setattr(story_semantic_critic_adapter, "build_decision_prompt", lambda **_kwargs: "frozen critic prompt")
    monkeypatch.setattr(story_semantic_critic_adapter, "adapter_config", lambda: {
        "shadow_enabled": True, "production_enabled": False,
    })
    monkeypatch.setattr(story_review, "_finalize_review", Mock(side_effect=AssertionError("canonical finalize must not run")))

    rc = story_review.run_critic(episode, attempt=2, codex_raw=None, timeout=5)
    output = json.loads(capsys.readouterr().out)

    assert rc == product_review_adapter.HOST_ACTION_REQUIRED_RC
    assert canonical_prepare.call_count == 1
    assert shadow_prepare.call_count == 1
    assert shadow_prepare.call_args.kwargs["attempt"] == 2
    assert shadow_prepare.call_args.kwargs["story_path"] == story
    assert shadow_prepare.call_args.kwargs["storyboard_path"] == board
    assert shadow_prepare.call_args.kwargs["applicability_context"]["anomaly_applicable"] is False
    assert shadow_prepare.call_args.kwargs["rubric_paths"][-1].name == "shot-progression-review.json"
    assert output["request_id"] == "canonical-story-review"
    assert output["critic_shadow_schedule"]["scheduled"] is True
    assert output["critic_shadow_schedule"]["request_id"] == "story-semantic-shadow-a2"
    assert output["critic_shadow_schedule"]["candidate_authority"] == "runtime_evidence_only"


def test_existing_story_review_shadow_flag_off_keeps_only_canonical_request(monkeypatch, tmp_path, capsys):
    episode, story, board = _files(tmp_path)
    canonical_prepare = Mock(return_value={"request_id": "canonical-story-review"})
    shadow_prepare = Mock()
    monkeypatch.setattr(story_review, "story_paths", lambda _ep: (story, board))
    monkeypatch.setattr(story_review, "critic_prompt", lambda *_args: "canonical review prompt")
    monkeypatch.setattr(runtime_router, "detect", lambda: ("WORK", {}))
    monkeypatch.setattr(product_review_adapter, "prepare", canonical_prepare)
    monkeypatch.setattr(story_semantic_critic_adapter, "prepare_shadow_request", shadow_prepare)
    monkeypatch.setattr(story_semantic_critic_adapter, "adapter_config", lambda: {
        "shadow_enabled": False, "production_enabled": False,
    })

    rc = story_review.run_critic(episode, attempt=1, codex_raw=None, timeout=5)
    output = json.loads(capsys.readouterr().out)

    assert rc == product_review_adapter.HOST_ACTION_REQUIRED_RC
    assert canonical_prepare.call_count == 1
    shadow_prepare.assert_not_called()
    assert output["critic_shadow_schedule"] == {"enabled": False, "scheduled": False}
