from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_subscription_image as image
import runtime_timeout_policy


def _provenance():
    return {"candidate_catalog_member": True, "catalog_source": image._LOGIN_CATALOG_SOURCE,
            "catalog_sha256": "a" * 64, "model": "test-visible-model",
            "effort": "low", "priority": 1}


def test_tool_visibility_uses_separate_longer_bound_without_generating():
    calls = []
    def fake_codex(*_args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(returncode=1, stdout="")
    with (patch.object(image, "execution_command_prefix", return_value=["codex"]),
          patch.object(image.codex_user_runner, "run_codex", side_effect=fake_codex)):
        result = image._probe_transport_model_diagnostic(
            Path("codex.exe"), "test-visible-model", "low",
            candidate_provenance=_provenance(), tool_visibility_probe=True)
    assert len(calls) == 1
    assert calls[0]["timeout"] == runtime_timeout_policy.seconds("image_tool_visibility_probe")
    assert calls[0]["task_type"] == "smoke"
    assert "Do not call any tool" in calls[0]["input"]
    assert result["status"] == "BLOCKED"


def test_login_transport_sentinel_keeps_short_probe_timeout():
    calls = []
    def fake_codex(*_args, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(returncode=1, stdout="")
    with (patch.object(image, "execution_command_prefix", return_value=["codex"]),
          patch.object(image.codex_user_runner, "run_codex", side_effect=fake_codex)):
        image._probe_transport_model_diagnostic(
            Path("codex.exe"), "test-visible-model", "low",
            candidate_provenance=_provenance(), tool_visibility_probe=False)
    assert len(calls) == 1
    assert calls[0]["timeout"] == runtime_timeout_policy.seconds("codex_auth_probe")
    assert "STORYOS_TRANSPORT_OK" in calls[0]["input"]


def test_visibility_default_is_bounded_without_changing_regular_login():
    assert runtime_timeout_policy.seconds("image_tool_visibility_probe") == 120
    assert runtime_timeout_policy.seconds("codex_auth_probe") == 30
