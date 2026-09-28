from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.p3_story_semantic_critic_paired_benchmark import _collect_samples, _eligible, _fixture_rows


def test_prepare_collects_unique_sha_bound_historical_review_labels_without_execution(tmp_path):
    episodes = []
    for index in range(5):
        episode = tmp_path / "episodes" / f"ep-{index}"
        (episode / "meta").mkdir(parents=True)
        (episode / "docs").mkdir()
        story = episode / "docs/story.md"
        board = episode / "docs/storyboard.md"
        story.write_text(f"story {index}", encoding="utf-8")
        board.write_text(f"board {index}", encoding="utf-8")
        import hashlib
        review = {
            "story_sha256": hashlib.sha256(story.read_bytes()).hexdigest(),
            "storyboard_sha256": hashlib.sha256(board.read_bytes()).hexdigest(),
            "summary": {"passed": index != 4},
            "issue_codes": [] if index != 4 else ["FIXTURE_ISSUE"],
            "critic_provenance": {"attempt": 2, "reviewed_at": "2026-09-20T00:00:00+00:00"},
        }
        (episode / "meta/story-semantic-review.json").write_text(
            json.dumps(review), encoding="utf-8"
        )
        (episode / "meta/release-manifest.json").write_text(json.dumps({
            "artifacts": {
                "story": story.relative_to(tmp_path).as_posix(),
                "storyboard": board.relative_to(tmp_path).as_posix(),
            }
        }), encoding="utf-8")
        (episode / "meta/episode-state.json").write_text(json.dumps({"current_state": "STORYBOARD_LOCKED"}), encoding="utf-8")
        episodes.append(episode)

    candidates, selected = _collect_samples(tmp_path, episodes)
    assert len(candidates) == 5
    assert len({row["story_sha256"] for row in selected}) == 5
    assert {row["review_label"] for row in selected} == {"PASS", "FAIL"}
    assert all(row["source_sha_consistent"] for row in selected)
    assert all(row["canonical_files_modified"] is False for row in selected)


def test_fixture_sample_set_has_distinct_sources_and_pass_fail_diversity():
    rows = _fixture_rows()
    eligible, counts, blockers = _eligible(rows + [{
        "sample_id": "real", "sample_type": "real_episode", "reference_label": "PASS",
        "story_sha256": "real-story", "storyboard_sha256": "real-board",
        "applicability_sha256": "real-applicability", "source_sha_consistent": True,
    }])
    assert len(rows) == 4
    assert {row["reference_label"] for row in rows} == {"PASS", "FAIL"}
    assert all(row["source_sha_consistent"] for row in rows)
    assert eligible is True
    assert counts == {"PASS": 3, "FAIL": 2}
    assert blockers == []


def test_sample_gate_rejects_pass_only_and_duplicate_source_sets():
    row = {"reference_label": "PASS", "story_sha256": "s", "storyboard_sha256": "b",
           "applicability_sha256": "a", "source_sha_consistent": True}
    eligible, _, blockers = _eligible([dict(row, sample_id=str(index)) for index in range(5)])
    assert eligible is False
    assert "PASS_FAIL_LABEL_DIVERSITY_NOT_MET" in blockers
    assert "SOURCE_SHA_MISSING_OR_DUPLICATE" in blockers
