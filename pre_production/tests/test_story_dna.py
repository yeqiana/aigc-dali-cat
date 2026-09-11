#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests: Story DNA extraction (structure only, no judgement)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.story_dna import (  # noqa: E402
    COMPARISON_FIELDS,
    DIMENSIONS,
    REQUIRED_TOP_LEVEL,
    comparison_tokens,
    dimension_tokens,
    extract_story_dna,
    find_story_lock,
    has_differentiation,
    parse_metadata,
    parse_units,
    resolve_story_id,
    token_set,
    validate_dna,
)
from pre_production.tests.support import assert_no_scores  # noqa: E402

FIXED_TIME = "2026-09-11T00:00:00+08:00"

SAMPLE_LOCK = """# 《雾中的测试故事》Story Lock DRAFT V1.0

> 系列：10
> 集数：03
> 标题：雾中的测试故事

## 一、一句话故事

主角开车返程，在山坡停车带拍风景时，看见雾和低云里出现另一片正常生活。

## 二、正式剧情

两个年轻人是情侣，普通上班族。他们本来只想拍点旅行素材，结果越看越不对劲，心里发慌。

## 三、异常机制

局部重叠：两个有人正常生活的现实空间发生局部重叠，只在某些天气和潮湿低云的短暂时刻出现。

## 四、视觉与采集

第一人称手持拍摄，旧数码质感，画面里反复出现灯和雾。

## 五、反同质化

本集最高相似点是空间重叠，但机制不同，避免重复。
"""


class StoryDnaShapeTests(unittest.TestCase):
    def setUp(self):
        self.dna = extract_story_dna(text=SAMPLE_LOCK, story_id="10-03", extracted_at=FIXED_TIME)

    def test_required_top_level_and_dimensions_present(self):
        for key in REQUIRED_TOP_LEVEL:
            self.assertIn(key, self.dna, "missing required key: " + key)
        for dim, subs in DIMENSIONS.items():
            self.assertIn(dim, self.dna)
            for sub in subs:
                self.assertIn(sub, self.dna[dim], "missing subfield: " + dim + "." + sub)

    def test_schema_shape_is_valid(self):
        self.assertEqual(validate_dna(self.dna), [])

    def test_every_subfield_is_string_or_string_list(self):
        for dim, subs in DIMENSIONS.items():
            for sub in subs:
                value = self.dna[dim][sub]
                if isinstance(value, list):
                    for item in value:
                        self.assertIsInstance(item, str)
                else:
                    self.assertIsInstance(value, str)

    def test_extracts_structuring_tokens_not_scores(self):
        self.assertIn("mountain_area", self.dna["setting"]["location"])
        self.assertIn("fog_environment", self.dna["setting"]["environment"])
        self.assertEqual(self.dna["anomaly"]["anomaly_type"], ["spatial_overlap_anomaly"])
        self.assertIn("romantic_partner", self.dna["relationship"]["relationship_type"])
        self.assertIn("first_person_handheld_capture", self.dna["visual_pattern"]["camera_style"])
        self.assertEqual(self.dna["series_fit"]["differentiation_evidence"], ["declared"])

    def test_no_score_like_keys_anywhere(self):
        assert_no_scores(self, self.dna, "story_dna")

    def test_title_and_story_id_resolution(self):
        self.assertEqual(self.dna["title"], "雾中的测试故事")
        self.assertEqual(self.dna["story_id"], "10-03")

    def test_evidence_records_keyword_anchor_and_snippet(self):
        self.assertTrue(self.dna["evidence"])
        anomaly = [e for e in self.dna["evidence"]
                   if e["field"] == "anomaly.anomaly_type" and e["token"] == "spatial_overlap_anomaly"]
        self.assertTrue(anomaly, "anomaly token must carry evidence")
        record = anomaly[0]
        self.assertEqual(record["keyword"], "局部重叠")
        self.assertTrue(record["anchor"])
        self.assertIn("局部重叠", record["snippet"])

    def test_derived_environment_pattern_follows_setting(self):
        self.assertEqual(self.dna["visual_pattern"]["environment_pattern"],
                         list(self.dna["setting"]["environment"]))

    def test_extraction_is_deterministic(self):
        again = extract_story_dna(text=SAMPLE_LOCK, story_id="10-03", extracted_at=FIXED_TIME)
        self.assertEqual(again, self.dna)

    def test_sha256_is_recorded_for_the_source_text(self):
        self.assertEqual(len(self.dna["source"]["story_lock_sha256"]), 64)
        self.assertEqual(self.dna["source"]["rule_version"], "1")


class StoryDnaScopeTests(unittest.TestCase):
    def test_anomaly_keyword_outside_its_section_is_not_claimed(self):
        text = "# 《范围测试》\n\n## 正式剧情\n\n这里提到局部重叠，但没有独立的机制章节。\n"
        dna = extract_story_dna(text=text, story_id="SCOPE-01", extracted_at=FIXED_TIME)
        self.assertEqual(dna["anomaly"]["anomaly_type"], [])

    def test_anomaly_keyword_inside_its_section_is_claimed(self):
        text = "# 《范围测试》\n\n## 异常机制\n\n局部重叠。\n"
        dna = extract_story_dna(text=text, story_id="SCOPE-02", extracted_at=FIXED_TIME)
        self.assertEqual(dna["anomaly"]["anomaly_type"], ["spatial_overlap_anomaly"])

    def test_missing_keyword_never_guesses_a_value(self):
        text = "# 《空测试》\n\n## 正式剧情\n\n这里是一段占位内容。\n"
        dna = extract_story_dna(text=text, story_id="EMPTY-01", extracted_at=FIXED_TIME)
        for dim in DIMENSIONS:
            self.assertEqual(dimension_tokens(dna, dim), set(), dim + " should stay empty")
        self.assertTrue(dna["extraction_trace"]["warnings"])

    def test_generic_tokens_are_excluded_from_comparison(self):
        dna = extract_story_dna(text=SAMPLE_LOCK, story_id="10-03", extracted_at=FIXED_TIME)
        self.assertIn("first_person_handheld_capture", dimension_tokens(dna, "visual_pattern"))
        self.assertNotIn("first_person_handheld_capture",
                         comparison_tokens(dna)["visual_pattern"])

    def test_comparison_fields_are_a_subset_of_dimensions(self):
        for dim, fields in COMPARISON_FIELDS.items():
            self.assertIn(dim, DIMENSIONS)
            for field in fields:
                self.assertIn(field, DIMENSIONS[dim])


class StoryDnaParsingTests(unittest.TestCase):
    def test_parse_units_captures_headings_and_preamble(self):
        units = parse_units(SAMPLE_LOCK)
        headings = [u["heading"] for u in units if u["heading"]]
        self.assertEqual(units[0]["heading"], "")
        self.assertIn("三、异常机制", headings)

    def test_parse_metadata_reads_quoted_header_lines(self):
        meta = parse_metadata(SAMPLE_LOCK)
        self.assertEqual(meta.get("系列"), "10")
        self.assertEqual(meta.get("集数"), "03")

    def test_resolve_story_id_prefers_explicit_then_meta(self):
        self.assertEqual(resolve_story_id(None, {"系列": "10", "集数": "03"}, "EXPLICIT"), "EXPLICIT")
        self.assertEqual(resolve_story_id(None, {"系列": "10", "集数": "03"}), "10-03")
        self.assertEqual(resolve_story_id(Path("D:/tmp/20260101_EP007_x")), "EP07")

    def test_resolve_story_id_reads_episode_state(self):
        with tempfile.TemporaryDirectory(prefix="pp-dna-") as tmp:
            ep = Path(tmp) / "ep"
            (ep / "meta").mkdir(parents=True)
            (ep / "meta" / "episode-state.json").write_text(
                '{"episode_id": "12-09"}', encoding="utf-8")
            self.assertEqual(resolve_story_id(ep), "12-09")

    def test_find_story_lock_prefers_docs_over_story(self):
        with tempfile.TemporaryDirectory(prefix="pp-lock-") as tmp:
            ep = Path(tmp) / "ep"
            (ep / "docs").mkdir(parents=True)
            (ep / "story").mkdir(parents=True)
            (ep / "docs" / "02_示范_StoryLock_V1.0.md").write_text("# x", encoding="utf-8")
            (ep / "story" / "01_StoryLock.md").write_text("# y", encoding="utf-8")
            found = find_story_lock(ep)
            self.assertEqual(found.name, "02_示范_StoryLock_V1.0.md")

    def test_find_story_lock_ignores_meta_dir(self):
        with tempfile.TemporaryDirectory(prefix="pp-lock-") as tmp:
            ep = Path(tmp) / "ep"
            (ep / "meta").mkdir(parents=True)
            (ep / "meta" / "StoryLock_backup.md").write_text("# x", encoding="utf-8")
            self.assertIsNone(find_story_lock(ep))

    def test_token_set_and_has_differentiation_helpers(self):
        self.assertEqual(token_set("a"), {"a"})
        self.assertEqual(token_set(["a", "b"]), {"a", "b"})
        self.assertEqual(token_set(None), set())
        self.assertTrue(has_differentiation({"series_fit": {"differentiation_evidence": ["declared"]}}))
        self.assertFalse(has_differentiation({"series_fit": {"differentiation_evidence": []}}))


if __name__ == "__main__":
    unittest.main()
