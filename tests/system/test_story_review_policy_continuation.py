from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_provenance
import story_review


def _candidate(attempt: int, *, authorized: bool) -> dict:
    h = "a" * 64
    prov = runtime_provenance.build_critic_provenance(
        "CODEX", attempt=attempt, allow_user_continuation_attempt=True
    )
    if not authorized:
        prov.pop("direct_user_continuation_review", None)
    if authorized:
        prov.update({
            "review_scope": "LOCKED_DOCUMENTARY_POLICY_REVISION",
            "review_epoch": 2, "epoch_attempt": 1,
            "previous_review_sha256": "b" * 64,
            "previous_rubric_sha256": "c" * 64,
            "current_rubric_sha256": "d" * 64,
        })
    contract = {key: "fact" for key in story_review.CONTRACT_FIELDS}
    contract["ending_recontextualization"] = ["land", "debt", "care"]
    return {
        "schema_version": 1,
        "story_os_version": "2.6.1",
        "story_sha256": h,
        "storyboard_sha256": h,
        "revision_count": attempt - 1,
        "critic_provenance": prov,
        "contract": contract,
        "blind_retell": {key: "fact" for key in story_review.BLIND_FIELDS},
        "hard_checks": {key: True for key in story_review.HARD_CHECKS},
        "issue_codes": [],
        "summary": {"passed": True},
    }


def test_unauthorized_attempt_three_is_not_valid():
    data = _candidate(3, authorized=False)
    errors = story_review.validate_payload(data, story_sha="a" * 64, storyboard_sha="a" * 64, version="2.6.1")
    assert any("explicitly authorized policy continuation" in error for error in errors)


def test_attempt_three_requires_true_review_epoch_provenance():
    data = _candidate(3, authorized=True)
    assert story_review.validate_payload(data, story_sha="a" * 64, storyboard_sha="a" * 64, version="2.6.1") == []
    data["critic_provenance"]["current_rubric_sha256"] = "c" * 64
    assert story_review.validate_payload(data, story_sha="a" * 64, storyboard_sha="a" * 64, version="2.6.1")
    data["critic_provenance"]["current_rubric_sha256"] = "d" * 64
    data["revision_count"] = 0
    assert story_review.validate_payload(data, story_sha="a" * 64, storyboard_sha="a" * 64, version="2.6.1")


def test_attempt_three_denied_without_explicit_flag(tmp_path):
    with pytest.raises(RuntimeError, match="explicit direct-user"):
        story_review.run_critic(tmp_path, attempt=3, codex_raw="codex", timeout=10)


def test_policy_continuation_refuses_previous_pass(monkeypatch, tmp_path):
    monkeypatch.setattr(story_review, "_locked_documentary_rubric", lambda _ep: True)
    monkeypatch.setattr(story_review, "load_review", lambda _ep: {
        "critic_provenance": {"attempt": 2}, "summary": {"passed": True}
    })
    with pytest.raises(RuntimeError, match="failed prior"):
        story_review._authorize_policy_continuation(tmp_path, attempt=3, prior_rubric_ref="some-ref")


def test_policy_continuation_refuses_existing_authorization(monkeypatch, tmp_path):
    monkeypatch.setattr(story_review, "_locked_documentary_rubric", lambda _ep: True)
    monkeypatch.setattr(story_review, "load_review", lambda _ep: {
        "critic_provenance": {"attempt": 2}, "summary": {"passed": False}
    })
    path = tmp_path / "meta/runtime/story-review-policy-continuation-a3.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="already authorized"):
        story_review._authorize_policy_continuation(tmp_path, attempt=3, prior_rubric_ref="some-ref")
