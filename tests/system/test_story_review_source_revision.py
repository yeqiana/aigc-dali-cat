from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_provenance
import story_review


def _candidate(attempt=4):
    h = "a" * 64
    provenance = runtime_provenance.build_critic_provenance(
        "CODEX", attempt=attempt, allow_user_continuation_attempt=True
    )
    provenance.update({
        "review_scope": "LOCKED_DOCUMENTARY_SOURCE_REVISION",
        "review_epoch": 3,
        "epoch_attempt": 1,
        "previous_review_sha256": "b" * 64,
        "previous_storyboard_sha256": "c" * 64,
        "current_rubric_sha256": "d" * 64,
    })
    contract = {k: "fact" for k in story_review.CONTRACT_FIELDS}
    contract["ending_recontextualization"] = ["one", "two", "three"]
    return {
        "schema_version": 1, "story_os_version": "2.6.1",
        "story_sha256": h, "storyboard_sha256": h,
        "revision_count": attempt-1, "critic_provenance": provenance,
        "contract": contract,
        "blind_retell": {k: "fact" for k in story_review.BLIND_FIELDS},
        "hard_checks": {k: True for k in story_review.HARD_CHECKS},
        "issue_codes": [], "summary": {"passed": True},
    }


def test_exactly_fourth_review_for_actual_source_revision():
    data = _candidate()
    assert story_review.validate_payload(
        data, story_sha="a" * 64, storyboard_sha="a" * 64, version="2.6.1"
    ) == []
    data["critic_provenance"]["previous_storyboard_sha256"] = "a" * 64
    assert story_review.validate_payload(
        data, story_sha="a" * 64, storyboard_sha="a" * 64, version="2.6.1"
    )


def test_no_fake_fifth_retry():
    data = _candidate(5)
    assert story_review.validate_payload(
        data, story_sha="a" * 64, storyboard_sha="a" * 64, version="2.6.1"
    )


def test_stale_or_unapproved_attempt_four_fails():
    data = _candidate()
    data["critic_provenance"]["direct_user_continuation_review"] = False
    assert story_review.validate_payload(
        data, story_sha="a" * 64, storyboard_sha="a" * 64, version="2.6.1"
    )
    with pytest.raises(RuntimeError, match="explicit"):
        story_review.run_critic(Path("."), attempt=4, codex_raw="codex")


def test_cannot_repeat_source_revision_authority(tmp_path, monkeypatch):
    monkeypatch.setattr(story_review, "_locked_documentary_rubric", lambda _ep: True)
    p = tmp_path / "meta/runtime/story-review-source-revision-a4.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({}), encoding="utf-8")
    with pytest.raises(RuntimeError, match="already authorized"):
        story_review._authorize_source_revision(tmp_path, attempt=4)


def test_source_revision_requires_actual_failure_3(tmp_path, monkeypatch):
    monkeypatch.setattr(story_review, "_locked_documentary_rubric", lambda _ep: True)
    monkeypatch.setattr(story_review, "load_review", lambda _ep: {
        "critic_provenance": {"attempt": 3}, "summary": {"passed": True}
    })
    with pytest.raises(RuntimeError, match="previous failed attempt 3"):
        story_review._authorize_source_revision(tmp_path, attempt=4)
