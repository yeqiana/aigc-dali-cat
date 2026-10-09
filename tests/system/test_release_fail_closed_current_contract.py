"""Fail-closed release regressions without invented direct-user acceptance APIs.

Historical untracked tests relied on functions no longer present in the native
Review Authority path. These tests exercise only the current published contract.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import caption_image_audit
import release_package
import release_preflight_review


def test_caption_hash_change_invalidates_existing_final_audit(tmp_path: Path):
    ep = tmp_path / "episode"
    ep.mkdir()
    frames = [{"frame": "01", "path": ep / "01.png", "sha256": "a" * 64}]
    old = {
        "schema_version": caption_image_audit.SCHEMA,
        "caption_source": {"review_image": {"mode": "final_publish_with_subtitle"}},
        "frames": {"01": {
            "image_sha256": "a" * 64, "caption_sha256": "b" * 64,
            "supported": True, "subtitle_unobstructed": True, "passed": True,
        }},
    }
    with (
        mock.patch.object(caption_image_audit, "_review_frame_records",
                          return_value=(frames, {"mode": "final_publish_with_subtitle"})),
        mock.patch.object(caption_image_audit, "_read", return_value=old),
        mock.patch.object(caption_image_audit, "_hashes",
                          return_value=({"01": "a" * 64}, {"01": "c" * 64}, {}, {})),
    ):
        errors = caption_image_audit.verify(ep)
    assert any("caption SHA stale: 01" in error for error in errors)


def test_release_critic_uncertainty_remains_blocked(tmp_path: Path):
    ep = tmp_path / "episode"
    ep.mkdir()
    checks = {key: True for key in release_preflight_review.RELEASE_CHECKS}
    # The final critic must not infer missing caption evidence from free text.
    checks["no_caption_invented_core_evidence"] = False
    data = {
        "schema_version": 1, "story_os_version": "2.6.1",
        "artifacts": {"body01": {"sha256": "a" * 64}},
        "critic_provenance": {},
        "release_checks": checks,
        "issue_codes": ["CAPTION_CORE_EVIDENCE_UNVERIFIED"],
        "summary": {"passed": False},
    }
    with (
        mock.patch.object(release_preflight_review, "episode_contract_version", return_value="2.6.1"),
        mock.patch.object(release_preflight_review, "release_hashes", return_value=data["artifacts"]),
        mock.patch.object(release_preflight_review.runtime_provenance, "validate_critic_provenance",
                          return_value=[]),
    ):
        errors = release_preflight_review.validate_release_review(ep, data)
    assert any("release_checks.no_caption_invented_core_evidence" in e for e in errors)
    assert any("issue_codes not empty" in e for e in errors)
    assert any("summary.passed must be true" in e for e in errors)


def test_release_package_requires_verified_review_authority_before_any_output(tmp_path: Path):
    ep = tmp_path / "episode"
    ep.mkdir()
    with (
        mock.patch.object(
            release_package.verified_review_authority,
            "require_verified_episode_review_authority",
            side_effect=RuntimeError("REVIEW_AUTHORITY_NOT_VERIFIED"),
        ) as authority,
        mock.patch.object(release_package, "load_json") as load_manifest,
        mock.patch.object(release_package, "file_row") as file_row,
    ):
        with pytest.raises(RuntimeError, match="REVIEW_AUTHORITY_NOT_VERIFIED"):
            release_package.build_payload(ep)
    authority.assert_called_once_with(ep, metadata_only=False)
    load_manifest.assert_not_called()
    file_row.assert_not_called()
