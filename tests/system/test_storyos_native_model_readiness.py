"""Hermetic tests for the local-only client/version gate; no model calls."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

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



def test_bridge_uses_live_runner_cli_not_stale_startup_version(monkeypatch):
    """A long-running interactive Runner can outlive an in-place CLI upgrade."""
    policy = {
        "profiles": _models(),
        "policy_sha256": "s" * 64,
    }
    invocations = []

    def run_codex(argv, **kwargs):
        invocations.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout="codex-cli 0.162.1\n")

    modules = {
        "codex_cli_contract": SimpleNamespace(resolve=lambda: (_ for _ in ()).throw(
            AssertionError("service account CLI must not own bridge readiness"))),
        "codex_user_runner": SimpleNamespace(
            bridge_required=lambda: True,
            runner_health=lambda: {"status": "ok", "codex_available": True,
                                   "codex_version": "codex-cli 0.153.4"},
            run_codex=run_codex,
        ),
        "model_policy": SimpleNamespace(freeze_for_episode=lambda: policy),
        "model_policy_persistence": SimpleNamespace(load=lambda _ep: None),
    }
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    actual = readiness.inspect()
    assert actual["status"] == "CLIENT_VERSION_COMPATIBLE"
    assert actual["cli_version"] == "codex-cli 0.162.1"
    assert actual["cli_resolution"] == "INTERACTIVE_USER_RUNNER_LIVE"
    assert actual["model_calls"] == actual["sql_writes"] == 0
    assert actual["model_entitlement_verified"] is False
    assert len(invocations) == 1
    argv, kwargs = invocations[0]
    assert argv == ["codex", "--version"]
    assert kwargs["task_type"] == "smoke"
    assert kwargs["timeout"] == 30


@pytest.mark.parametrize("returncode,stdout", [
    (1, "codex-cli 0.162.1"), (0, "bad-output"), (0, "codex-cli 0.153.4\nerror"),
])
def test_bridge_rejects_unverifiable_live_version(monkeypatch, returncode, stdout):
    modules = {
        "codex_cli_contract": SimpleNamespace(resolve=lambda: None),
        "codex_user_runner": SimpleNamespace(
            bridge_required=lambda: True,
            runner_health=lambda: {"status": "ok", "codex_available": True},
            run_codex=lambda *_a, **_kw: SimpleNamespace(
                returncode=returncode, stdout=stdout),
        ),
        "model_policy": SimpleNamespace(freeze_for_episode=lambda: {
            "profiles": _models(), "policy_sha256": "s" * 64,
        }),
        "model_policy_persistence": SimpleNamespace(load=lambda _ep: None),
    }
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    with pytest.raises(RuntimeError, match="USER_RUNNER_LIVE_CODEX_VERSION_UNVERIFIED"):
        readiness.inspect()
