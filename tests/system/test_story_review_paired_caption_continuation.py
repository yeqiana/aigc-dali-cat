from __future__ import annotations

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
import story_review
import runtime_provenance


def _candidate(attempt=6):
    provenance = runtime_provenance.build_critic_provenance(
        "CODEX", attempt=attempt, allow_user_continuation_attempt=True
    )
    provenance.update({
        "review_scope": "LOCKED_PHOTO_TEXT_CAPTION_REVIEW",
        "review_epoch": 5, "epoch_attempt": 1,
        "previous_review_sha256": "b" * 64,
        "previous_rubric_sha256": "c" * 64,
        "current_rubric_sha256": "d" * 64,
        "subtitle_source_sha256": "e" * 64,
    })
    contract = {k: "documentary" for k in story_review.CONTRACT_FIELDS}
    contract["ending_recontextualization"] = ["land", "care", "debt"]
    return {
        "schema_version": 1, "story_os_version": "2.6.1",
        "story_sha256": "a" * 64, "storyboard_sha256": "a" * 64,
        "subtitle_source_sha256": "e" * 64, "revision_count": attempt - 1,
        "critic_provenance": provenance,
        "contract": contract,
        "blind_retell": {k: "documentary" for k in story_review.BLIND_FIELDS},
        "hard_checks": {k: True for k in story_review.HARD_CHECKS},
        "issue_codes": [], "summary": {"passed": True},
    }


def _errors(data):
    return story_review.validate_payload(
        data, story_sha="a" * 64, storyboard_sha="a" * 64, version="2.6.1"
    )


def test_paired_caption_review_has_distinct_epoch_and_sha():
    row = _candidate()
    assert _errors(row) == []
    row["subtitle_source_sha256"] = "f" * 64
    assert _errors(row)
    row["subtitle_source_sha256"] = "e" * 64
    row["critic_provenance"]["current_rubric_sha256"] = "c" * 64
    assert _errors(row)


def test_unauthorized_attempt_six_and_no_automatic_seven():
    row = _candidate()
    row["critic_provenance"]["direct_user_continuation_review"] = False
    assert _errors(row)
    assert _errors(_candidate(7))
    with pytest.raises(RuntimeError, match="explicit direct-user"):
        story_review.run_critic(Path("."), attempt=6, codex_raw="codex")


def test_authorization_one_time_and_requires_true_fifth_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(story_review, "_locked_documentary_rubric", lambda _ep: True)
    target = tmp_path / "meta/runtime/story-review-paired-caption-a6.json"
    target.parent.mkdir(parents=True)
    target.write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="already authorized"):
        story_review._authorize_paired_caption_revision(tmp_path, attempt=6)
    target.unlink()
    monkeypatch.setattr(story_review, "load_review", lambda _ep: {
        "critic_provenance": {"attempt": 5}, "summary": {"passed": True},
        "issue_codes": ["STORYBOARD_STALL"],
    })
    with pytest.raises(RuntimeError, match="failure from reviewer attempt"):
        story_review._authorize_paired_caption_revision(tmp_path, attempt=6)
