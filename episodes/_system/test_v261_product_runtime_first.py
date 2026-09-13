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
            with mock.patch.dict(os.environ, {"LOCALAPPDATA": td, "CODEX_EXE": ""}, clear=False):
                with mock.patch.object(
                    codex_subscription_image.shutil,
                    "which",
                    side_effect=lambda name: sys.executable if name == "codex" else None,
                ):
                    resolved = codex_subscription_image.resolve_codex(None)
        self.assertEqual(resolved, Path(sys.executable).resolve())

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
            history = list((ep / product_runtime_adapter.REQUEST_HISTORY_REL).glob("*.json"))
            self.assertEqual(len(history), 1)
            final = product_runtime_adapter.mark_complete(ep, first["request_id"], result={"ok": True})
            self.assertEqual(final["status"], "FINALIZED")
            current = json.loads((ep / product_runtime_adapter.REQUEST_REL).read_text(encoding="utf-8"))
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
            current = json.loads((ep / product_runtime_adapter.REQUEST_REL).read_text(encoding="utf-8"))
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

    def test_product_runtime_request_is_work_devspace_only(self) -> None:
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
            self.assertEqual(req["host_contract"]["workspace_transport"], "DEVSPACE")
            self.assertFalse(req["host_contract"]["webcodex_allowed"])
            with self.assertRaises(ValueError):
                product_runtime_adapter.build_request(
                    ep, runtime="WEB", mode="full_auto", resume=False, source="test"
                )

    def test_product_review_request_is_work_devspace_only(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            (ep / "meta").mkdir(parents=True, exist_ok=True)
            source = ep / "source.txt"
            source.write_text("frozen", encoding="utf-8")
            candidate = ep / "meta/candidate.json"
            req = product_review_adapter.prepare(
                ep,
                kind="devspace-review",
                runtime="WORK",
                attempt=1,
                prompt="review frozen source",
                source_paths=[source],
                candidate_path=candidate,
            )
            self.assertEqual(req["runtime"], "WORK")
            self.assertEqual(req["critic_runtime"], "WORK_ISOLATED")
            self.assertEqual(req["workspace_transport"], "DEVSPACE")
            self.assertFalse(req["review_execution_contract"]["webcodex_allowed"])
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

    def test_product_review_finalize_emits_devspace_provenance(self) -> None:
        with self.temp_episode() as td:
            ep = Path(td)
            (ep / "meta").mkdir(parents=True, exist_ok=True)
            source = ep / "source.txt"
            source.write_text("frozen", encoding="utf-8")
            candidate = ep / "meta/candidate.json"
            product_review_adapter.prepare(
                ep,
                kind="devspace-finalize",
                runtime="WORK",
                attempt=1,
                prompt="review frozen source",
                source_paths=[source],
                candidate_path=candidate,
            )
            candidate.write_text(json.dumps({"summary": {"passed": True}}), encoding="utf-8")
            payload, provenance = product_review_adapter.finalize_candidate(
                ep,
                kind="devspace-finalize",
                runtime="WORK",
                attempt=1,
                candidate_path=candidate,
            )
            self.assertTrue(payload["summary"]["passed"])
            self.assertEqual(provenance["runtime"], "WORK_ISOLATED")
            self.assertEqual(provenance["workspace_transport"], "DEVSPACE")
            self.assertEqual(provenance["isolation_mode"], "fresh_product_review_turn")
            self.assertFalse(provenance["webcodex_used"])
            self.assertEqual(runtime_provenance.validate_critic_provenance(provenance), [])

    def test_product_review_bounded_devspace_is_honest_and_daily_life_only(self) -> None:
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
                kind="bounded-review",
                runtime="WORK",
                attempt=1,
                prompt="review frozen source",
                source_paths=[source],
                candidate_path=candidate,
            )
            self.assertTrue(req["review_execution_contract"]["devspace_bounded_fallback_allowed"])
            candidate.write_text(json.dumps({"summary": {"passed": True}}), encoding="utf-8")
            payload, provenance = product_review_adapter.finalize_candidate(
                ep,
                kind="bounded-review",
                runtime="WORK",
                attempt=1,
                candidate_path=candidate,
                bounded_devspace=True,
            )
            self.assertTrue(payload["summary"]["passed"])
            self.assertEqual(provenance["runtime"], "WORK_DEVSPACE_BOUNDED")
            self.assertFalse(provenance["isolated_session"])
            self.assertEqual(provenance["workspace_transport"], "DEVSPACE")
            self.assertEqual(provenance["isolation_mode"], "bounded_request_only")
            self.assertTrue(provenance["full_auto_user_authorized"])
            self.assertTrue(provenance["ordinary_life_only"])
            self.assertEqual(runtime_provenance.validate_critic_provenance(provenance), [])

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
