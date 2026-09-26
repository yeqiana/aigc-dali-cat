#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SYSTEM = Path(__file__).resolve().parent
ROOT = SYSTEM.parents[1]
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import caption_image_audit
import codex_subscription_image
import codex_user_runner
import image_provider_runtime
import image_worker_pool
import next_action
import product_image_import
import product_review_adapter
import product_runtime_adapter
import raw_candidate_budget
import release_preflight
import resource_library
import runtime_checkpoint
import runtime_provenance
import runtime_router
import story_review
import visual_review_legacy


class ProductRuntimeFirstTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = os.environ.get("STORY_OS_RUNTIME")
        self.image_runtime = os.environ.get("STORY_OS_IMAGE_RUNTIME")
        self.api_key = os.environ.get("OPENAI_API_KEY")
        os.environ.pop("STORY_OS_RUNTIME", None)
        os.environ.pop("STORY_OS_IMAGE_RUNTIME", None)
        os.environ.pop("OPENAI_API_KEY", None)

    def tearDown(self) -> None:
        if self.runtime is None:
            os.environ.pop("STORY_OS_RUNTIME", None)
        else:
            os.environ["STORY_OS_RUNTIME"] = self.runtime
        if self.image_runtime is None:
            os.environ.pop("STORY_OS_IMAGE_RUNTIME", None)
        else:
            os.environ["STORY_OS_IMAGE_RUNTIME"] = self.image_runtime
        if self.api_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = self.api_key

    def temp_episode(self):
        base = ROOT / "episodes" / "_tests"
        base.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(prefix="v261-product-runtime-", dir=base)

    def test_default_runtime_is_work(self) -> None:
        runtime, reason = runtime_router.detect()
        self.assertEqual(runtime, "WORK")
        self.assertIn("preferred_runtime", reason)
        caps = runtime_router.capabilities()
        self.assertEqual(caps["effective_runtime"], "WORK")
        self.assertFalse(caps["local_codex_spawn_allowed"])
        self.assertEqual(caps["image_execution_runtime"], "CODEX")
        self.assertEqual(caps["codex_image_controller_model"], "gpt-5.6-luna")
        self.assertEqual(caps["codex_image_reasoning_effort"], "medium")
        self.assertTrue(caps["local_codex_image_spawn_allowed"])
        self.assertEqual(caps["text_review_runtime"], "WORK")
        self.assertEqual(caps["vision_review_runtime"], "CODEX")
        self.assertEqual(caps["governance_review_runtime"], "WORK")
        self.assertTrue(caps["local_codex_vision_spawn_allowed"])

    def test_default_runtime_falls_back_to_codex_when_webcodex_is_unavailable(self) -> None:
        with mock.patch.dict(os.environ, {
            "STORY_OS_WEBCODEX_AVAILABLE": "0",
        }, clear=False), mock.patch.object(runtime_router, "_codex_cli_path", return_value="C:/fake/codex.exe"):
            runtime, reason = runtime_router.detect()
            caps = runtime_router.capabilities()
        self.assertEqual(runtime, "CODEX")
        self.assertIn("Codex CLI fallback", reason)
        self.assertEqual(caps["effective_runtime"], "CODEX")
        self.assertTrue(caps["codex_fallback_active"])
        self.assertFalse(caps["webcodex_detected"])
        self.assertTrue(caps["local_codex_spawn_allowed"])

    def test_default_runtime_stays_work_when_webcodex_is_unavailable_without_codex(self) -> None:
        with mock.patch.dict(os.environ, {
            "STORY_OS_WEBCODEX_AVAILABLE": "0",
        }, clear=False), mock.patch.object(runtime_router, "_codex_cli_path", return_value=None):
            runtime, reason = runtime_router.detect()
        self.assertEqual(runtime, "WORK")
        self.assertIn("preferred_runtime", reason)

    def test_explicit_work_override_disables_automatic_codex_fallback(self) -> None:
        with mock.patch.dict(os.environ, {
            "STORY_OS_RUNTIME": "WORK",
            "STORY_OS_WEBCODEX_AVAILABLE": "0",
        }, clear=False), mock.patch.object(runtime_router, "_codex_cli_path", return_value="C:/fake/codex.exe"):
            runtime, reason = runtime_router.detect()
        self.assertEqual(runtime, "WORK")
        self.assertEqual(reason, "STORY_OS_RUNTIME override")

    def test_codex_requires_explicit_runtime_or_explicit_call(self) -> None:
        os.environ["STORY_OS_RUNTIME"] = "WORK"
        self.assertFalse(runtime_router.local_codex_allowed())
        self.assertTrue(runtime_router.local_codex_allowed(explicit=True))
        self.assertTrue(runtime_router.local_codex_image_allowed())
        self.assertTrue(runtime_router.local_codex_vision_allowed())
        os.environ["STORY_OS_RUNTIME"] = "CODEX"
        runtime, _ = runtime_router.detect()
        self.assertEqual(runtime, "CODEX")
        self.assertTrue(runtime_router.local_codex_allowed())

    def test_work_image_runtime_can_resolve_codex_without_full_codex_runtime(self) -> None:
        os.environ["STORY_OS_RUNTIME"] = "WORK"
        os.environ["STORY_OS_IMAGE_RUNTIME"] = "CODEX"
        with tempfile.TemporaryDirectory(prefix="v261-no-desktop-codex-") as td:
            fake_codex = Path(td) / "codex.exe"
            fake_codex.write_bytes(b"fake-codex")
            with mock.patch.dict(os.environ, {"LOCALAPPDATA": td, "CODEX_EXE": ""}, clear=False), \
                 mock.patch.object(codex_user_runner, "resolve_codex", return_value=(fake_codex, "runner_resolved")), \
                 mock.patch.object(codex_user_runner, "codex_version", return_value="codex-cli 0.153.4"):
                resolved = codex_subscription_image.resolve_codex(None)
        self.assertEqual(resolved, fake_codex.resolve())

    def test_queue_model_strictness_survives_internal_forwarding(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            default_policy = image_worker_pool.model_policy_for_item(ep, {"model": "gpt-image-2", "quality": "high"})
            self.assertFalse(default_policy["strict_model"])
            strict_policy = image_worker_pool.model_policy_for_item(ep, {"model": "gpt-image-2", "quality": "high", "strict_model": True})
            self.assertTrue(strict_policy["strict_model"])

    def test_work_isolated_provenance_is_valid(self) -> None:
        prov = runtime_provenance.build_critic_provenance("WORK", attempt=1)
        self.assertEqual(prov["runtime"], "WORK_ISOLATED")
        self.assertEqual(runtime_provenance.validate_critic_provenance(prov), [])
        h = "a" * 64
        payload = {
            "schema_version": 1,
            "story_os_version": "2.6.1",
            "story_sha256": h,
            "storyboard_sha256": h,
            "revision_count": 0,
            "critic_provenance": prov,
            "contract": {key: "x" for key in story_review.CONTRACT_FIELDS},
            "blind_retell": {key: "x" for key in story_review.BLIND_FIELDS},
            "hard_checks": {key: True for key in story_review.HARD_CHECKS},
            "issue_codes": [],
            "summary": {"passed": True},
        }
        payload["contract"]["ending_recontextualization"] = ["a", "b", "c"]
        self.assertEqual(
            story_review.validate_payload(payload, story_sha=h, storyboard_sha=h, version="2.6.1"),
            [],
        )

    def test_legacy_visual_review_work_branch_never_calls_codex(self) -> None:
        os.environ["STORY_OS_RUNTIME"] = "WORK"
        with self.temp_episode() as td:
            ep = Path(td)
            (ep / "meta").mkdir(parents=True, exist_ok=True)
            rel_ep = ep.relative_to(ROOT)
            items = []
            for idx, name in enumerate(("A", "B", "C"), 1):
                image = ep / f"cal-{idx}.png"
                image.write_bytes(b"legacy-visual-smoke-image")
                items.append({
                    "id": name,
                    "role": f"legacy-{idx}",
                    "path": (rel_ep / image.name).as_posix(),
                    "decision": "passed",
                })
            gates = {
                "tool_version": "2.0.3.2",
                "visual_profile": {"mode": "default", "profile_id": "M00", "capture_profile": "auto"},
                "visual": {"calibration": {"items": items}},
            }
            (ep / "meta/story-gates.json").write_text(json.dumps(gates, ensure_ascii=False), encoding="utf-8")
            with mock.patch.object(visual_review_legacy, "resolve_codex", side_effect=AssertionError("Codex must not be called")), \
                 mock.patch("builtins.print"):
                rc = visual_review_legacy.run_critic(ep, attempt=1, codex_raw=None, timeout=30)
            self.assertEqual(rc, product_review_adapter.HOST_ACTION_REQUIRED_RC)
            self.assertTrue(product_review_adapter.request_path(ep, "visual-profile-legacy", attempt=1).is_file())

    def test_legacy_visual_review_accepts_work_isolated(self) -> None:
        h = "b" * 64
        assets = [{"id": x, "sha256": h} for x in ("A", "B", "C")]
        payload = {
            "schema_version": 1,
            "story_os_version": "2.6.1",
            "profile_id": "M00",
            "profile_sha256": h,
            "critic_provenance": runtime_provenance.build_critic_provenance("WORK", attempt=1),
            "calibration": [
                {"id": x, "sha256": h, "checks": {k: True for k in visual_review_legacy.CHECKS}, "issues": []}
                for x in ("A", "B", "C")
            ],
            "issue_codes": [],
            "summary": {"passed": True},
        }
        self.assertEqual(
            visual_review_legacy.validate_payload(payload, profile_id="M00", profile_sha=h, assets=assets, version="2.6.1"),
            [],
        )

    def test_codex_image_controller_is_luna_medium(self) -> None:
        args = codex_subscription_image.controller_args()
        self.assertEqual(args[:4], ['-m', 'gpt-5.6-luna', '-c', 'model_reasoning_effort="medium"'])
        self.assertIn('model_provider="openai"', args)
        self.assertIn('openai_base_url="https://chatgpt.com/backend-api/codex"', args)

    def test_resource_selection_stale_guard_rebuilds_wrong_location(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            (ep / "meta").mkdir(parents=True, exist_ok=True)
            (ep / "meta/character-contract.json").write_text(json.dumps({
                "era": {"bucket": "modern_2020s"},
                "entry": {"type": "travel"},
                "scene": {"primary_category": "village_home", "primary_place": "川西山谷小镇普通民宿"},
                "cast": {"size": 2},
            }, ensure_ascii=False), encoding="utf-8")
            (ep / "meta/resource-selection.json").write_text(json.dumps({
                "schema_version": 1,
                "source_tags": ["village_home"],
                "selected": [{"id": "LOC_NORTHWEST_VILLAGE", "tags": ["西北农村"]}],
            }, ensure_ascii=False), encoding="utf-8")
            self.assertFalse(resource_library.is_fresh(ep))
            rebuilt = resource_library.ensure_fresh(ep)
            self.assertTrue(resource_library.is_fresh(ep))
            self.assertEqual(rebuilt["resolver_version"], resource_library.RESOLVER_VERSION)
            self.assertNotIn("LOC_NORTHWEST_VILLAGE", {x.get("id") for x in rebuilt.get("selected") or []})

    def test_work_authoring_uses_codex_for_images_only(self) -> None:
        os.environ["STORY_OS_RUNTIME"] = "WORK"
        decision = image_provider_runtime.select_batch_provider(5)
        self.assertEqual(decision["provider"], "codex_subscription")
        self.assertEqual(runtime_router.detect()[0], "WORK")
        self.assertFalse(runtime_router.local_codex_allowed())
        self.assertTrue(runtime_router.local_codex_image_allowed())

    def test_codex_image_runtime_wins_even_if_api_key_exists(self) -> None:
        os.environ["STORY_OS_RUNTIME"] = "WORK"
        os.environ["OPENAI_API_KEY"] = "test-only-not-used"
        decision = image_provider_runtime.select_batch_provider(5)
        self.assertEqual(decision["provider"], "codex_subscription")

    def test_product_image_runtime_can_be_explicitly_restored(self) -> None:
        os.environ["STORY_OS_RUNTIME"] = "WORK"
        os.environ["STORY_OS_IMAGE_RUNTIME"] = "PRODUCT_RUNTIME"
        decision = image_provider_runtime.select_batch_provider(5)
        self.assertEqual(decision["provider"], "product_runtime_image")
        self.assertTrue(decision["host_action_required"])
        self.assertFalse(decision["local_codex_fallback"])

    def test_full_codex_runtime_still_supports_codex_images(self) -> None:
        os.environ["STORY_OS_RUNTIME"] = "CODEX"
        decision = image_provider_runtime.select_batch_provider(5)
        self.assertEqual(decision["provider"], "codex_subscription")

    def test_runtime_dag_uses_generic_scoped_model(self) -> None:
        dag = json.loads((ROOT / "runtimes/runtime-dag.json").read_text(encoding="utf-8"))
        model_steps = [x for x in dag["steps"] if x["id"] != "INCREMENTAL_PLAN"]
        self.assertTrue(model_steps)
        self.assertTrue(all(x["executor"] == "scoped_model" for x in model_steps))

    def test_product_host_action_code_is_not_success(self) -> None:
        self.assertEqual(product_runtime_adapter.HOST_ACTION_REQUIRED_RC, 20)
        self.assertNotEqual(product_runtime_adapter.HOST_ACTION_REQUIRED_RC, 0)
        self.assertIn("HOST_WAIT", runtime_checkpoint.VALID_STEP_STATUS)

    def test_host_request_is_idempotent_and_historical(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            (ep / "meta").mkdir(parents=True, exist_ok=True)
            (ep / "meta/episode-state.json").write_text(
                json.dumps({"current_state": "IDEA_LOCKED"}), encoding="utf-8"
            )
            first = product_runtime_adapter.build_request(
                ep, runtime="WORK", mode="full_auto", resume=False, source="test"
            )
            second = product_runtime_adapter.build_request(
                ep, runtime="WORK", mode="full_auto", resume=False, source="test"
            )
            self.assertEqual(first["request_id"], second["request_id"])
            history = product_runtime_adapter.host_request_persistence.list_all(ep)
            self.assertEqual(len(history), 1)
            final = product_runtime_adapter.mark_complete(ep, first["request_id"], result={"ok": True})
            self.assertEqual(final["status"], "FINALIZED")
            current = product_runtime_adapter._read_current_request(ep)
            self.assertEqual(current["status"], "FINALIZED")

    def test_stale_preimage_committed_snapshot_routes_back_to_task_set(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            (ep / "meta/runtime").mkdir(parents=True, exist_ok=True)
            (ep / "meta/episode-state.json").write_text(
                json.dumps({"current_state": "STORYBOARD_LOCKED"}), encoding="utf-8"
            )
            (ep / "meta/runtime/preimage-task-state.json").write_text(
                json.dumps({"snapshot_id": "old", "tasks": {}}), encoding="utf-8"
            )
            (ep / "meta/runtime/preimage-committed-snapshot.json").write_text(
                json.dumps({"snapshot_id": "old", "authority_sha256": {}}), encoding="utf-8"
            )
            with mock.patch.object(product_runtime_adapter.preproduction_handoff, "verify", return_value=["stale handoff"]), \
                    mock.patch.object(product_runtime_adapter.preimage_authority_snapshot, "stale", return_value=True):
                step, target = product_runtime_adapter.next_host_step(ep)
            self.assertEqual((step, target), ("PREIMAGE_TASK_SET", None))

    def test_stale_frame_contract_index_routes_to_deterministic_recompile(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            (ep / "meta/runtime/contracts").mkdir(parents=True, exist_ok=True)
            (ep / "meta/episode-state.json").write_text(
                json.dumps({"current_state": "STORYBOARD_LOCKED"}), encoding="utf-8"
            )
            (ep / "meta/runtime/preimage-authority-barrier.json").write_text("{}", encoding="utf-8")
            (ep / "meta/runtime/contracts/frame-contract-index.json").write_text("{}", encoding="utf-8")
            (ep / "meta/preproduction-handoff.json").write_text("{}", encoding="utf-8")
            with mock.patch.object(product_runtime_adapter.preproduction_handoff, "verify", return_value=["stale handoff"]), \
                    mock.patch.object(product_runtime_adapter.frame_contract, "verify_all", return_value=["frame 02 stale"]):
                step, target = product_runtime_adapter.next_host_step(ep)
            self.assertEqual((step, target), ("PREIMAGE_FRAME_CONTRACT_COMPILE", None))
            with mock.patch.object(product_runtime_adapter.preproduction_handoff, "verify", return_value=["stale handoff"]), \
                    mock.patch.object(product_runtime_adapter.frame_contract, "verify_all", return_value=[]):
                step, target = product_runtime_adapter.next_host_step(ep)
            self.assertEqual((step, target), ("PREIMAGE_VERIFY", None))

    def test_preimage_verify_host_request_reconciles_from_valid_handoff(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            meta = ep / "meta"
            history = ep / product_runtime_adapter.REQUEST_HISTORY_REL
            history.mkdir(parents=True, exist_ok=True)
            (meta / "episode-state.json").write_text(
                json.dumps({"current_state": "STORYBOARD_LOCKED"}), encoding="utf-8"
            )
            (meta / "preproduction-handoff.json").write_text("{}", encoding="utf-8")
            request_id = "host-preimage-verify-test"
            request = {
                "request_id": request_id,
                "status": "HOST_ACTION_REQUIRED",
                "next_step": "PREIMAGE_VERIFY",
                "target_state": None,
            }
            (history / f"{request_id}.json").write_text(json.dumps(request), encoding="utf-8")
            (ep / product_runtime_adapter.REQUEST_REL).write_text(json.dumps(request), encoding="utf-8")
            with mock.patch.object(product_runtime_adapter.preproduction_handoff, "verify", return_value=[]):
                reconciled = product_runtime_adapter.reconcile(ep)
            self.assertEqual(reconciled["status"], "FINALIZED")
            current = product_runtime_adapter._read_current_request(ep)
            self.assertEqual(current["status"], "FINALIZED")

    def test_visual_product_review_is_legacy_residue_when_codex_vision_owns_pixels(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            review_dir = ep / "meta/runtime/reviews"
            review_dir.mkdir(parents=True, exist_ok=True)
            request = {
                "status": "AWAITING_PRODUCT_REVIEW",
                "review_kind": "visual-lock-baseline",
                "created_at": "2026-09-12T13:05:05+08:00",
            }
            (review_dir / "visual-lock-baseline-request.json").write_text(
                json.dumps(request), encoding="utf-8"
            )
            self.assertIsNone(next_action.pending_product_review(ep, current_state="STORYBOARD_LOCKED"))
            self.assertIsNone(next_action.pending_product_review(ep, current_state="VISUAL_CALIBRATED"))

    def test_pending_story_review_outranks_stale_preimage_handoff(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            meta = ep / "meta"
            review_dir = meta / "runtime/reviews"
            review_dir.mkdir(parents=True, exist_ok=True)
            (meta / "episode-state.json").write_text(
                json.dumps({"current_state": "STORYBOARD_LOCKED"}), encoding="utf-8"
            )
            request = {
                "status": "AWAITING_PRODUCT_REVIEW",
                "review_kind": "story-semantic",
                "created_at": "2026-09-14T18:06:05+08:00",
                "candidate_path": "episodes/example/meta/.story-semantic-review.candidate.json",
            }
            (review_dir / "story-semantic-request.json").write_text(
                json.dumps(request), encoding="utf-8"
            )
            with mock.patch.object(next_action.product_runtime_adapter, "reconcile", return_value={}), \
                    mock.patch.object(next_action, "_handoff_valid", return_value=False), \
                    mock.patch("scheduler_core.progress", return_value={}):
                derived = next_action.derive(ep)
            self.assertEqual(derived["action"], "PRODUCT_REVIEW")
            self.assertEqual(derived["review_kind"], "story-semantic")
            self.assertIn("story-semantic-request.json", derived["request_path"])

    def test_product_runtime_request_uses_webcodex_workspace_provider(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            (ep / "meta").mkdir(parents=True, exist_ok=True)
            (ep / "meta/episode-state.json").write_text(
                json.dumps({"current_state": "IDEA_LOCKED"}), encoding="utf-8"
            )
            req = product_runtime_adapter.build_request(
                ep, runtime="WORK", mode="full_auto", resume=False, source="test"
            )
            self.assertEqual(req["runtime"], "WORK")
            self.assertEqual(req["host_contract"]["workspace_provider"], "webcodex")
            self.assertEqual(req["host_contract"]["workspace_transport"], "WEBCODEX")
            self.assertEqual(req["host_contract"]["workspace_execution_mode"], "host_mcp_runner")
            self.assertTrue(req["host_contract"]["workspace_host_managed"])
            self.assertTrue(req["host_contract"]["webcodex_allowed"])
            with self.assertRaises(ValueError):
                product_runtime_adapter.build_request(
                    ep, runtime="WEB", mode="full_auto", resume=False, source="test"
                )

    def test_product_review_request_uses_webcodex_workspace_provider(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            (ep / "meta").mkdir(parents=True, exist_ok=True)
            source = ep / "source.txt"
            source.write_text("frozen", encoding="utf-8")
            candidate = ep / "meta/candidate.json"
            req = product_review_adapter.prepare(
                ep,
                kind="workspace-review",
                runtime="WORK",
                attempt=1,
                prompt="review frozen source",
                source_paths=[source],
                candidate_path=candidate,
            )
            self.assertEqual(req["runtime"], "WORK")
            self.assertEqual(req["critic_runtime"], "WORK_ISOLATED")
            self.assertEqual(req["workspace_provider"], "webcodex")
            self.assertEqual(req["workspace_transport"], "WEBCODEX")
            self.assertEqual(req["review_execution_contract"]["workspace_provider"], "webcodex")
            self.assertTrue(req["review_execution_contract"]["webcodex_allowed"])
            self.assertTrue(req["review_execution_contract"]["fresh_product_review_turn_required"])
            with self.assertRaises(product_review_adapter.ProductReviewError):
                product_review_adapter.prepare(
                    ep,
                    kind="web-review-disabled",
                    runtime="WEB",
                    attempt=1,
                    prompt="must reject web",
                    source_paths=[source],
                    candidate_path=ep / "meta/web-candidate.json",
                )

    def test_product_review_finalize_emits_webcodex_provider_provenance(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            (ep / "meta").mkdir(parents=True, exist_ok=True)
            source = ep / "source.txt"
            source.write_text("frozen", encoding="utf-8")
            candidate = ep / "meta/candidate.json"
            product_review_adapter.prepare(
                ep,
                kind="workspace-finalize",
                runtime="WORK",
                attempt=1,
                prompt="review frozen source",
                source_paths=[source],
                candidate_path=candidate,
            )
            candidate.write_text(json.dumps({"summary": {"passed": True}}), encoding="utf-8")
            payload, provenance = product_review_adapter.finalize_candidate(
                ep,
                kind="workspace-finalize",
                runtime="WORK",
                attempt=1,
                candidate_path=candidate,
            )
            self.assertTrue(payload["summary"]["passed"])
            self.assertEqual(provenance["runtime"], "WORK_ISOLATED")
            self.assertEqual(provenance["workspace_provider"], "webcodex")
            self.assertEqual(provenance["workspace_transport"], "WEBCODEX")
            self.assertEqual(provenance["isolation_mode"], "fresh_product_review_turn")
            self.assertTrue(provenance["webcodex_used"])
            self.assertEqual(runtime_provenance.validate_critic_provenance(provenance), [])

    def test_product_review_has_no_local_bounded_workspace_fallback(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            (ep / "meta").mkdir(parents=True, exist_ok=True)
            (ep / "meta/runtime-request.json").write_text(json.dumps({
                "user_intent": {"full_auto_authorized": True}
            }), encoding="utf-8")
            (ep / "meta/shot-progression-review.json").write_text(json.dumps({
                "anomaly_applicable": False,
                "anomaly_exception_reason": "pure daily life episode"
            }), encoding="utf-8")
            source = ep / "source.txt"
            source.write_text("frozen", encoding="utf-8")
            candidate = ep / "meta/candidate.json"
            req = product_review_adapter.prepare(
                ep,
                kind="workspace-provider-review",
                runtime="WORK",
                attempt=1,
                prompt="review frozen source",
                source_paths=[source],
                candidate_path=candidate,
            )
            contract = req["review_execution_contract"]
            self.assertEqual(contract["workspace_provider"], "webcodex")
            self.assertNotIn("devspace_bounded_fallback_allowed", contract)
            self.assertNotIn("bounded_fallback_runtime", contract)

    def test_product_review_attempt_is_immutable(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            (ep / "meta").mkdir(parents=True, exist_ok=True)
            source = ep / "source.txt"
            source.write_text("frozen", encoding="utf-8")
            candidate = ep / "meta/candidate.json"
            first = product_review_adapter.prepare(
                ep,
                kind="test-review",
                runtime="WORK",
                attempt=1,
                prompt="review frozen source",
                source_paths=[source],
                candidate_path=candidate,
            )
            second = product_review_adapter.prepare(
                ep,
                kind="test-review",
                runtime="WORK",
                attempt=1,
                prompt="review frozen source",
                source_paths=[source],
                candidate_path=candidate,
            )
            self.assertEqual(first["request_id"], second["request_id"])
            with self.assertRaises(product_review_adapter.ProductReviewError):
                product_review_adapter.prepare(
                    ep,
                    kind="test-review",
                    runtime="WORK",
                    attempt=1,
                    prompt="different prompt must not overwrite attempt one",
                    source_paths=[source],
                    candidate_path=candidate,
                )

    def test_product_image_failure_releases_uncommitted_budget(self) -> None:
        ep = Path("unused")
        item = {"id": "q1", "frame": 1}
        with mock.patch.object(raw_candidate_budget, "release") as release, \
             mock.patch.object(product_image_import.image_scheduler, "ledger_tech_fail") as tech_fail, \
             mock.patch.object(product_image_import, "_set_queue_failure") as queue_fail:
            product_image_import._record_technical_failure(
                ep,
                item,
                token="q1",
                budget_committed=False,
                code="TEST_FAILURE",
                message="boom",
            )
            release.assert_called_once()
            tech_fail.assert_called_once()
            queue_fail.assert_called_once()

    def test_product_image_failure_keeps_committed_content_budget(self) -> None:
        ep = Path("unused")
        item = {"id": "q1", "frame": 1}
        with mock.patch.object(raw_candidate_budget, "release") as release, \
             mock.patch.object(product_image_import.image_scheduler, "ledger_tech_fail"), \
             mock.patch.object(product_image_import, "_set_queue_failure"):
            product_image_import._record_technical_failure(
                ep,
                item,
                token="q1",
                budget_committed=True,
                code="LEDGER_FINALIZE_FAILURE",
                message="candidate already exists",
            )
            release.assert_not_called()

    def test_release_and_caption_product_runtime_hooks_exist(self) -> None:
        self.assertTrue(callable(release_preflight.finalize_product_release_review))
        self.assertTrue(issubclass(caption_image_audit.ProductReviewHostAction, RuntimeError))

    # --- V2.6.1.1: a second attempt needs revised bytes, not a new attempt number ---

    def _freeze(self, ep: Path, name: str, text: str) -> Path:
        path = ep / name
        path.write_text(text, encoding="utf-8")
        return path

    def _reviewed_once(self, ep: Path, kind: str, source: Path) -> tuple[Path, Path]:
        """Drive the real prepare -> finalize -> mark_complete cycle for attempt 1.

        Hand-writing a FINALIZED JSON would only prove the guard reads a string.
        This makes the same three calls story_review.py makes, so the fixture is
        FINALIZED for the same reason a production review is: rc == 0.
        """
        (ep / "meta/runtime/reviews").mkdir(parents=True, exist_ok=True)
        candidate = ep / f"meta/.{kind}.candidate.json"
        product_review_adapter.prepare(
            ep, kind=kind, runtime="WORK", attempt=1,
            prompt="review frozen source", source_paths=[source],
            candidate_path=candidate,
        )
        candidate.write_text(json.dumps({"summary": {"passed": True}}), encoding="utf-8")
        product_review_adapter.finalize_candidate(
            ep, kind=kind, runtime="WORK", attempt=1, candidate_path=candidate,
        )
        final = ep / f"meta/{kind}-review.json"
        final.write_text(json.dumps({"summary": {"passed": True}}), encoding="utf-8")
        product_review_adapter.mark_complete(ep, kind=kind, final_path=final, attempt=1)
        return candidate, final

    def _second_attempt(self, ep: Path, kind: str, source: Path, candidate: Path) -> dict:
        return product_review_adapter.prepare(
            ep, kind=kind, runtime="WORK", attempt=2,
            prompt="second independent review", source_paths=[source],
            candidate_path=candidate,
        )

    def test_second_attempt_rejected_when_first_is_finalized_and_sources_unchanged(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            source = self._freeze(ep, "story.md", "story v1")
            candidate, _ = self._reviewed_once(ep, "story-semantic", source)
            with self.assertRaises(product_review_adapter.ProductReviewError) as ctx:
                self._second_attempt(ep, "story-semantic", source, candidate)
            self.assertIn("revised frozen sources", str(ctx.exception))
            self.assertFalse(
                product_review_adapter.request_path(ep, "story-semantic", attempt=2).is_file(),
                "a rejected attempt 2 must not leave a request behind",
            )

    def test_second_attempt_allowed_when_first_is_not_finalized(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            source = self._freeze(ep, "story.md", "story v1")
            (ep / "meta/runtime/reviews").mkdir(parents=True, exist_ok=True)
            candidate = ep / "meta/.story-semantic.candidate.json"
            # attempt 1 FAILed: story_review.py calls mark_complete only when rc == 0,
            # so the attempt-1 file stays AWAITING. Re-asking over these bytes is the
            # documented revise-then-retry lane and it has to keep working.
            product_review_adapter.prepare(
                ep, kind="story-semantic", runtime="WORK", attempt=1,
                prompt="review frozen source", source_paths=[source],
                candidate_path=candidate,
            )
            req = self._second_attempt(ep, "story-semantic", source, candidate)
            self.assertEqual(req["attempt"], 2)
            self.assertEqual(req["status"], "AWAITING_PRODUCT_REVIEW")

    def test_second_attempt_allowed_when_sources_changed(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            source = self._freeze(ep, "story.md", "story v1")
            candidate, _ = self._reviewed_once(ep, "story-semantic", source)
            source.write_text("story v2 revised", encoding="utf-8")
            req = self._second_attempt(ep, "story-semantic", source, candidate)
            self.assertEqual(req["attempt"], 2)

    def test_second_attempt_guard_resolves_legacy_alias_only(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            source = self._freeze(ep, "story.md", "story v1")
            candidate, _ = self._reviewed_once(ep, "story-semantic", source)
            # Requests written before V2.6.1.1 left only the alias behind.
            product_review_adapter.request_path(ep, "story-semantic", attempt=1).replace(
                product_review_adapter.request_path(ep, "story-semantic")
            )
            with self.assertRaises(product_review_adapter.ProductReviewError) as ctx:
                self._second_attempt(ep, "story-semantic", source, candidate)
            self.assertIn("revised frozen sources", str(ctx.exception))

    # --- V2.6.1.1: FINALIZED means "answered" only where finalization is PASS-gated ---

    def _redundant_residue(self, ep: Path, kind: str) -> tuple[dict, dict]:
        """Reproduce the 尸解仙 shape: attempt 1 FINALIZED over frozen bytes, then an
        attempt 2 over byte-identical sources still AWAITING, whose candidate was
        never written. Returns (attempt-1 request, attempt-2 entry)."""
        source = self._freeze(ep, f"{kind}.md", "frozen body")
        _, final = self._reviewed_once(ep, kind, source)
        reviewed = product_review_adapter._read_json(
            product_review_adapter.request_path(ep, kind, attempt=1)
        )
        residue = {
            "schema_version": 3,
            "status": "AWAITING_PRODUCT_REVIEW",
            "review_kind": kind,
            "runtime": "WORK",
            "attempt": 2,
            "created_at": "2026-09-14T18:06:05+08:00",
            "source_files": reviewed["source_files"],
            "candidate_path": reviewed["candidate_path"],
            "review_execution_contract": reviewed.get("review_execution_contract") or {},
        }
        reviews = ep / "meta/runtime/reviews"
        scoped = reviews / f"{kind}-attempt-2-request.json"
        scoped.write_text(json.dumps(residue), encoding="utf-8")
        alias = reviews / f"{kind}-request.json"
        alias.write_text(
            json.dumps({**residue, "attempt_request_path": product_review_adapter._repo_rel(scoped)}),
            encoding="utf-8",
        )
        # The reviewer never produced a candidate, so there is no finished work to lose.
        (ROOT / reviewed["candidate_path"]).unlink(missing_ok=True)
        self.assertTrue(final.is_file())
        return reviewed, {**residue, "path": product_review_adapter._repo_rel(alias)}

    def test_redundant_story_review_residue_is_suppressed_and_reported(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            (ep / "meta").mkdir(parents=True, exist_ok=True)
            (ep / "meta/episode-state.json").write_text(
                json.dumps({"current_state": "STORYBOARD_LOCKED"}), encoding="utf-8"
            )
            reviewed, entry = self._redundant_residue(ep, "story-semantic")
            self.assertIsNotNone(product_review_adapter.answered_request(ep, entry))
            self.assertIsNone(
                next_action.pending_product_review(ep, current_state="STORYBOARD_LOCKED")
            )
            residue = next_action.redundant_product_review_residue(
                ep, current_state="STORYBOARD_LOCKED"
            )
            self.assertEqual(len(residue), 1)
            answered = residue[0]["redundant_with"]
            self.assertEqual(residue[0]["review_kind"], "story-semantic")
            self.assertEqual(residue[0]["attempt"], 2)
            self.assertEqual(answered["final_path"], reviewed["final_path"])
            with mock.patch.object(next_action.product_runtime_adapter, "reconcile", return_value={}), \
                    mock.patch.object(next_action, "_handoff_valid", return_value=False), \
                    mock.patch("scheduler_core.progress", return_value={}):
                derived = next_action.derive(ep)
            self.assertNotEqual(derived["action"], "PRODUCT_REVIEW")
            self.assertEqual(derived["suppressed_product_reviews"], [{
                "request_path": residue[0]["path"],
                "review_kind": "story-semantic",
                "attempt": 2,
                "answered_by": answered["path"],
                "final_path": reviewed["final_path"],
            }])

    def test_counterexample_reviews_are_never_suppressed(self) -> None:
        """FINALIZED means "already answered" only where finalization is PASS-gated.

        These three kinds finalize unconditionally, so suppressing one would either
        re-ask an unanswered question or throw a repair authorization away.
        """
        for kind in ("recent5-semantic", "production-batch-batch-001", "caption-image-audit-v2-001"):
            with self.subTest(kind=kind), self.temp_episode() as td:
                ep = Path(td)
                _, entry = self._redundant_residue(ep, kind)
                self.assertNotIn(kind, product_review_adapter.FINALIZED_IS_PASS_KINDS)
                self.assertIsNone(product_review_adapter.answered_request(ep, entry))

    def test_redundant_review_is_not_suppressed_when_candidate_exists(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            reviewed, entry = self._redundant_residue(ep, "story-semantic")
            # A request whose candidate exists is completable, so there is no
            # permanent pin to break -- suppressing it would discard finished work.
            (ROOT / reviewed["candidate_path"]).write_text(
                json.dumps({"summary": {"passed": True}}), encoding="utf-8"
            )
            self.assertIsNone(product_review_adapter.answered_request(ep, entry))

    def test_legacy_request_without_frozen_sources_is_not_suppressed(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            _, entry = self._redundant_residue(ep, "story-semantic")
            for dropped in ("source_files", "attempt", "candidate_path"):
                with self.subTest(dropped=dropped):
                    self.assertIsNone(product_review_adapter.answered_request(
                        ep, {k: v for k, v in entry.items() if k != dropped}
                    ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
