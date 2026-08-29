#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import contract_sync  # noqa: E402
import story_os_contract  # noqa: E402
import story_review  # noqa: E402
import subtitle_layout  # noqa: E402
import visual_profile  # noqa: E402
import visual_review  # noqa: E402


class CreativeEnforcementTests(unittest.TestCase):
    def test_product_version(self):
        manifest = json.loads((ROOT / "story_os_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["story_os_version"], story_os_contract.story_os_version(ROOT))
        self.assertEqual(manifest["stages"], [
            "IDEA_LOCKED", "STORYBOARD_LOCKED", "VISUAL_CALIBRATED",
            "PRODUCTION_PASSED", "PUBLISH_READY", "PUBLISHED", "DATA_REVIEWED",
        ])

    def test_default_visual_contract_is_m00(self):
        contract = visual_profile.compile_prompt_contract(ROOT / "episodes")
        self.assertEqual(contract["profile_id"], "M00")
        self.assertEqual(len(contract["profile_sha256"]), 64)
        self.assertIn("reality", contract["text"].lower())
        self.assertIn("cinematic", contract["text"].lower())

    def test_story_contract_rejects_mechanism_failure(self):
        h = "a" * 64
        data = {
            "schema_version": 1,
            "story_os_version": "2.0.3.2",
            "story_sha256": h,
            "storyboard_sha256": h,
            "revision_count": 0,
            "critic_provenance": {"runtime": "CODEX_ISOLATED", "isolated_session": True, "attempt": 1},
            "contract": {key: "x" for key in story_review.CONTRACT_FIELDS},
            "blind_retell": {key: "x" for key in story_review.BLIND_FIELDS},
            "hard_checks": {key: True for key in story_review.HARD_CHECKS},
            "issue_codes": [],
            "summary": {"passed": True},
        }
        data["contract"]["ending_recontextualization"] = ["1", "2", "3"]
        self.assertEqual(story_review.validate_payload(data, story_sha=h, storyboard_sha=h, version="2.0.3.2"), [])
        data["hard_checks"]["mechanism_consistency"] = False
        self.assertTrue(story_review.validate_payload(data, story_sha=h, storyboard_sha=h, version="2.0.3.2"))

    def test_visual_review_requires_actual_profile_checks(self):
        h = "b" * 64
        assets = [{"id": x, "sha256": h} for x in ("1", "2", "3")]
        data = {
            "schema_version": 1,
            "story_os_version": "2.0.3.2",
            "profile_id": "M00",
            "profile_sha256": h,
            "critic_provenance": {"runtime": "CODEX_ISOLATED", "isolated_session": True, "attempt": 1},
            "calibration": [
                {"id": x, "sha256": h, "checks": {k: True for k in visual_review.CHECKS}, "issues": []}
                for x in ("1", "2", "3")
            ],
            "issue_codes": [],
            "summary": {"passed": True},
        }
        self.assertEqual(visual_review.validate_payload(data, profile_id="M00", profile_sha=h, assets=assets, version="2.0.3.2"), [])
        data["calibration"][1]["checks"]["unposed_capture"] = False
        self.assertTrue(visual_review.validate_payload(data, profile_id="M00", profile_sha=h, assets=assets, version="2.0.3.2"))

    def test_punctuation_only_second_line_is_dropped(self):
        lines, dropped = subtitle_layout.sanitize_wrapped_lines(["第一行文字", "。！？……”）"])
        self.assertEqual(lines, ["第一行文字"])
        self.assertTrue(dropped)
        lines, dropped = subtitle_layout.sanitize_wrapped_lines(["第一行", "第二行。"])
        self.assertEqual(lines, ["第一行", "第二行。"])
        self.assertFalse(dropped)

    def test_delegated_approval_uses_product_version(self):
        text = (HERE / "delegated_approval.py").read_text(encoding="utf-8-sig")
        self.assertIn("story_os_version", text)
        self.assertNotIn("'story_os_version': '2.0.2'", text)
        self.assertNotIn("store['story_os_version'] = '2.0.2'", text)

    def test_image_backend_injects_visual_contract(self):
        text = (HERE / "codex_subscription_image.py").read_text(encoding="utf-8-sig")
        self.assertIn("compile_prompt_contract", text)
        self.assertIn("<visual_contract>", text)
        self.assertIn("visual_profile", text)

    def test_story_and_visual_locks_require_reviews(self):
        text = (HERE / "approval_lock.py").read_text(encoding="utf-8-sig")
        self.assertIn("verify_story_review", text)
        self.assertIn("verify_visual_review", text)
        evidence = (HERE / "evidence_gate.py").read_text(encoding="utf-8-sig")
        self.assertIn("verify_story_review", evidence)
        self.assertIn("verify_visual_review", evidence)
        self.assertIn("verify_layout_audit", evidence)

    def test_ci_runs_creative_enforcement(self):
        workflow = (ROOT / ".github/workflows/story-gates.yml").read_text(encoding="utf-8-sig")
        self.assertIn("test_v2032_creative_enforcement.py -v", workflow)
        self.assertIn("subtitle_layout.py self-test", workflow)
        self.assertIn("story_review.py self-test", workflow)
        self.assertIn("visual_review.py self-test", workflow)

    def test_full_contract_sync(self):
        self.assertEqual(contract_sync.collect_errors(ROOT), [])


if __name__ == "__main__":
    unittest.main()
