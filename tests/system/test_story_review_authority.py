from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import story_review  # noqa: E402


def test_load_review_uses_generic_review_owner(monkeypatch, tmp_path):
    payload = {"summary": {"passed": True}}
    monkeypatch.setattr(
        story_review.review_record_persistence,
        "load_latest",
        lambda _ep, _type, legacy_path=None: payload,
    )
    assert story_review.load_review(tmp_path) == payload


def test_save_review_delegates_to_generic_owner(monkeypatch, tmp_path):
    payload = {
        "summary": {"passed": True},
        "critic_provenance": {"runtime": "WORK_ISOLATED"},
    }
    calls = []
    monkeypatch.setattr(
        story_review.review_record_persistence,
        "save",
        lambda *args, **kwargs: calls.append((args, kwargs)) or {"mysql_written": True},
    )

    story_review.save_review(
        tmp_path, payload, decision="PASS", source_sha256="a" * 64
    )

    assert calls[0][0][1] == story_review.REVIEW_TYPE
    assert calls[0][0][2] == story_review.REVIEW_REL
    assert calls[0][1]["decision"] == "PASS"
    assert calls[0][1]["reviewer_type"] == "WORK_ISOLATED"


def test_review_required_uses_episode_state_authority(monkeypatch, tmp_path):
    monkeypatch.setattr(
        story_review.episode_state_persistence,
        "load",
        lambda _ep: {"tool_version": "2.6.1"},
    )
    assert story_review.review_required(tmp_path) is True


def test_materialized_export_is_not_legacy_authority(monkeypatch, tmp_path):
    payload = {"summary": {"passed": True}}
    monkeypatch.setattr(
        story_review.review_record_persistence,
        "load_latest",
        lambda *_args, **_kwargs: payload,
    )
    path = story_review.materialize_review_export(tmp_path, payload)
    assert path == tmp_path / story_review.EXPORT_REL
    assert path.is_file()
    assert not (tmp_path / story_review.REVIEW_REL).exists()
