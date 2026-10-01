#!/usr/bin/env python3
from __future__ import annotations

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
