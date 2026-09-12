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
            Image.new("RGB", (98, 125), (1, 2, 3)).save(review, "PNG")
            Image.new("RGB", (96, 125), (1, 2, 3)).save(reject, "PNG")
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
    def _ready_episode(self, td: str) -> Path:
        ep = Path(td)
        (ep / "meta").mkdir()
        (ep / "meta/release-manifest.json").write_text(
            json.dumps({"episode": {"aspect_ratio": "4:5"}, "release": {"body_frame_count": 1}}),
            encoding="utf-8",
        )
        production_ledger.init_ledger(ep)
        return ep

    def _queue_item(self, prompt: Path) -> dict:
        return {"id": "q-recovery-01", "frame": 1, "kind": "original", "scope": "batch",
                "prompt_file": str(prompt), "capture_id": "CP01", "model": "gpt-image-2",
                "quality": "high", "references": []}

    def _no_spawn(self) -> mock._patch:
        return mock.patch("subprocess.run",
                          side_effect=AssertionError("ledger must not spawn a subprocess"))

    def test_ledger_bridge_begin_and_tech_fail_are_in_process(self):
        with tempfile.TemporaryDirectory() as td:
            ep = self._ready_episode(td)
            prompt = Path(td) / "prompt.md"
            prompt.write_text("ordinary snapshot", encoding="utf-8")
            item = self._queue_item(prompt)
            with self._no_spawn():
                ok, msg = image_scheduler.ledger_begin(ep, item)
            self.assertTrue(ok, msg)
            data = json.loads((ep / "meta/production-ledger.json").read_text(encoding="utf-8"))
            self.assertEqual(data["frames"]["01"]["status"], "GENERATING")
            with self._no_spawn():
                ok2, msg2 = image_scheduler.ledger_begin(ep, item)
            self.assertFalse(ok2)
            self.assertIn("cannot begin original", msg2)
            with self._no_spawn():
                image_scheduler.ledger_tech_fail(ep, item, "WORKER_FAILED", "boom")
            data = json.loads((ep / "meta/production-ledger.json").read_text(encoding="utf-8"))
            self.assertEqual(data["frames"]["01"]["status"], "TECH_FAILED")

    def test_batch_scheduler_ledger_begin_is_in_process(self):
        import batch_scheduler
        with tempfile.TemporaryDirectory() as td:
            ep = self._ready_episode(td)
            prompt = Path(td) / "prompt.md"
            prompt.write_text("ordinary snapshot", encoding="utf-8")
            with self._no_spawn():
                ok, msg = batch_scheduler.ledger_begin(ep, self._queue_item(prompt))
            self.assertTrue(ok, msg)
            data = json.loads((ep / "meta/production-ledger.json").read_text(encoding="utf-8"))
            self.assertEqual(data["frames"]["01"]["status"], "GENERATING")

    def test_ledger_bridge_maps_cli_failure_to_false_without_exit(self):
        import ledger_call
        with tempfile.TemporaryDirectory() as td:
            ep = self._ready_episode(td)
            prompt = Path(td) / "prompt.md"
            prompt.write_text("ordinary snapshot", encoding="utf-8")
            with self._no_spawn():
                ok, msg = ledger_call.begin(
                    ep, frame=1, kind="original", prompt_file=prompt, capture_id="CP01",
                    model="gpt-image-2", quality="high", notes="bridge test")
            self.assertTrue(ok, msg)
            ok2, msg2 = ledger_call.success(ep, frame=1, path=Path(td) / "missing.png")
            self.assertFalse(ok2)
            self.assertIn("candidate not found", msg2)

    def test_repair_arbiter_review_is_in_process(self):
        import batch_repair_arbiter
        import ledger_call
        with tempfile.TemporaryDirectory() as td:
            ep = self._ready_episode(td)
            prompt = Path(td) / "prompt.md"
            prompt.write_text("ordinary snapshot", encoding="utf-8")
            with self._no_spawn():
                ok, msg = ledger_call.begin(
                    ep, frame=1, kind="original", prompt_file=prompt, capture_id="CP01",
                    model="gpt-image-2", quality="high", notes="bridge test")
            self.assertTrue(ok, msg)
            canvas = json.loads((ep / "meta/production-ledger.json").read_text(encoding="utf-8"))["canvas"]
            candidate = Path(td) / "candidate.png"
            Image.new("RGB", (canvas["width"], canvas["height"]), (30, 40, 50)).save(candidate, "PNG")
            with self._no_spawn():
                ok, msg = ledger_call.success(ep, frame=1, path=candidate)
            self.assertTrue(ok, msg)
            with self._no_spawn():
                ok2, msg2 = batch_repair_arbiter.authorize_single_repair(ep, 1, "unit bridge test")
            self.assertTrue(ok2, msg2)
            data = json.loads((ep / "meta/production-ledger.json").read_text(encoding="utf-8"))
            self.assertEqual(data["frames"]["01"]["status"], "CONTENT_FAILED")

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


class ModelFallbackConvergenceTests(unittest.TestCase):
    def test_bridged_windows_image_worker_uses_disposable_no_os_sandbox_lane(self):
        with mock.patch.object(codex_subscription_image.os, "name", "nt"):
            self.assertEqual(
                codex_subscription_image.image_worker_sandbox_mode(bridged=True, has_references=False),
                "workspace-write",
            )
            self.assertEqual(
                codex_subscription_image.image_worker_sandbox_mode(bridged=False, has_references=True),
                "danger-full-access",
            )
            self.assertEqual(
                codex_subscription_image.image_worker_sandbox_mode(bridged=False, has_references=False),
                "workspace-write",
            )

    def test_subscription_worker_defaults_follow_yaml_policy(self):
        import inspect
        for func in (codex_subscription_image.worker_prompt, codex_subscription_image.invoke_codex):
            params = inspect.signature(func).parameters
            self.assertEqual(params["image_model"].default, image_model_policy.DEFAULT_MODEL)
            self.assertEqual(params["image_quality"].default, image_model_policy.DEFAULT_QUALITY)
            self.assertEqual(params["image_model"].default, codex_subscription_image.DEFAULT_IMAGE_MODEL)
            self.assertEqual(params["image_quality"].default, codex_subscription_image.DEFAULT_IMAGE_QUALITY)

    def test_orchestrator_runtime_request_fallback_follows_yaml_policy(self):
        import codex_auto_orchestrator
        with tempfile.TemporaryDirectory() as td:
            ep = Path(td)
            request = ep / "meta/runtime-request.json"
            request.parent.mkdir(parents=True)
            request.write_text(
                json.dumps({"story_input": {"mode": "auto_create"}, "image": {}}, ensure_ascii=False),
                encoding="utf-8",
            )
            block = codex_auto_orchestrator.runtime_request_block(ep)
            expected = f"requested={image_model_policy.DEFAULT_MODEL} quality={image_model_policy.DEFAULT_QUALITY}"
            self.assertIn(expected, block)
            self.assertIn("auto_create", block)


if __name__ == "__main__":
    unittest.main()
