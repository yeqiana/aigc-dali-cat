"""Hermetic tests for the local-only client/version gate; no model calls."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "storyos_native_model_readiness", ROOT / "scripts/storyos_native_model_readiness.py"
)
assert spec is not None and spec.loader is not None
readiness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readiness)


def _models(model="gpt-6-luna"):
    return {
        "orchestration": {"model": model, "reasoning_effort": "high"},
        "semantic_critic": {"model": model, "reasoning_effort": "high"},
        "image_payload": {"model": "gpt-image-2.5-flare", "quality": "high"},
    }


def test_luna_rejects_older_native_cli_without_model_calls():
    result = readiness.assess("codex-cli 0.153.4", _models())
    assert result["status"] == "CLIENT_VERSION_BLOCKED"
    assert result["minimum_cli_version"] == "0.155.0"
    assert result["outdated_models"] == ["gpt-6-luna"]
    assert result["model_calls"] == result["sql_writes"] == 0
    assert result["model_entitlement_verified"] is False


def test_luna_supported_client_version_does_not_claim_entitlement():
    result = readiness.assess("codex-cli 0.155.0", _models())
    assert result["status"] == "CLIENT_VERSION_COMPATIBLE"
    assert result["model_entitlement_verified"] is False
    assert result["image_tool_verified"] is False


def test_sol_and_astra_respect_different_minima():
    assert readiness.assess("codex 0.153.0", _models("gpt-6-astra"))["status"] == "CLIENT_VERSION_COMPATIBLE"
    assert readiness.assess("codex 0.154.9", _models("gpt-6-sol"))["status"] == "CLIENT_VERSION_BLOCKED"


def test_unknown_model_and_invalid_version_fail_closed():
    assert readiness.assess("codex-cli 0.999.0", _models("private-unknown"))["unassessed_models"] == ["private-unknown"]
    assert readiness.assess("not-a-version", _models())["status"] == "CLIENT_VERSION_BLOCKED"
    assert readiness.assess("codex 0.155.0", {"image_payload": {"model": "gpt-image-2"}})["status"] == "CLIENT_VERSION_BLOCKED"


def test_image_payload_not_misclassified_as_codex_cli_model():
    result = readiness.assess("codex-cli 0.155.1", _models())
    assert result["unassessed_models"] == []
    assert result["status"] == "CLIENT_VERSION_COMPATIBLE"
