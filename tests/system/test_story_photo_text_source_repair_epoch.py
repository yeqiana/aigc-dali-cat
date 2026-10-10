"""A repaired photo-text source earns one new, SHA-bound Story Review epoch."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import story_review


def setup_episode(tmp_path, *, repair_board=True, add_subtitles=True):
    ep = tmp_path / "episode"
    (ep / "docs").mkdir(parents=True)
    (ep / "meta").mkdir()
    story = ep / "docs/story.md"
    board = ep / "docs/storyboard.md"
    story.write_text("locked story source", encoding="utf-8")
    board.write_text("original storyboard", encoding="utf-8")
    old_board_sha = story_review.sha256_file(board)
    if repair_board:
        board.write_text("genuine revised storyboard with new information", encoding="utf-8")
    (ep / "meta/release-manifest.json").write_text(
        json.dumps({"release": {"body_frame_count": 20}}), encoding="utf-8",
    )
    if add_subtitles:
        subtitles = ep / "docs/subtitles.yaml"
        subtitles.write_text(
            "voice_card:\n  tone: real everyday speech\nframes:\n"
            + "".join(f"  {i}: \"caption {i}\"\n" for i in range(1, 21))
            + "silent_frames: []\n", encoding="utf-8",
        )
    return ep, story, board, old_board_sha


def test_photo_text_repair_authorizes_only_one_changed_source(tmp_path, monkeypatch):
    ep, story, board, previous_board_sha = setup_episode(tmp_path)
    prior = {
        "summary": {"passed": False},
        "issue_codes": ["DELETE_FRAME_TEST_FAIL", "AUTHORITATIVE_SUBTITLES_MISSING"],
        "story_sha256": story_review.sha256_file(story),
        "storyboard_sha256": previous_board_sha,
        "critic_provenance": {"attempt": 2},
    }
    monkeypatch.setattr(story_review, "_locked_documentary_rubric", lambda _ep: False)
    monkeypatch.setattr(story_review, "story_paths", lambda _ep: (story, board))
    monkeypatch.setattr(story_review, "load_review", lambda _ep: prior)
    monkeypatch.setattr(story_review, "review_authority_sha256", lambda _ep: "a" * 64)
    grant = story_review._authorize_photo_text_source_repair(ep, attempt=7)
    assert grant["previous_review_sha256"] == "a" * 64
    assert grant["story_sha256"] == story_review.sha256_file(story)
    assert grant["storyboard_sha256"] != previous_board_sha
    assert grant["subtitle_source_sha256"] == story_review.sha256_file(
        ep / "docs/subtitles.yaml"
    )
    assert grant["previous_issue_codes"] == prior["issue_codes"]
    assert grant["review_scope"] == "PHOTO_TEXT_SOURCE_REPAIR_AFTER_FAIL"
    assert grant["global_review_attempt"] == 7
    marker = ep / "meta/runtime/story-review-photo-text-source-repair-a7.json"
    assert marker.is_file()
    with pytest.raises(RuntimeError, match="already authorized"):
        story_review._authorize_photo_text_source_repair(ep, attempt=7)


@pytest.mark.parametrize("board_changed,subtitles_present", [
    (False, True), (True, False),
])
def test_source_repair_rejects_unfixed_inputs(
    tmp_path, monkeypatch, board_changed, subtitles_present
):
    ep, story, board, old_board_sha = setup_episode(
        tmp_path, repair_board=board_changed, add_subtitles=subtitles_present,
    )
    prior = {
        "summary": {"passed": False},
        "issue_codes": ["DELETE_FRAME_TEST_FAIL", "AUTHORITATIVE_SUBTITLES_MISSING"],
        "story_sha256": story_review.sha256_file(story),
        "storyboard_sha256": old_board_sha,
        "critic_provenance": {"attempt": 2},
    }
    monkeypatch.setattr(story_review, "_locked_documentary_rubric", lambda _ep: False)
    monkeypatch.setattr(story_review, "story_paths", lambda _ep: (story, board))
    monkeypatch.setattr(story_review, "load_review", lambda _ep: prior)
    monkeypatch.setattr(story_review, "review_authority_sha256", lambda _ep: "a" * 64)
    with pytest.raises(RuntimeError):
        story_review._authorize_photo_text_source_repair(ep, attempt=7)
    assert not (ep / "meta/runtime/story-review-photo-text-source-repair-a7.json").exists()


def test_repair_rejects_missing_prior_failed_review(tmp_path, monkeypatch):
    ep, story, board, old_board_sha = setup_episode(tmp_path)
    monkeypatch.setattr(story_review, "_locked_documentary_rubric", lambda _ep: False)
    monkeypatch.setattr(story_review, "load_review", lambda _ep: {
        "summary": {"passed": True},
        "issue_codes": [],
        "critic_provenance": {"attempt": 2},
    })
    with pytest.raises(RuntimeError, match="real failed independent review"):
        story_review._authorize_photo_text_source_repair(ep, attempt=7)
