import hashlib
import json
from pathlib import Path

import pytest

from scripts import p3_final_semantic_critic_frozen_source_audit as audit
from scripts import p3_final_semantic_critic_real_shadow_smoke as smoke


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _historical_bundle(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(smoke, "ROOT", tmp_path)
    ep = tmp_path / "episodes" / "sample"
    bundle = tmp_path / ".storyos" / "bundle"
    ep.mkdir(parents=True)
    bundle.mkdir(parents=True)
    (ep / "meta").mkdir()
    story = b"historical story\n"
    board = b"historical storyboard\n"
    captions = b"captions: historical\n"
    visual = {"v": 1}
    review_path = ep / smoke.frame_semantic_review.SUMMARY_REL
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text("{}", encoding="utf-8")
    review = {
        "story_sha256": _sha(story), "storyboard_sha256": _sha(board),
        "caption_source_sha256": _sha(captions), "visual_contract_sha256": smoke.critic.digest(visual),
    }
    story_path, board_path, caption_path = bundle / "story.md", bundle / "storyboard.md", bundle / "subtitles.yaml"
    story_path.write_bytes(story)
    board_path.write_bytes(board)
    caption_path.write_bytes(captions)
    sources = []
    for kind, path, raw, current in (
        ("story", story_path, story, "current-story-sha"),
        ("storyboard", board_path, board, "current-board-sha"),
        ("caption_source", caption_path, captions, "current-caption-sha"),
    ):
        sources.append({"kind": kind, "bundle_path": path.relative_to(tmp_path).as_posix(),
                        "review_bound_sha256": _sha(raw), "recovered_sha256": _sha(raw),
                        "current_sha256": current, "exact_match": True, "byte_exact": True})
    sources.append({"kind": "visual_contract_projection", "review_bound_sha256": smoke.critic.digest(visual),
                    "exact_match": True})
    manifest = {
        "source_set_status": "RECOVERABLE_EXACT", "source_type": "historical_final_semantic_exact",
        "canonical": False, "canonical_write": False, "runtime_evidence_only": True,
        "episode": "episodes/sample", "canonical_final_review_sha256": _sha(b"{}"), "sources": sources,
    }
    (bundle / "source-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(smoke.frame_semantic_review, "stable_visual_contract", lambda _ep: visual)
    return ep, bundle, review, manifest


def test_git_exact_blob_is_allowed_and_byte_exact(tmp_path, monkeypatch):
    current = tmp_path / "current.md"
    current.write_bytes(b"new revision")
    expected = b"historical exact bytes"
    monkeypatch.setattr(audit, "git_exact_blob", lambda _path, _sha: (expected, "abc123"))
    row, recovered = audit.source_record("story", "episode/story.md", _sha(expected), current)
    assert row["recovery_origin"] == "git_exact_blob"
    assert row["git_commit"] == "abc123"
    assert row["recovered_sha256"] == _sha(expected)
    assert recovered == expected


def test_non_exact_reconstruction_is_rejected(tmp_path, monkeypatch):
    current = tmp_path / "current.md"
    current.write_bytes(b"current")
    monkeypatch.setattr(audit, "git_exact_blob", lambda _path, _sha: None)
    row, recovered = audit.source_record("story", "episode/story.md", _sha(b"target"), current)
    assert row["historical_exact_found"] is False
    assert row["exact_match"] is False
    assert recovered is None


def test_historical_bundle_exact_sources_validate_without_canonical_writes(tmp_path, monkeypatch):
    ep, bundle, review, _ = _historical_bundle(tmp_path, monkeypatch)
    before = {p: p.read_bytes() for p in ep.rglob("*") if p.is_file()}
    verified = smoke.validate_historical_source_bundle(bundle, ep, review)
    assert set(verified["sources"]) == {"story", "storyboard", "caption_source"}
    assert before == {p: p.read_bytes() for p in ep.rglob("*") if p.is_file()}


def test_partial_historical_bundle_fails_closed_before_request(tmp_path, monkeypatch):
    ep, bundle, review, _ = _historical_bundle(tmp_path, monkeypatch)
    (bundle / "storyboard.md").unlink()
    with pytest.raises(smoke.critic.FinalSemanticCriticError, match="storyboard"):
        smoke.validate_historical_source_bundle(bundle, ep, review)


def test_wrong_manifest_sha_fails_closed(tmp_path, monkeypatch):
    ep, bundle, review, manifest = _historical_bundle(tmp_path, monkeypatch)
    manifest["sources"][0]["review_bound_sha256"] = "0" * 64
    (bundle / "source-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(smoke.critic.FinalSemanticCriticError, match="story"):
        smoke.validate_historical_source_bundle(bundle, ep, review)


def test_current_visual_contract_drift_fails_closed(tmp_path, monkeypatch):
    ep, bundle, review, _ = _historical_bundle(tmp_path, monkeypatch)
    monkeypatch.setattr(smoke.frame_semantic_review, "stable_visual_contract", lambda _ep: {"v": 2})
    with pytest.raises(smoke.critic.FinalSemanticCriticError, match="Visual Contract"):
        smoke.validate_historical_source_bundle(bundle, ep, review)
