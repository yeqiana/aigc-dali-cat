from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import image_worker_pool


class GenerationAttemptContextTests(TestCase):
    def test_attempt_context_captures_frozen_controller_and_separate_payload_before_reserve(self):
        policy_sha = "4bc59107d83cf3900162dc09b925e49f6b2657d59d351f0804ea4546d64118c5"
        bound = {
            "image.controller": {
                "profile": "image_controller", "model": "gpt-6-luna",
                "reasoning_effort": "high", "policy_version": "frozen-v1",
                "model_policy_sha256": policy_sha,
            },
            "image.payload": {
                "profile": "image_payload", "model": "gpt-image-2.5-flare",
                "quality": "high", "policy_version": "frozen-v1",
                "model_policy_sha256": policy_sha,
            },
        }
        with patch.object(image_worker_pool.model_policy, "resolve", side_effect=lambda role, episode=None: bound[role]):
            context = image_worker_pool.generation_attempt_context(
                ROOT / "episodes" / "_canary" / "unused",
                {"scope": "production", "provider": "codex_subscription", "runner": "codex_user_runner"},
                {"model": "gpt-image-2.5-flare", "quality": "high"},
            )

        self.assertEqual(context["model_role"], "image.controller")
        self.assertEqual(context["profile"], "image_controller")
        self.assertEqual(context["controller_model"], "gpt-6-luna")
        self.assertEqual(context["controller_effort"], "high")
        self.assertEqual(context["payload_model"], "gpt-image-2.5-flare")
        self.assertEqual(context["payload_quality"], "high")
        self.assertEqual(context["model_policy_version"], "frozen-v1")
        self.assertEqual(context["model_policy_sha256"], policy_sha)
        self.assertEqual(context["provider_candidate"], "codex_subscription")
        self.assertEqual(context["runner_candidate"], "codex_user_runner")
        self.assertEqual(context["controller_model_source"], "EPISODE_BOUND_RUNTIME_POLICY")
        self.assertEqual(context["payload_model_source"], "EXPLICIT_RUNTIME_BINDING")

    def test_attempt_context_keeps_runner_and_provider_candidates_explicit(self):
        with patch.object(image_worker_pool.model_policy, "resolve", side_effect=[
            {"profile": "image_controller", "model": "gpt-6-luna", "reasoning_effort": "high",
             "policy_version": "frozen-v1", "model_policy_sha256": "a" * 64},
            {"profile": "image_payload", "model": "gpt-image-2.5-flare", "quality": "high",
             "policy_version": "frozen-v1", "model_policy_sha256": "a" * 64},
        ]):
            context = image_worker_pool.generation_attempt_context(
                ROOT, {"provider_candidate": "api_http", "runner_candidate": "codex_cli"},
                {"model": "gpt-image-2.5-flare", "quality": "high"},
            )
        self.assertEqual(context["provider"], "api_http")
        self.assertEqual(context["provider_candidate"], "api_http")
        self.assertEqual(context["runner_candidate"], "codex_cli")

    def test_worker_passes_complete_canary_frozen_context_to_claim_before_provider(self):
        from unittest.mock import Mock

        policy_sha = "4bc59107d83cf3900162dc09b925e49f6b2657d59d351f0804ea4546d64118c5"
        bound = {
            "image.controller": {
                "profile": "image_controller", "model": "gpt-6-luna",
                "reasoning_effort": "high", "policy_version": "lean-2026-09-30-v1",
                "model_policy_sha256": policy_sha,
            },
            "image.payload": {
                "profile": "image_payload", "model": "gpt-image-2.5-flare",
                "quality": "high", "policy_version": "lean-2026-09-30-v1",
                "model_policy_sha256": policy_sha,
            },
        }
        call_order = []
        captured = {}

        def claim_stub(*_args, generation_context=None, **_kwargs):
            call_order.append("claim")
            captured.update(generation_context or {})
            # Fail closed here so this unit test cannot reach a Provider call.
            return False, {"decision": "TEST_STOP_BEFORE_RESERVE"}

        provider_stub = Mock(side_effect=lambda *_args, **_kwargs: call_order.append("provider"))
        item = {
            "id": "phase5a-context-test", "frame": 1, "attempts": 1,
            "scope": "production", "prompt_file": "episodes/_canary/test/prompt.txt",
            "provider_candidate": "codex_subscription", "runner_candidate": "codex_user_runner",
        }
        episode = ROOT / "episodes" / "_canary" / "phase5a-context-unit"

        with (
            patch.object(image_worker_pool.resource_library, "ensure_fresh"),
            patch.object(image_worker_pool.runtime_router, "detect", return_value=("CODEX", {})),
            patch.object(image_worker_pool.runtime_router, "image_execution_runtime", return_value=("CODEX", {})),
            patch.object(image_worker_pool.production_recovery, "write_lifecycle"),
            patch.object(image_worker_pool, "model_policy_for_item", return_value={
                "model": "gpt-image-2.5-flare", "quality": "high", "strict_model": True,
            }),
            patch.object(image_worker_pool.prompt_package, "compile_frame", return_value={
                "package_sha256": "p", "scene_prompt_sha256": "s", "frame_contract_sha256": "f",
            }),
            patch.object(image_worker_pool.runtime_circuit_breaker, "blocking", return_value=None),
            patch.object(image_worker_pool.canvas_normalize, "read_canvas", return_value=(1080, 1350, "4:5")),
            patch.object(image_worker_pool, "_canonical_controller_request", side_effect=lambda *_a, **_k: (
                call_order.append("controller") or {
                    "request": {"controller_output_sha256": "controller-output", "request_fingerprint": "request-fp"},
                    "controller_call_id": "controller-call",
                }
            )),
            patch.object(image_worker_pool.openai_images_provider, "payload_capability_preflight", side_effect=lambda **_k: (
                call_order.append("payload_preflight") or {"status": "PASS"}
            )),
            patch.object(image_worker_pool.raw_candidate_budget, "kind_for_queue_item", return_value="original"),
            patch.object(image_worker_pool.raw_candidate_budget, "semantic_key_for_queue_item", return_value=None),
            patch.object(image_worker_pool.raw_candidate_budget, "claim", side_effect=claim_stub),
            patch.object(image_worker_pool.backend, "generate_for_frame", provider_stub),
            patch.object(image_worker_pool.model_policy, "resolve", side_effect=lambda role, episode=None: bound[role]),
        ):
            result = image_worker_pool.execute(episode, item, 10, codex=True)

        self.assertEqual(result["returncode"], 98)
        self.assertEqual(call_order, ["controller", "payload_preflight", "claim"])
        provider_stub.assert_not_called()
        self.assertEqual(captured["model_role"], "image.controller")
        self.assertEqual(captured["profile"], "image_controller")
        self.assertEqual(captured["controller_model"], "gpt-6-luna")
        self.assertEqual(captured["controller_effort"], "high")
        self.assertEqual(captured["payload_model"], "gpt-image-2.5-flare")
        self.assertEqual(captured["payload_quality"], "high")
        self.assertEqual(captured["model_policy_version"], "lean-2026-09-30-v1")
        self.assertEqual(captured["model_policy_sha256"], policy_sha)
        self.assertEqual(captured["provider_candidate"], "openai_images_api")
        self.assertEqual(captured["runner_candidate"], "python-openai-images-http")


if __name__ == "__main__":
    import unittest
    unittest.main()
