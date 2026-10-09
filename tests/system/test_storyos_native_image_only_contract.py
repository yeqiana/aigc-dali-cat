from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import effective_config
import codex_user_runner
import image_blocked_recovery
import image_payload_transport
import image_scheduler


def test_opencodex_explicit_route_blocked_before_any_provider_or_proxy_probe():
    with (
        patch.dict(os.environ, {"STORY_OS_IMAGE_PROVIDER_ROUTE": "opencodex"}),
        patch.object(image_payload_transport, "selected_route", return_value={"provider": "codex_subscription"}),
        patch.object(image_payload_transport.codex_subscription_image, "payload_capability_preflight") as provider,
        patch.object(codex_user_runner.socket, "create_connection") as health,
    ):
        row = image_payload_transport.payload_capability_preflight(model="gpt-image-2.5-flare", quality="high")
        assert row["status"] == "BLOCKED"
        assert row["failure_class"] == "CODEX_NATIVE_IMAGE_PROVIDER_REQUIRED"
        assert row["image_attempt_authority_called"] is False
        assert row["image_generation_called"] is False
        try:
            codex_user_runner.resolve_provider_transport(["codex", "exec", "--json", "-"], task_type="image")
        except codex_user_runner.CodexUserRunnerRejected as exc:
            assert "CODEX_NATIVE_IMAGE_PROVIDER_REQUIRED" in str(exc)
        else:
            raise AssertionError("proxy route must reject")
    provider.assert_not_called()
    health.assert_not_called()
    assert not hasattr(codex_user_runner, "_opencodex_health")
    assert not hasattr(codex_user_runner, "_opencodex_image_capability")


def test_explicit_proxy_denial_is_non_regenerating_and_actionable(tmp_path):
    code = "CODEX_NATIVE_IMAGE_PROVIDER_REQUIRED"
    assert code in image_scheduler.PRE_DISPATCH_CAPABILITY_BLOCK_CODES
    assert code in image_scheduler.NON_REGENERATING_FAILURE_CODES
    result = image_blocked_recovery.inspect_item(
        tmp_path, {"frame": 1, "id": "frame-1", "technical_failure_code": code})
    assert result["auto_resolvable"] is False
    assert result["recovery_action"] == "VERIFY_NATIVE_CODEX_IMAGE_CAPABILITY"


def test_legacy_native_only_policy_failure_is_never_reclassified_as_retry(monkeypatch):
    monkeypatch.setenv("STORY_OS_IMAGE_PROVIDER_ROUTE", "opencodex")
    code = "CODEX_NATIVE_IMAGE_PROVIDER_REQUIRED"
    assert image_scheduler.classify_error(f"{code}: policy denial") == code
    assert image_scheduler._technical_retry_code({
        "technical_failure_code": code,
        "last_error": f"{code}: policy denial",
    }) == code
    assert "OPENCODEX_CONTROLLER_ROUTE_RETRY" not in image_scheduler.RETRYABLE_TECH_CODES


def test_effective_config_exposes_actual_route_string_not_false():
    with patch.dict(os.environ, {"STORY_OS_IMAGE_PROVIDER_ROUTE": "opencodex"}):
        result = effective_config.snapshot()
    assert result["sources"]["image_provider_route"]["value"] == "opencodex"
    assert result["sources"]["image_provider_route"]["source"] == "env:STORY_OS_IMAGE_PROVIDER_ROUTE"
