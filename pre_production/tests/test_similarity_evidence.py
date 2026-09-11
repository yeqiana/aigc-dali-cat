#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests: similarity analysis outputs evidence, never a score."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.similarity_analysis.analyzer import (  # noqa: E402
    analyze_similarity,
    classify_level,
    match_dimensions,
)
from pre_production.similarity_analysis.evidence import (  # noqa: E402
    build_evidence,
    count_levels,
    sort_evidence,
)
from pre_production.story_dna.validator import validate_similarity_evidence  # noqa: E402
from pre_production.tests.support import assert_no_scores, build_dna  # noqa: E402

ANOMALY = {"anomaly__anomaly_type": ["spatial_overlap_anomaly"]}
ANOMALY_SETTING = dict(ANOMALY, setting__location=["mountain_area"])
ANOMALY_VISUAL = dict(ANOMALY, visual_pattern__camera_style=["drone_feed_capture"])


def history_sample(story_id: str, title: str, **values) -> dict:
    return build_dna(story_id, title, **values)


class ClassifyLevelTests(unittest.TestCase):
    def test_no_match_is_none(self):
        self.assertIsNone(classify_level({}))

    def test_anomaly_with_setting_is_high(self):
        self.assertEqual(classify_level({"anomaly": ["x"], "setting": ["y"]}), "HIGH")

    def test_anomaly_with_visual_is_high(self):
        self.assertEqual(classify_level({"anomaly": ["x"], "visual_pattern": ["y"]}), "HIGH")

    def test_anomaly_alone_is_medium(self):
        self.assertEqual(classify_level({"anomaly": ["x"]}), "MEDIUM")

    def test_setting_visual_and_relationship_is_medium(self):
        self.assertEqual(classify_level({"setting": ["x"], "visual_pattern": ["y"],
                                         "relationship": ["z"]}), "MEDIUM")

    def test_partial_match_is_low(self):
        self.assertEqual(classify_level({"emotion": ["unease"]}), "LOW")


class DetermineEvidenceTests(unittest.TestCase):
    def test_no_shared_dimension_emits_no_evidence(self):
        current = build_dna("CUR-01", "当前", **ANOMALY_SETTING)
        other = build_dna("HIS-99", "无关", setting__location=["urban_area"])
        self.assertEqual(analyze_similarity(current, [other]), [])

    def test_generic_tokens_alone_emit_no_evidence(self):
        current = build_dna("CUR-01", "当前",
                            visual_pattern__camera_style=["first_person_handheld_capture"],
                            character__protagonist_profile=["ordinary_young_adult"])
        other = build_dna("HIS-01", "历史",
                          visual_pattern__camera_style=["first_person_handheld_capture"],
                          character__protagonist_profile=["ordinary_young_adult"])
        self.assertEqual(analyze_similarity(current, [other]), [])

    def test_high_risk_evidence_shape_and_traceability(self):
        current = build_dna("CUR-01", "当前", **ANOMALY_SETTING)
        other = history_sample("HIS-01", "历史高危", **ANOMALY_SETTING)
        items = analyze_similarity(current, [other])
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["risk_level"], "HIGH")
        self.assertEqual(item["related_episode_id"], "HIS-01")
        self.assertEqual(item["current_story_id"], "CUR-01")
        self.assertIn("anomaly", item["matched_dimensions"])
        self.assertIn("spatial_overlap_anomaly", item["matched_features"])
        self.assertEqual(item["evidence_id"], "SE-CUR-01-HIS-01")
        self.assertEqual(validate_similarity_evidence(item), [])
        assert_no_scores(self, item, "similarity_evidence")

    def test_evidence_never_states_a_percentage(self):
        current = build_dna("CUR-01", "当前", **ANOMALY_SETTING)
        other = history_sample("HIS-01", "历史", **ANOMALY_SETTING)
        item = analyze_similarity(current, [other])[0]
        self.assertNotIn("%", item["explanation"])
        self.assertIn("不使用相似度分数", item["explanation"])

    def test_levels_are_sorted_high_first(self):
        current = build_dna("CUR-01", "当前", emotion__primary_emotion=["unease"],
                            **ANOMALY_SETTING)
        history = [
            history_sample("HIS-LOW", "低", emotion__primary_emotion=["unease"]),
            history_sample("HIS-HIGH", "高", **ANOMALY_SETTING),
            history_sample("HIS-MED", "中", **ANOMALY),
        ]
        items = analyze_similarity(current, history)
        self.assertEqual([i["risk_level"] for i in items], ["HIGH", "MEDIUM", "LOW"])
        self.assertEqual([i["related_episode_id"] for i in items], ["HIS-HIGH", "HIS-MED", "HIS-LOW"])

    def test_match_dimensions_reports_shared_tokens_only(self):
        current = build_dna("CUR-01", "当前", **ANOMALY_SETTING)
        other = build_dna("HIS-01", "历史", anomaly__anomaly_type=["future_recording_anomaly"],
                          setting__location=["mountain_area"])
        matches = match_dimensions(current, other)
        self.assertEqual(matches, {"setting": ["mountain_area"]})


class EvidenceHelperTests(unittest.TestCase):
    def test_build_evidence_requires_expected_keys(self):
        item = build_evidence(
            current_story_id="A", related_episode_id="B", related_title="T",
            risk_level="LOW", matched_dimensions=["emotion"],
            matched_features=["unease"], explanation="低风险提示。")
        for key in ("evidence_id", "current_story_id", "related_episode_id",
                    "risk_type", "risk_level", "matched_dimensions",
                    "matched_features", "explanation"):
            self.assertIn(key, item)
        self.assertEqual(item["risk_type"], "similarity")

    def test_sort_and_count_helpers(self):
        items = [
            build_evidence(current_story_id="A", related_episode_id="3", related_title="t",
                           risk_level="LOW", matched_dimensions=["emotion"],
                           matched_features=["x"], explanation="e"),
            build_evidence(current_story_id="A", related_episode_id="1", related_title="t",
                           risk_level="HIGH", matched_dimensions=["anomaly"],
                           matched_features=["x"], explanation="e"),
        ]
        ordered = sort_evidence(items)
        self.assertEqual([i["related_episode_id"] for i in ordered], ["1", "3"])
        self.assertEqual(count_levels(ordered), {"HIGH": 1, "MEDIUM": 0, "LOW": 1})


if __name__ == "__main__":
    unittest.main()

