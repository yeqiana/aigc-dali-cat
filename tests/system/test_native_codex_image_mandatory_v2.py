"""Regression guard: no StoryOS image path can call OpenCodex (port 10100)."""
from __future__ import annotations
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_user_runner
import image_payload_transport
import image_scheduler


def test_image_preflight_forbidden_proxy_never_hits_health_or_payload():
    with (
        patch.dict(os.environ, {"STORY_OS_IMAGE_PROVIDER_ROUTE": "opencodex"}),
        patch.object(image_payload_transport, "selected_route", return_value={"provider": "codex_subscription"}),
        patch.object(codex_user_runner, "_opencodex_health", side_effect=AssertionError("proxied")) as health,
        patch.object(codex_user_runner, "_opencodex_image_capability", side_effect=AssertionError("proxied")) as cap,
        patch.object(image_payload_transport.codex_subscription_image, "payload_capability_preflight",
                     side_effect=AssertionError("sent to provider")) as provider,
    ):
        result = image_payload_transport.payload_capability_preflight(
            model="gpt-image-2.5-flare", quality="high")
    assert result["status"] == "BLOCKED"
    assert result["failure_class"] == "CODEX_NATIVE_IMAGE_PROVIDER_REQUIRED"
    assert result["image_attempt_authority_called"] is False
    assert result["image_generation_called"] is False
    health.assert_not_called()
    cap.assert_not_called()
    provider.assert_not_called()


def test_codex_runner_rejects_explicit_proxy_without_socket_call():
    with (
        patch.object(codex_user_runner, "_opencodex_health", side_effect=AssertionError("probed")) as health,
        patch.object(codex_user_runner, "_opencodex_image_capability", side_effect=AssertionError("probed")) as cap,
    ):
        with pytest.raises(codex_user_runner.CodexUserRunnerRejected, match="CODEX_NATIVE_IMAGE_PROVIDER_REQUIRED"):
            codex_user_runner.resolve_provider_transport(
                ["codex", "exec", "--json", "-"], env={"STORY_OS_IMAGE_PROVIDER_ROUTE": "opencodex"},
                task_type="image")
    health.assert_not_called()
    cap.assert_not_called()


def test_forbidden_proxy_code_stays_nonregenerating(monkeypatch):
    monkeypatch.setenv("STORY_OS_IMAGE_PROVIDER_ROUTE", "opencodex")
    code = "CODEX_NATIVE_IMAGE_PROVIDER_REQUIRED"
    assert code in image_scheduler.NON_REGENERATING_FAILURE_CODES
    assert image_scheduler.classify_error(code) == code
    assert image_scheduler._technical_retry_code(
        {"last_error": code, "technical_failure_code": code}) == code
    assert "OPENCODEX_CONTROLLER_ROUTE_RETRY" not in image_scheduler.RETRYABLE_TECH_CODES


@pytest.mark.parametrize("unsupported_route", ["opencodex", "third_party_proxy", "other_provider"])
def test_image_provider_route_never_accepts_non_native_override(unsupported_route):
    with (patch.dict(os.environ, {"STORY_OS_IMAGE_PROVIDER_ROUTE": unsupported_route}),
          patch.object(image_payload_transport, "selected_route", return_value={"provider": "codex_subscription"}),
          patch.object(image_payload_transport.codex_subscription_image, "payload_capability_preflight", side_effect=AssertionError("provider contacted"))):
        row = image_payload_transport.payload_capability_preflight(model="gpt-image-2.5-flare", quality="high")
    assert row["status"] == "BLOCKED"
    assert row["failure_class"] == "CODEX_NATIVE_IMAGE_PROVIDER_REQUIRED"
    with pytest.raises(codex_user_runner.CodexUserRunnerRejected, match="CODEX_NATIVE_IMAGE_PROVIDER_REQUIRED"):
        codex_user_runner.resolve_provider_transport(["codex","exec","--json","-"], env={"STORY_OS_IMAGE_PROVIDER_ROUTE": unsupported_route}, task_type="image")
