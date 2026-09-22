from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import delegated_delivery  # noqa: E402
import final_candidate_snapshot  # noqa: E402
import release_package  # noqa: E402


def test_delivery_modules_depend_on_story_review_export_not_legacy_literal():
    modules = (
        delegated_delivery,
        final_candidate_snapshot,
        release_package,
    )
    for module in modules:
        source = Path(module.__file__).read_text(encoding="utf-8-sig")
        assert "materialize_review_export" in source
        assert "story_review.load_review" in source
        assert "visual_profile_review_persistence.materialize_export" in source
        assert "visual_profile_review_persistence.load" in source


def test_story_review_archive_name_stays_compatible():
    delegated_source = Path(delegated_delivery.__file__).read_text(encoding="utf-8-sig")
    snapshot_source = Path(final_candidate_snapshot.__file__).read_text(encoding="utf-8-sig")
    assert "qa/story-semantic-review.json" in delegated_source
    assert "qa/story-semantic-review.json" in snapshot_source
    assert "qa/visual-profile-review.json" in delegated_source
    assert "qa/visual-profile-review.json" in snapshot_source
