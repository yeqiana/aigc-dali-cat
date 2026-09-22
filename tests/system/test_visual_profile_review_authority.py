from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import visual_profile_review_persistence as visual_review_owner  # noqa: E402


def test_visual_profile_owner_loads_generic_review(monkeypatch, tmp_path):
    payload = {"schema_version": 2, "summary": {"passed": True}}
    monkeypatch.setattr(
        visual_review_owner.review_record_persistence,
        "load_latest",
        lambda _ep, _type, legacy_path=None: payload,
    )
    assert visual_review_owner.load(tmp_path) == payload


def test_visual_profile_owner_saves_one_logical_review_type(monkeypatch, tmp_path):
    payload = {
        "schema_version": 2,
        "summary": {"passed": True},
        "issue_codes": [],
        "critic_provenance": {"runtime": "WORK_ISOLATED"},
    }
    calls = []
    monkeypatch.setattr(
        visual_review_owner.review_record_persistence,
        "save",
        lambda *args, **kwargs: calls.append((args, kwargs)) or {},
    )
    visual_review_owner.save(tmp_path, payload)
    assert calls[0][0][1] == "VISUAL_PROFILE"
    assert calls[0][0][2] == visual_review_owner.LEGACY_REL
    assert calls[0][1]["decision"] == "PASS"
    assert calls[0][1]["reviewer_type"] == "WORK_ISOLATED"


def test_visual_profile_export_is_rebuildable_not_legacy_authority(monkeypatch, tmp_path):
    payload = {"schema_version": 2, "summary": {"passed": True}}
    path = visual_review_owner.materialize_export(tmp_path, payload)
    assert path == tmp_path / "meta/runtime/review-exports/visual-profile.json"
    assert path.is_file()
    assert not (tmp_path / visual_review_owner.LEGACY_REL).exists()
