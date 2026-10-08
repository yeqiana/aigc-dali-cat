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


def _review(attempt=5):
    h="a"*64
    prov=runtime_provenance.build_critic_provenance(
        "CODEX", attempt=attempt, allow_user_continuation_attempt=True
    )
    prov.update({
        "review_scope":"LOCKED_DOCUMENTARY_SYMBOLIC_REMEDIATION",
        "review_epoch":4, "epoch_attempt":1,
        "previous_review_sha256":"b"*64,
        "previous_storyboard_sha256":"c"*64,
        "previous_rubric_sha256":"d"*64,
        "current_rubric_sha256":"e"*64,
    })
    contract={k:"fact" for k in story_review.CONTRACT_FIELDS}
    contract["ending_recontextualization"]=["land","debt","loss"]
    return {
        "schema_version":1, "story_os_version":"2.6.1",
        "story_sha256":h, "storyboard_sha256":h,
        "revision_count":attempt-1, "critic_provenance":prov,
        "contract":contract,
        "blind_retell":{k:"fact" for k in story_review.BLIND_FIELDS},
        "hard_checks":{k:True for k in story_review.HARD_CHECKS},
        "issue_codes":[], "summary":{"passed":True},
    }


def _validate(data):
    return story_review.validate_payload(
        data, story_sha="a"*64, storyboard_sha="a"*64, version="2.6.1"
    )


def test_attempt_five_needs_matched_policy_and_source():
    data=_review()
    assert _validate(data)==[]
    data["critic_provenance"]["previous_storyboard_sha256"]="a"*64
    assert _validate(data)
    data["critic_provenance"]["previous_storyboard_sha256"]="c"*64
    data["critic_provenance"]["previous_rubric_sha256"]="e"*64
    assert _validate(data)


def test_caption_source_sha_must_be_bound_when_present():
    data = _review()
    data['critic_provenance']['subtitle_source_sha256'] = 'f'*64
    data['subtitle_source_sha256'] = 'f'*64
    assert _validate(data) == []
    data['subtitle_source_sha256'] = 'e'*64
    assert 'review subtitle source SHA binding mismatch' in _validate(data)


def test_no_sixth_auto_review_or_missing_auth():
    assert _validate(_review(6))
    data=_review()
    data["critic_provenance"]["direct_user_continuation_review"]=False
    assert _validate(data)
    with pytest.raises(RuntimeError, match="explicit direct-user"):
        story_review.run_critic(Path("."),attempt=5,codex_raw="codex")


def test_repeated_symbolic_authorization_denied(monkeypatch,tmp_path):
    monkeypatch.setattr(story_review,"_locked_documentary_rubric",lambda _ep:True)
    path=tmp_path/"meta/runtime/story-review-symbolic-remediation-a5.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}",encoding="utf-8")
    with pytest.raises(RuntimeError,match="already authorized"):
        story_review._authorize_symbolic_remediation(tmp_path,attempt=5)


def test_source_and_rubric_must_be_from_real_failed_a4(monkeypatch,tmp_path):
    monkeypatch.setattr(story_review,"_locked_documentary_rubric",lambda _ep:True)
    monkeypatch.setattr(story_review,"load_review",lambda _ep:{
        "critic_provenance":{"attempt":4}, "summary":{"passed":True},
        "issue_codes":["DOCUMENTARY_EVIDENCE_UNSUPPORTED"],
    })
    with pytest.raises(RuntimeError,match="failed documentary evidence review"):
        story_review._authorize_symbolic_remediation(tmp_path,attempt=5)
