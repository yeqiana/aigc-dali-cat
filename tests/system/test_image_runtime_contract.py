#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
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
import image_worker_pool
import production_ledger
import production_ledger_core
import production_ledger_persistence
import runtime_request
import episode_contract_persistence
import model_policy
import model_policy_persistence
import scheduler_core
import storage_config


class RuntimeRequestQualityTests(unittest.TestCase):
    def test_new_request_locks_model_and_quality(self):
        request = runtime_request.compile_request("全自动做一篇「比例合同测试」。")
        self.assertEqual(request["image_model"], image_model_policy.DEFAULT_MODEL)
        self.assertEqual(request["image_quality"], "high")
        self.assertEqual(request["image"]["model"], request["image_model"])
        self.assertEqual(request["image"]["quality"], request["image_quality"])
        self.assertEqual(runtime_request.validate_request(request), [])
        self.assertEqual(request["runtime"]["max_image_workers"], 5)

    def test_request_rejects_more_than_five_image_workers(self):
        request = runtime_request.compile_request("全自动做一篇「并发上限测试」。")
        request["runtime"]["max_image_workers"] = 6
        self.assertIn(
            "runtime.max_image_workers must be 1..5",
            runtime_request.validate_request(request),
        )

    def test_legacy_request_defaults_to_high_without_mutation(self):
        request = {"image": {"provider": "openai", "model": "gpt-image-2", "source": "system_default", "strict_model": False}}
        policy = image_model_policy.resolve_model(request=request)
        self.assertEqual(policy["quality"], "high")
        self.assertNotIn("image_quality", request)


class ImageModelMigrationTests(unittest.TestCase):
    def test_system_default_migration_updates_only_pending_inherited_work(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ep = root / "episodes" / "ep"
            (ep / "meta/runtime").mkdir(parents=True)
            request = runtime_request.compile_request("全自动做一篇「legacy migration test」。")
            request["request_id"] = "old-request"
            request["image_model"] = "gpt-image-2"
            request["image"]["model"] = "gpt-image-2"
            self.assertEqual(runtime_request.validate_request(request), [])
            bound_request = {"value": request}

            # Model Policy is a separate immutable contract. The explicit legacy
            # image operation may update the old Runtime Request, but must not
            # rewrite the already frozen Model Policy record.
            contract_records = {}
            save_contract = lambda _ep, contract_type, _rel, payload, **_kw: contract_records.__setitem__(contract_type, dict(payload))
            load_contract = lambda _ep, contract_type, **_kw: contract_records.get(contract_type)
            with mock.patch.object(episode_contract_persistence, "save", side_effect=save_contract), \
                    mock.patch.object(episode_contract_persistence, "load_latest", side_effect=load_contract), \
                    mock.patch.object(model_policy_persistence.runtime_workspace, "write_json",
                                      side_effect=AssertionError("mysql mode must not force a JSON projection")), \
                    mock.patch.object(runtime_request, "authority_for_episode",
                                      side_effect=lambda _ep: bound_request["value"]), \
                    mock.patch.object(runtime_request, "bind_request",
                                      side_effect=lambda path, _ep, force=False: bound_request.__setitem__(
                                          "value", runtime_request.read_json(path))), \
                    mock.patch.object(runtime_request, "REQUESTS_DIR", root / "runtime/requests"):
                frozen = model_policy.freeze_for_episode(ep)
                frozen_sha = frozen["policy_sha256"]
                queue_authority = {"value": {"items": [
                    {"id": "done", "frame": 1, "status": "generated", "model": "gpt-image-2", "strict_model": False},
                    {"id": "retry", "frame": 2, "status": "external_blocked", "model": "gpt-image-2", "strict_model": False,
                     "technical_failure_code": "IMAGE_BACKEND_ERROR", "last_error": "PROVIDER_CAPACITY: requested=gpt-image-2"},
                    {"id": "strict", "frame": 3, "status": "queued", "model": "gpt-image-2", "strict_model": True},
                ]}}
                with mock.patch.object(storage_config, "hot_state_config", return_value={"mode": "redis"}), \
                        mock.patch.object(scheduler_core.hot_state_bridge, "read",
                                          side_effect=lambda _ep, _kind: {
                                              "mode": "redis", "value": queue_authority["value"]}), \
                        mock.patch.object(scheduler_core.hot_state_bridge, "mirror",
                                          side_effect=lambda _ep, _kind, value: queue_authority.__setitem__(
                                              "value", json.loads(json.dumps(value)))):
                    scheduler_core.save_queue(ep, queue_authority["value"])
                    result = image_model_policy.migrate_system_default(ep)
                self.assertEqual(model_policy_persistence.load(ep)["policy_sha256"], frozen_sha)

            self.assertEqual(result["status"], "MIGRATED")
            migrated = bound_request["value"]
            self.assertEqual(migrated["image_model"], image_model_policy.DEFAULT_MODEL)
            queue = queue_authority["value"]["items"]
            self.assertEqual(queue[0]["model"], "gpt-image-2")
            self.assertEqual(queue[1]["model"], image_model_policy.DEFAULT_MODEL)
            self.assertEqual(queue[1]["technical_failure_code"], "PROVIDER_CAPACITY")
            self.assertEqual(queue[2]["model"], "gpt-image-2")
            self.assertEqual(result["queue_items_updated"], 1)
            self.assertEqual(result["technical_codes_reclassified"], 1)

    def test_explicit_model_migration_is_forbidden(self):
        with tempfile.TemporaryDirectory() as td:
            ep = Path(td)
            (ep / "meta").mkdir()
            request = runtime_request.compile_request(
                "全自动做一篇「strict migration test」，image=gpt-image-2。")
            self.assertEqual(runtime_request.validate_request(request), [])
            with mock.patch.object(runtime_request, "authority_for_episode", return_value=request):
                with self.assertRaisesRegex(ValueError, "IMAGE_MODEL_MIGRATION_FORBIDDEN"):
                    image_model_policy.migrate_system_default(ep)


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
    def setUp(self):
        self.ledger_authority = {}
        self._ledger_mode = mock.patch.object(
            production_ledger_persistence, "mode", return_value="mysql")
        self._ledger_persist = mock.patch.object(
            production_ledger_persistence, "persist_authority",
            side_effect=lambda ep, data: self.ledger_authority.__setitem__(
                str(Path(ep).resolve()), json.loads(json.dumps(data))),
        )
        self._ledger_load = mock.patch.object(
            production_ledger_persistence, "load_authority",
            side_effect=lambda ep: json.loads(json.dumps(
                self.ledger_authority[str(Path(ep).resolve())]))
                if str(Path(ep).resolve()) in self.ledger_authority else None,
        )
        self._ledger_mode.start(); self._ledger_persist.start(); self._ledger_load.start()
        self.addCleanup(self._ledger_mode.stop)
        self.addCleanup(self._ledger_persist.stop)
        self.addCleanup(self._ledger_load.stop)

    def _read_ledger_authority(self, ep: Path) -> dict:
        return production_ledger.load_authority(ep)

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

    def test_worker_backend_return_without_artifact_is_explicit_technical_failure(self):
        with tempfile.TemporaryDirectory() as td:
            ep = self._ready_episode(td)
            prompt = Path(td) / "prompt.md"
            prompt.write_text("ordinary snapshot", encoding="utf-8")
            item = self._queue_item(prompt)
            bound_contracts = {}
            def save_contract(_ep, contract_type, _rel, payload, **_kwargs):
                bound_contracts[(str(Path(_ep).resolve()), contract_type)] = json.loads(json.dumps(payload))
                return {"mode": "test", "mysql_written": True}
            def load_contract(_ep, contract_type, **_kwargs):
                return bound_contracts.get((str(Path(_ep).resolve()), contract_type))
            with mock.patch.object(episode_contract_persistence, "save", side_effect=save_contract), \
                    mock.patch.object(episode_contract_persistence, "load_latest", side_effect=load_contract):
                model_policy.freeze_for_episode(ep)
                with mock.patch.object(image_worker_pool.resource_library, "ensure_fresh"), \
                    mock.patch.object(image_worker_pool.runtime_router, "detect", return_value=("CODEX", "test")), \
                    mock.patch.object(image_worker_pool.runtime_router, "image_execution_runtime", return_value=("CODEX", "test")), \
                    mock.patch.object(image_worker_pool.prompt_package, "compile_frame", return_value={
                        "package_sha256": "a" * 64, "scene_prompt_sha256": "b" * 64, "frame_contract_sha256": "c" * 64,
                        "scene_prompt": "A valid frozen scene prompt.",
                        "frame_prompt_contract": "A valid frame contract."}), \
                    mock.patch.object(image_worker_pool, "_canonical_controller_request", return_value={
                        "request": {"request_fingerprint": "d" * 64},
                        "controller_call_id": "controller-test-call",
                        "controller_output_sha256": "e" * 64,
                        "request_fingerprint": "d" * 64}), \
                    mock.patch.object(image_worker_pool.image_payload_transport,
                                      "payload_capability_preflight", return_value={
                        "status": "PASS", "provider": "fake", "runner": "fake-runner",
                        "transport_model": "fake-transport", "transport_effort": "low"}), \
                    mock.patch.object(image_worker_pool.backend, "generate_for_frame", return_value={"backend": "fake"}), \
                    mock.patch.object(image_worker_pool.production_recovery, "write_lifecycle"), \
                    mock.patch.object(image_worker_pool.runtime_trace, "start_span", return_value="span"), \
                    mock.patch.object(image_worker_pool.runtime_trace, "end_span"), \
                    mock.patch.object(image_worker_pool.raw_candidate_budget, "claim", return_value=(True, {"decision": "ALLOW"})), \
                    mock.patch.object(image_worker_pool.raw_candidate_budget, "release", return_value=(True, {"decision": "RELEASED"})) as release, \
                    mock.patch.object(image_worker_pool.raw_candidate_budget, "commit", side_effect=AssertionError("missing output must not consume budget")):
                    result = image_worker_pool.execute(ep, item, 30, "codex")
            self.assertEqual(result["returncode"], 95)
            self.assertIn("IMAGE_BACKEND_NO_OUTPUT", result["stdout"])
            self.assertIsNone(result["output"])
            release.assert_called_once()
            self.assertEqual(image_scheduler.classify_error(result["stdout"]), "IMAGE_BACKEND_NO_OUTPUT")

    def test_ledger_bridge_begin_and_tech_fail_are_in_process(self):
        with tempfile.TemporaryDirectory() as td:
            ep = self._ready_episode(td)
            prompt = Path(td) / "prompt.md"
            prompt.write_text("ordinary snapshot", encoding="utf-8")
            item = self._queue_item(prompt)
            with self._no_spawn():
                ok, msg = image_scheduler.ledger_begin(ep, item)
            self.assertTrue(ok, msg)
            data = self._read_ledger_authority(ep)
            self.assertEqual(data["frames"]["01"]["status"], "GENERATING")
            self.assertEqual(data["frames"]["01"]["attempts"][-1]["provider_attempt"]["status"], "NOT_INVOKED")
            with self._no_spawn():
                ok2, msg2 = image_scheduler.ledger_begin(ep, item)
            self.assertFalse(ok2)
            self.assertIn("cannot begin original", msg2)
            with self._no_spawn():
                image_scheduler.ledger_tech_fail(ep, item, "WORKER_FAILED", "boom")
            data = self._read_ledger_authority(ep)
            self.assertEqual(data["frames"]["01"]["status"], "TECH_FAILED")
            self.assertEqual(data["frames"]["01"]["attempts"][-1]["provider_attempt"]["status"], "NOT_INVOKED")

    def test_ledger_tech_fail_records_invoked_provider_attempt_without_success_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            ep = self._ready_episode(td)
            prompt = Path(td) / "prompt.md"
            prompt.write_text("ordinary snapshot", encoding="utf-8")
            item = self._queue_item(prompt)
            item["execution"] = {"runner_request_id": "runner-123"}
            with self._no_spawn():
                ok, msg = image_scheduler.ledger_begin(ep, item)
                self.assertTrue(ok, msg)
                image_scheduler.ledger_tech_fail(ep, item, "PROVIDER_CAPACITY", "capacity")
            data = self._read_ledger_authority(ep)
            receipt = data["frames"]["01"]["attempts"][-1]["provider_attempt"]
            self.assertEqual(receipt["status"], "INVOKED")
            self.assertEqual(receipt["runner_request_id"], "runner-123")
            self.assertEqual(receipt["failure_code"], "PROVIDER_CAPACITY")

    def test_batch_scheduler_ledger_begin_is_in_process(self):
        import batch_scheduler
        with tempfile.TemporaryDirectory() as td:
            ep = self._ready_episode(td)
            prompt = Path(td) / "prompt.md"
            prompt.write_text("ordinary snapshot", encoding="utf-8")
            with self._no_spawn():
                ok, msg = batch_scheduler.ledger_begin(ep, self._queue_item(prompt))
            self.assertTrue(ok, msg)
            data = self._read_ledger_authority(ep)
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
            canvas = self._read_ledger_authority(ep)["canvas"]
            candidate = Path(td) / "candidate.png"
            Image.new("RGB", (canvas["width"], canvas["height"]), (30, 40, 50)).save(candidate, "PNG")
            with self._no_spawn():
                ok, msg = ledger_call.success(ep, frame=1, path=candidate)
            self.assertTrue(ok, msg)
            with self._no_spawn():
                ok2, msg2 = batch_repair_arbiter.authorize_single_repair(ep, 1, "unit bridge test")
            self.assertTrue(ok2, msg2)
            data = self._read_ledger_authority(ep)
            self.assertEqual(data["frames"]["01"]["status"], "CONTENT_FAILED")

    def test_worker_consumes_exact_canvas_and_high_quality(self):
        prompt = codex_subscription_image.worker_prompt("scene", [], "1080x1920")
        self.assertIn("quality=high", prompt)
        self.assertIn("canvas=1080x1920 exactly", prompt)
        self.assertEqual(codex_subscription_image.provider_size(1080, 1920), "1080x1920")

    def test_only_canvas_aspect_failure_may_use_shared_technical_retry_slot(self):
        self.assertEqual(image_scheduler.classify_error("NORMALIZE_REVIEW: manual review"), "NORMALIZE_REVIEW")
        self.assertEqual(image_scheduler.classify_error("ASPECT_RATIO_MISMATCH: reject"), "ASPECT_RATIO_MISMATCH")
        self.assertIn("NORMALIZE_REVIEW", image_scheduler.NON_REGENERATING_FAILURE_CODES)
        self.assertIn("IMAGE_QUALITY_CONTRACT_MISMATCH", image_scheduler.NON_REGENERATING_FAILURE_CODES)
        self.assertIn("ASPECT_RATIO_MISMATCH", image_scheduler.RETRYABLE_TECH_CODES)
        self.assertNotIn("ASPECT_RATIO_MISMATCH", image_scheduler.NON_REGENERATING_FAILURE_CODES)

    def test_structured_connect_failure_does_not_masquerade_as_timeout(self):
        historical = ('http/request send failed http_method="POST" '
                      'error_is_timeout=false error_is_connect=true error=error sending request')
        self.assertEqual(image_scheduler.classify_error(historical), "NETWORK_CONNECT")
        self.assertEqual(
            image_scheduler.classify_error("error_is_timeout=true error_is_connect=false request failed"),
            "TIMEOUT",
        )

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
            data = self._read_ledger_authority(ep)
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
    def test_default_model_has_bounded_non_strict_availability_fallbacks(self):
        self.assertEqual(image_model_policy.DEFAULT_MODEL, "gpt-image-2.5-flare")
        self.assertEqual(image_model_policy.FALLBACK_MODELS,
                         ("gpt-image-2.5-sunburst", "gpt-image-2"))
        self.assertEqual(image_model_policy.next_fallback_model("gpt-image-2.5-flare"),
                         "gpt-image-2.5-sunburst")
        self.assertEqual(image_model_policy.next_fallback_model("gpt-image-2.5-sunburst"),
                         "gpt-image-2")
        self.assertIsNone(image_model_policy.next_fallback_model("gpt-image-2"))
        self.assertIsNone(image_model_policy.next_fallback_model(
            "gpt-image-2.5-flare", strict_model=True))

    def test_image_runtime_preflight_direct_requires_auth_and_writable_generated_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source-home"
            worker = root / "worker-home"
            source.mkdir(); worker.mkdir()
            with self.assertRaises(codex_subscription_image.BackendError) as ctx:
                codex_subscription_image.image_runtime_preflight(
                    bridged=False, source_home=source, worker_home=worker)
            self.assertIn("auth.json", str(ctx.exception))

            (source / "auth.json").write_text("{}", encoding="utf-8")
            result = codex_subscription_image.image_runtime_preflight(
                bridged=False, source_home=source, worker_home=worker)
            self.assertEqual(result["transport"], "direct")
            self.assertTrue(result["auth_context_present"])
            self.assertTrue(result["generated_images_writable"])
            self.assertTrue((worker / "generated_images").is_dir())

    def test_invoke_codex_fails_preflight_before_provider_call(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prompt = root / "prompt.txt"
            prompt.write_text("one frame", encoding="utf-8")
            source_home = root / "source-home"
            source_home.mkdir()
            workdir = root / "work"
            workdir.mkdir()
            workspace_cm = mock.MagicMock()
            workspace_cm.__enter__.return_value = str(workdir)
            workspace_cm.__exit__.return_value = False
            with mock.patch.dict(codex_subscription_image.os.environ, {"CODEX_HOME": str(source_home)}, clear=False), \
                 mock.patch.object(codex_subscription_image, "resolve_codex", return_value=root / "codex.exe"), \
                 mock.patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=False), \
                 mock.patch.object(codex_subscription_image.codex_user_runner, "workspace", return_value=workspace_cm), \
                 mock.patch.object(codex_subscription_image.codex_user_runner, "run_codex") as run_codex:
                with self.assertRaises(codex_subscription_image.BackendError) as ctx:
                    codex_subscription_image.invoke_codex(
                        prompt, [], root / "raw.png", root / "attempt.log",
                        "1080x1350", 30, None)
            self.assertIn("GENERATION_ATTEMPT_LEASE_REQUIRED", str(ctx.exception))
            run_codex.assert_not_called()

    def test_image_runtime_preflight_bridge_uses_runner_health_without_credential_contents(self):
        health = {
            "codex_available": True,
            "codex_home_accessible": True,
            "codex_auth_present": True,
        }
        with mock.patch.object(codex_subscription_image.codex_user_runner, "runner_health", return_value=health):
            result = codex_subscription_image.image_runtime_preflight(bridged=True)
        self.assertEqual(result["transport"], "user_runner")
        self.assertTrue(result["auth_context_present"])
        self.assertNotIn("auth", json.dumps(result).lower().replace("auth_context_present", ""))

        health["codex_auth_present"] = False
        with mock.patch.object(codex_subscription_image.codex_user_runner, "runner_health", return_value=health), \
             mock.patch.object(codex_subscription_image, "_legacy_bridge_auth_probe") as legacy_probe:
            with self.assertRaises(codex_subscription_image.BackendError):
                codex_subscription_image.image_runtime_preflight(bridged=True)
        legacy_probe.assert_not_called()

    def test_image_runtime_preflight_bridge_probes_legacy_runner_missing_auth_bit(self):
        health = {
            "protocol_revision": 2,
            "codex_available": True,
            "codex_home_accessible": True,
        }
        completed = subprocess.CompletedProcess(["codex", "login", "status"], 0, "Logged in using ChatGPT", None)
        with mock.patch.object(codex_subscription_image.codex_user_runner, "runner_health", return_value=health), \
             mock.patch.object(codex_subscription_image.codex_user_runner, "run_codex", return_value=completed) as run_codex:
            result = codex_subscription_image.image_runtime_preflight(bridged=True)
        self.assertTrue(result["auth_context_present"])
        run_codex.assert_called_once()

        logged_out = subprocess.CompletedProcess(["codex", "login", "status"], 1, "Not logged in", None)
        with mock.patch.object(codex_subscription_image.codex_user_runner, "runner_health", return_value=health), \
             mock.patch.object(codex_subscription_image.codex_user_runner, "run_codex", return_value=logged_out):
            with self.assertRaises(codex_subscription_image.BackendError):
                codex_subscription_image.image_runtime_preflight(bridged=True)

    def test_bridged_windows_image_worker_uses_disposable_no_os_sandbox_lane(self):
        with mock.patch.object(codex_subscription_image.os, "name", "nt"):
            self.assertEqual(
                codex_subscription_image.image_worker_sandbox_mode(bridged=True, has_references=False),
                "danger-full-access",
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
            request = runtime_request.compile_request("全自动做一篇「orchestrator policy fixture」。")
            with mock.patch.object(runtime_request, "authority_for_episode", return_value=request):
                block = codex_auto_orchestrator.runtime_request_block(ep)
            expected = f"requested={image_model_policy.DEFAULT_MODEL} quality={image_model_policy.DEFAULT_QUALITY}"
            self.assertIn(expected, block)
            self.assertIn("auto_create", block)


if __name__ == "__main__":
    unittest.main()
