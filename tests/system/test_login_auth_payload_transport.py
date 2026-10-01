#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_subscription_image
import image_payload_transport


class LoginAuthPayloadTransportTests(unittest.TestCase):
    def test_catalog_prefers_visible_provider_models_and_excludes_business_controller(self):
        rows = codex_subscription_image._catalog_candidates({
            "models": [
                {"slug": "gpt-6-luna", "visibility": "list", "priority": 1,
                 "default_reasoning_level": "high", "supported_reasoning_levels": ["high"]},
                {"slug": "gpt-hidden", "visibility": "hide", "priority": 2},
                {"slug": "transport-b", "visibility": "list", "priority": 8,
                 "default_reasoning_level": "medium", "supported_reasoning_levels": ["medium"]},
                {"slug": "transport-a", "visibility": "list", "priority": 3,
                 "default_reasoning_level": "medium",
                 "supported_reasoning_levels": [{"effort": "low"}, {"effort": "medium"}]},
            ]
        })
        self.assertEqual([row["model"] for row in rows], ["transport-a", "transport-b"])
        self.assertEqual(rows[0]["effort"], "low")

    def test_bridge_execution_prefix_defers_executable_resolution_to_user_runner(self):
        with patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=True):
            self.assertEqual(
                codex_subscription_image.execution_command_prefix(Path(r"C:/service/codex.exe")),
                ["codex"],
            )

    def test_direct_execution_prefix_keeps_local_codex_contract(self):
        with (
            patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=False),
            patch.object(codex_subscription_image, "command_prefix", return_value=["resolved-codex"]),
        ):
            self.assertEqual(
                codex_subscription_image.execution_command_prefix(Path("codex.exe")),
                ["resolved-codex"],
            )

    def test_login_preflight_failure_is_before_attempt_and_generation(self):
        with (
            patch.object(codex_subscription_image, "resolve_codex", return_value=Path("codex.exe")),
            patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=True),
            patch.object(codex_subscription_image, "image_runtime_preflight",
                         side_effect=codex_subscription_image.BackendError("runner unavailable")),
        ):
            row = codex_subscription_image.payload_capability_preflight(
                model="gpt-image-2.5-flare", quality="high")
        self.assertEqual(row["status"], "BLOCKED")
        self.assertEqual(row["failure_class"], "LOGIN_AUTH_IMAGE_TOOL_UNAVAILABLE")
        self.assertFalse(row["image_attempt_authority_called"])
        self.assertFalse(row["image_generation_called"])

    def test_cleanup_timeout_adopts_completed_sentinel_without_image_call(self):
        raw = (
            '{"type":"thread.started"}\n'
            '{"type":"turn.started"}\n'
            '{"type":"item.completed","item":{"type":"agent_message","text":"STORYOS_TRANSPORT_OK"}}\n'
            '{"type":"turn.completed","usage":{}}\n'
        )
        exc = codex_subscription_image.codex_user_runner.CodexUserRunnerTimeout(
            ["codex"], 30, "cleanup timeout")
        exc.remote = {"request_id": "abc123", "timed_out": True, "returncode": 124}
        result = {
            "output_base64": base64.b64encode(raw.encode("utf-8")).decode("ascii"),
            "returncode": 124,
        }
        with (
            patch.object(codex_subscription_image.codex_user_runner, "run_codex", side_effect=exc),
            patch.object(codex_subscription_image.codex_user_runner, "read_task_result", return_value=result),
            patch.object(codex_subscription_image, "execution_command_prefix", return_value=["codex"]),
        ):
            ok, evidence = codex_subscription_image._probe_transport_model(
                Path("codex.exe"), "transport-a", "low")
        self.assertTrue(ok)
        self.assertEqual(evidence, "PASS_WITH_CLEANUP_TIMEOUT")

    def test_normal_jsonl_exact_sentinel_and_completed_turn_passes(self):
        raw = (
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"  STORYOS_TRANSPORT_OK  "}}\n'
            '{"type":"turn.completed"}\n'
        )
        self.assertTrue(codex_subscription_image._transport_probe_completed(raw))
        with (
            patch.object(codex_subscription_image.codex_user_runner, "run_codex",
                         return_value=SimpleNamespace(returncode=0, stdout=raw)) as run,
            patch.object(codex_subscription_image, "execution_command_prefix", return_value=["codex"]),
        ):
            ok, evidence = codex_subscription_image._probe_transport_model(
                Path("codex.exe"), "transport-a", "low")
        self.assertTrue(ok)
        self.assertEqual(evidence, "PASS")
        run.assert_called_once()

    def _timeout_probe(self, *, remote, result=None):
        exc = codex_subscription_image.codex_user_runner.CodexUserRunnerTimeout(
            ["codex"], 30, "cleanup timeout")
        exc.remote = remote
        with (
            patch.object(codex_subscription_image.codex_user_runner, "run_codex", side_effect=exc) as run,
            patch.object(codex_subscription_image.codex_user_runner, "read_task_result",
                         return_value=result or {}) as read_result,
            patch.object(codex_subscription_image, "execution_command_prefix", return_value=["codex"]),
        ):
            outcome = codex_subscription_image._probe_transport_model(
                Path("codex.exe"), "transport-a", "low")
        run.assert_called_once()
        return outcome, read_result

    def test_cleanup_timeout_without_request_id_fails_without_readback(self):
        (ok, _), read_result = self._timeout_probe(remote={"timed_out": True})
        self.assertFalse(ok)
        read_result.assert_not_called()

    def test_cleanup_timeout_reads_request_id_from_remote_object(self):
        raw = (
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"STORYOS_TRANSPORT_OK"}}\n'
            '{"type":"turn.completed"}\n'
        )
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        (ok, evidence), read_result = self._timeout_probe(
            remote=SimpleNamespace(request_id="request-object"),
            result={"output_base64": encoded},
        )
        self.assertTrue(ok)
        self.assertEqual(evidence, "PASS_WITH_CLEANUP_TIMEOUT")
        read_result.assert_called_once_with("request-object")

    def test_cleanup_timeout_without_durable_result_fails(self):
        (ok, _), read_result = self._timeout_probe(remote={"request_id": "abc123"})
        self.assertFalse(ok)
        read_result.assert_called_once_with("abc123")

    def test_cleanup_timeout_rejects_corrupt_durable_base64(self):
        (ok, _), _ = self._timeout_probe(
            remote={"request_id": "abc123"}, result={"output_base64": "%%%"})
        self.assertFalse(ok)

    def test_cleanup_timeout_rejects_invalid_utf8_durable_output(self):
        encoded = base64.b64encode(b"\xff").decode("ascii")
        (ok, _), _ = self._timeout_probe(
            remote={"request_id": "abc123"}, result={"output_base64": encoded})
        self.assertFalse(ok)

    def test_cleanup_timeout_requires_turn_completed(self):
        raw = '{"type":"item.completed","item":{"type":"agent_message","text":"STORYOS_TRANSPORT_OK"}}\n'
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        (ok, _), _ = self._timeout_probe(
            remote={"request_id": "abc123"}, result={"output_base64": encoded})
        self.assertFalse(ok)

    def test_cleanup_timeout_rejects_ordinary_text_sentinel(self):
        raw = 'Some ordinary text says STORYOS_TRANSPORT_OK\n{"type":"turn.completed"}\n'
        self.assertFalse(codex_subscription_image._transport_probe_completed(raw))
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        (ok, _), _ = self._timeout_probe(
            remote={"request_id": "abc123"}, result={"output_base64": encoded})
        self.assertFalse(ok)

    def test_probe_rejects_malformed_jsonl_instead_of_skipping_unknown_event(self):
        raw = (
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"STORYOS_TRANSPORT_OK"}}\n'
            'not-json\n'
            '{"type":"turn.completed"}\n'
        )
        self.assertFalse(codex_subscription_image._transport_probe_completed(raw))

    def test_direct_probe_rejects_image_generation_tool_event(self):
        raw = (
            '{"type":"item.completed","item":{"type":"tool_call",'
            '"name":"image_generation"}}\n'
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"STORYOS_TRANSPORT_OK"}}\n'
            '{"type":"turn.completed"}\n'
        )
        with (
            patch.object(codex_subscription_image.codex_user_runner, "run_codex",
                         return_value=SimpleNamespace(returncode=0, stdout=raw)),
            patch.object(codex_subscription_image, "execution_command_prefix", return_value=["codex"]),
        ):
            ok, _ = codex_subscription_image._probe_transport_model(
                Path("codex.exe"), "transport-a", "low")
        self.assertFalse(ok)

    def test_probe_rejects_provider_image_generation_item_type(self):
        raw = (
            '{"type":"item.completed","item":{"type":"image_generation_call"}}\n'
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"STORYOS_TRANSPORT_OK"}}\n'
            '{"type":"turn.completed"}\n'
        )
        self.assertFalse(codex_subscription_image._transport_probe_completed(raw))

    def test_cleanup_timeout_rejects_image_tool_event(self):
        raw = (
            '{"type":"item.completed","item":{"type":"tool_call","name":"image_generation"}}\n'
            '{"type":"item.completed","item":{"type":"agent_message","text":"STORYOS_TRANSPORT_OK"}}\n'
            '{"type":"turn.completed","usage":{}}\n'
        )
        self.assertFalse(codex_subscription_image._transport_probe_completed(raw))

    def test_login_preflight_selects_first_successful_catalog_transport(self):
        probes = []
        with (
            patch.object(codex_subscription_image, "resolve_codex", return_value=Path("codex.exe")),
            patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=True),
            patch.object(codex_subscription_image, "image_runtime_preflight", return_value={"transport": "user_runner"}),
            patch.object(codex_subscription_image, "_subscription_model_catalog", return_value=[
                {"model": "transport-a", "effort": "low", "priority": 1},
                {"model": "transport-b", "effort": "medium", "priority": 2},
            ]),
            patch.object(codex_subscription_image, "_probe_transport_model",
                         side_effect=lambda _c, model, effort: (
                             probes.append((model, effort)) or (model == "transport-b", "probe")
                         )),
        ):
            row = codex_subscription_image.payload_capability_preflight(
                model="gpt-image-2.5-flare", quality="high")
        self.assertEqual(row["status"], "PASS")
        self.assertEqual(row["transport_model"], "transport-b")
        self.assertEqual(row["transport_effort"], "medium")
        self.assertEqual(probes, [("transport-a", "low"), ("transport-b", "medium")])
        self.assertFalse(row["api_key_required"])
        self.assertFalse(row["image_attempt_authority_called"])
        self.assertFalse(row["image_generation_called"])

    def test_transport_prompt_freezes_payload_and_calls_image_once(self):
        request = {
            "request_fingerprint": "f" * 64,
            "payload_model": "gpt-image-2.5-flare",
            "payload_quality": "high",
            "scene_prompt": "exact scene prompt",
        }
        prompt = codex_subscription_image.payload_transport_prompt(request, "1080x1350", 2)
        self.assertIn("image_generation exactly once", prompt)
        self.assertIn("EXACT_IMAGE_MODEL: gpt-image-2.5-flare", prompt)
        self.assertIn("EXACT_IMAGE_QUALITY: high", prompt)
        self.assertIn("EXACT_CANVAS: 1080x1350", prompt)
        self.assertIn("exact scene prompt", prompt)
        self.assertIn("Do not rewrite", prompt)

    def test_provider_adapter_delegates_to_selected_codex_login_route(self):
        with (
            patch.object(image_payload_transport, "selected_route", return_value={
                "provider": "codex_subscription", "api_key_required": False,
            }),
            patch.object(image_payload_transport.codex_subscription_image,
                         "payload_capability_preflight", return_value={
                             "status": "PASS", "provider": "codex_subscription",
                             "transport_model": "transport-a", "transport_effort": "low",
                         }),
        ):
            row = image_payload_transport.payload_capability_preflight(
                model="gpt-image-2.5-flare", quality="high")
        self.assertEqual(row["provider"], "codex_subscription")
        self.assertEqual(row["transport_model"], "transport-a")
        self.assertFalse(row["api_key_required"])


if __name__ == "__main__":
    unittest.main()
