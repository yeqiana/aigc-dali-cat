#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import canvas_normalize
import codex_subscription_image
import image_model_policy
import image_scheduler
import production_ledger
import runtime_request


class RuntimeRequestQualityTests(unittest.TestCase):
    def test_new_request_locks_model_and_quality(self):
        request = runtime_request.compile_request("全自动做一篇「比例合同测试」。")
        self.assertEqual(request["image_model"], "gpt-image-2")
        self.assertEqual(request["image_quality"], "high")
        self.assertEqual(request["image"]["model"], request["image_model"])
        self.assertEqual(request["image"]["quality"], request["image_quality"])
        self.assertEqual(runtime_request.validate_request(request), [])

    def test_legacy_request_defaults_to_high_without_mutation(self):
        request = {"image": {"provider": "openai", "model": "gpt-image-2", "source": "system_default", "strict_model": False}}
        policy = image_model_policy.resolve_model(request=request)
        self.assertEqual(policy["quality"], "high")
        self.assertNotIn("image_quality", request)


class NormalizePolicyTests(unittest.TestCase):
    def test_exact_png_is_noop_without_reencoding(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src, dst = root / "raw.png", root / "candidate.png"
            Image.new("RGB", (1080, 1350), (12, 34, 56)).save(src, "PNG")
            before = src.read_bytes()
            result = canvas_normalize.normalize(src, dst, 1080, 1350)
            self.assertEqual(result["operation"], "NOOP")
            self.assertFalse(result["reencoded"])
            self.assertFalse(result["crop_applied"])
            self.assertEqual(dst.read_bytes(), before)
            self.assertEqual(src.read_bytes(), before)

    def test_small_ratio_delta_resizes_without_crop(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src, dst = root / "raw.png", root / "candidate.png"
            Image.new("RGB", (100, 126), (1, 2, 3)).save(src, "PNG")
            result = canvas_normalize.normalize(src, dst, 100, 125)
            self.assertEqual(result["operation"], "RESIZE_LANCZOS")
            self.assertFalse(result["crop_applied"])
            with Image.open(dst) as image:
                self.assertEqual(image.size, (100, 125))

    def test_review_and_reject_thresholds(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review = root / "review.png"
            reject = root / "reject.png"
            Image.new("RGB", (96, 125), (1, 2, 3)).save(review, "PNG")
            Image.new("RGB", (90, 125), (1, 2, 3)).save(reject, "PNG")
            with self.assertRaises(canvas_normalize.NormalizeError) as ctx:
                canvas_normalize.normalize(review, root / "review-out.png", 100, 125)
            self.assertEqual(ctx.exception.code, "NORMALIZE_REVIEW")
            with self.assertRaises(canvas_normalize.NormalizeError) as ctx:
                canvas_normalize.normalize(reject, root / "reject-out.png", 100, 125)
            self.assertEqual(ctx.exception.code, "ASPECT_RATIO_MISMATCH")

    def test_technical_failure_retries_locally(self):
        expected = {"operation": "NOOP"}
        with mock.patch.object(canvas_normalize, "_normalize_once", side_effect=[OSError("one"), OSError("two"), expected]) as call:
            result = canvas_normalize.normalize(Path("raw.png"), Path("candidate.png"), 1080, 1350)
        self.assertEqual(call.call_count, 3)
        self.assertEqual(result["local_attempts"], 3)


class BackendAndLedgerContractTests(unittest.TestCase):
    def test_worker_consumes_exact_canvas_and_high_quality(self):
        prompt = codex_subscription_image.worker_prompt("scene", [], "1080x1920")
        self.assertIn("quality=high", prompt)
        self.assertIn("canvas=1080x1920 exactly", prompt)
        self.assertEqual(codex_subscription_image.provider_size(1080, 1920), "1080x1920")

    def test_normalize_failures_are_not_auto_requeued_for_generation(self):
        self.assertEqual(image_scheduler.classify_error("NORMALIZE_REVIEW: manual review"), "NORMALIZE_REVIEW")
        self.assertEqual(image_scheduler.classify_error("ASPECT_RATIO_MISMATCH: reject"), "ASPECT_RATIO_MISMATCH")
        self.assertIn("NORMALIZE_REVIEW", image_scheduler.NON_REGENERATING_FAILURE_CODES)
        self.assertIn("IMAGE_QUALITY_CONTRACT_MISMATCH", image_scheduler.NON_REGENERATING_FAILURE_CODES)

    def test_ledger_records_model_quality_and_contract_sha_field(self):
        with tempfile.TemporaryDirectory() as td:
            ep = Path(td)
            (ep / "meta").mkdir()
            (ep / "meta/release-manifest.json").write_text(
                json.dumps({"episode": {"aspect_ratio": "4:5"}, "release": {"body_frame_count": 1}}),
                encoding="utf-8",
            )
            production_ledger.init_ledger(ep)
            args = argparse.Namespace(
                episode_dir=str(ep), frame="01", kind="original", prompt="ordinary snapshot",
                prompt_file=None, capture_id="CP01", model="gpt-image-2", quality="high",
                reference=None, notes="test", allow_long_prompt=False,
            )
            production_ledger.cmd_begin(args)
            data = json.loads((ep / "meta/production-ledger.json").read_text(encoding="utf-8"))
            request = data["frames"]["01"]["attempts"][0]["request"]
            self.assertEqual(request["model"], "gpt-image-2")
            self.assertEqual(request["quality"], "high")
            self.assertIn("frame_contract_sha256", request)

    def test_m00_machine_contract_contains_required_final_fields(self):
        data = json.loads((ROOT / "standards/visual_profiles/M00_MP4_网吧_流水席_旧数码.json").read_text(encoding="utf-8"))
        self.assertEqual(data["profile_name"], "现实生活纪实母版")
        dna = data["visual_dna"]
        self.assertTrue(dna["reality_first"])
        self.assertEqual(dna["ghost_camera"], "forbidden")
        self.assertEqual(dna["seed_dependency"], "none")
        self.assertEqual(dna["visual_polish_ceiling"], "documentary_realism")


if __name__ == "__main__":
    unittest.main()
