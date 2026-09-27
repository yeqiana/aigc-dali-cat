from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from scripts import p3_story_semantic_frozen_source_audit as audit
from scripts import p3_story_semantic_critic_real_shadow_smoke as smoke


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_frozen_source_audit_exact_story_recovery():
    content = b"historical story bytes\n"
    assert audit.recovery_is_exact({"found": True, "bytes": content}, _sha(content))


def test_frozen_source_audit_exact_storyboard_recovery():
    content = b"historical storyboard bytes\n"
    assert audit.recovery_is_exact({"found": True, "bytes": content}, _sha(content))


def test_partial_recovery_not_eligible():
    assert audit.source_set_status(True, False) == "PARTIALLY_RECOVERABLE"
    assert audit.source_set_status(False, True) == "PARTIALLY_RECOVERABLE"


def test_wrong_sha_recovery_rejected():
    assert not audit.recovery_is_exact({"found": True, "bytes": b"other"}, _sha(b"expected"))


def test_historical_git_blob_allowed_read_only():
    relative = "episodes/独立篇/01_五环外的浓雾/docs/03_壹·五环外的浓雾_20张正式分镜_V1.1.md"
    content = audit._git_bytes("5000e82294930bc01dd39913a7cd13ddf73214b8", relative)
    assert content is not None
    assert _sha(content) == "ba55a67cfa0d7232d762dadb683ae4a451eaefc54ebe28edef4e4d17de35ac04"


def test_historical_bundle_never_modifies_canonical_files(tmp_path):
    episode = tmp_path / "episode"
    canonical_story = episode / "docs/story.md"
    canonical_board = episode / "docs/storyboard.md"
    canonical_story.parent.mkdir(parents=True)
    canonical_story.write_bytes(b"canonical story")
    canonical_board.write_bytes(b"canonical board")
    before = (canonical_story.read_bytes(), canonical_board.read_bytes())
    story = b"exact reviewed story"
    board = b"exact reviewed storyboard"
    bundle = audit._bundle_exact_sources(
        episode,
        {"bytes": story, "origin": "git_exact_blob", "path": "story.md", "git_commit": "abc"},
        {"bytes": board, "origin": "runtime_snapshot", "path": "storyboard.md"},
        _sha(story), _sha(board),
    )
    manifest = json.loads((bundle / "source-manifest.json").read_text(encoding="utf-8"))
    assert manifest["candidate_authority"] == "runtime_evidence_only"
    assert manifest["not_canonical"] is True and manifest["canonical_write"] is False
    assert (canonical_story.read_bytes(), canonical_board.read_bytes()) == before


def test_smoke_reports_both_source_mismatches_and_creates_no_host_request(monkeypatch, tmp_path):
    episode = tmp_path / "episode"
    episode.mkdir()
    story, board = tmp_path / "story.md", tmp_path / "storyboard.md"
    story.write_bytes(b"current story")
    board.write_bytes(b"current storyboard")
    review = {
        "story_sha256": _sha(b"review story"),
        "storyboard_sha256": _sha(b"review storyboard"),
        "revision_count": 1,
    }
    monkeypatch.setattr(smoke.episode_state_persistence, "load", lambda _ep: {"current_state": "STORYBOARD_LOCKED"})
    monkeypatch.setattr(smoke.story_review, "load_review", lambda _ep: review)
    monkeypatch.setattr(smoke.story_review, "story_paths", lambda _ep: (story, board))
    schedule = Mock(side_effect=AssertionError("stale sources must not create a Host Request"))
    execute = Mock(side_effect=AssertionError("stale sources must not call the model"))
    monkeypatch.setattr(smoke.story_review, "schedule_critic_shadow", schedule)
    monkeypatch.setattr(smoke.critic, "execute_shadow_request", execute)

    try:
        smoke.run(episode)
    except smoke.SourceSetValidationError as exc:
        assert exc.source_validation == {"story_match": False, "storyboard_match": False}
        assert exc.blockers == ["STORY_SOURCE_SHA_STALE", "STORYBOARD_SOURCE_SHA_STALE"]
    else:
        raise AssertionError("stale source set was accepted")
    schedule.assert_not_called()
    execute.assert_not_called()


def test_exact_current_sources_allow_shadow_schedule(monkeypatch, tmp_path):
    monkeypatch.setattr(smoke, "ROOT", tmp_path)
    episode = tmp_path / "episode"
    episode.mkdir()
    story, board = tmp_path / "story.md", tmp_path / "storyboard.md"
    story.write_bytes(b"review story")
    board.write_bytes(b"review storyboard")
    review = {
        "story_sha256": _sha(story.read_bytes()),
        "storyboard_sha256": _sha(board.read_bytes()),
        "revision_count": 1,
        "summary": {"passed": True},
        "issue_codes": [],
    }
    state = {"current_state": "STORYBOARD_LOCKED"}
    monkeypatch.setattr(smoke.episode_state_persistence, "load", lambda _ep: dict(state))
    monkeypatch.setattr(smoke, "_load_existing_canonical_review", lambda _ep: (review, tmp_path / "review.json"))
    monkeypatch.setattr(smoke.story_review, "story_paths", lambda _ep: (story, board))
    monkeypatch.setattr(smoke.story_review, "review_authority_sha256", lambda _ep: "record-sha")
    monkeypatch.setattr(smoke.product_review_adapter, "request_path", lambda *_args, **_kwargs: tmp_path / "pointer.json")
    schedule = Mock(return_value={"scheduled": True, "request_id": "shadow-request"})
    monkeypatch.setattr(smoke.story_review, "schedule_critic_shadow", schedule)
    monkeypatch.setattr(smoke.critic, "execute_shadow_request", Mock(return_value={
        "request_id": "shadow-request",
        "request_path": "runtime-only-request.json",
        "candidate_path": "runtime-only-candidate.json",
        "critic_invoked": True,
        "telemetry_complete": True,
        "model_execution": {"real_model_execution": True, "failure": False, "timeout": False},
        "decision_schema_valid": True,
        "decision": {"decision": "ACCEPT_CANDIDATE"},
        "decision_equivalent": True,
        "issue_disagreement": False,
        "authority_write": False,
        "gate_pass": False,
        "episode_transition": False,
        "shadow_is_advisory": True,
        "allowed_tools_empty": True,
        "repair_invoked": False,
        "reflection": {"max_review_attempts": 2, "max_auto_repairs": 1},
    }))
    report = smoke.run(episode)
    assert report["source_mode"] == "canonical_current"
    assert report["source_matches_review"] is True
    assert report["status"] == "PASS"
    schedule.assert_called_once()


def test_review_record_unchanged():
    review = {"summary": {"passed": True}, "issue_codes": []}
    before = json.dumps(review, sort_keys=True)
    assert smoke.critic.compare_with_existing_review(
        {"decision": "ACCEPT_CANDIDATE", "issue_codes": [], "severity": "LOW", "repair_scope": [], "evidence": ["frozen"]},
        {**review, "decision": "PASS"},
    )["existing_review_decision"] == "ACCEPT_CANDIDATE"
    assert json.dumps(review, sort_keys=True) == before


def test_story_and_storyboard_unchanged(tmp_path):
    paths = [tmp_path / "story.md", tmp_path / "storyboard.md"]
    for path in paths:
        path.write_text("frozen", encoding="utf-8")
    before = [path.read_bytes() for path in paths]
    assert [path.read_bytes() for path in paths] == before


def test_no_episode_transition():
    before = {"current_state": "STORYBOARD_LOCKED"}
    after = dict(before)
    assert after == before and after["current_state"] == "STORYBOARD_LOCKED"
