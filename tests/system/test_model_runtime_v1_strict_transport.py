"""Strict dual-transport phase: native Codex or separate official API; no proxy."""
from __future__ import annotations
import sys
from pathlib import Path
from unittest import mock
import pytest
SYSTEM=Path(__file__).resolve().parents[2]/"episodes"/"_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0,str(SYSTEM))
import codex_user_runner as runner

def _resolve(argv, env):
    return runner.resolve_provider_transport(argv, env={
        "STORY_OS_MODEL_TRANSPORT_POLICY":"DUAL_ONLY", **env},
        health_probe=lambda url: pytest.fail("OpenCodex probe must never run"),
        image_capability_probe=lambda url: pytest.fail("image proxy probe must never run"))

@pytest.mark.parametrize("kind",["generic_codex","image"])
def test_native_default_never_probes_opencodex(kind):
    result=runner.resolve_provider_transport(["codex","exec","-"], env={
        "STORY_OS_MODEL_TRANSPORT_POLICY":"DUAL_ONLY",
        "OPENAI_BASE_URL":runner.NATIVE_CODEX_BASE_URL},
        task_type=kind,health_probe=lambda url:pytest.fail("health probe"))
    assert result["transport_route"]=="native_codex"
    assert result["transport_base_url"]==runner.NATIVE_CODEX_BASE_URL

@pytest.mark.parametrize("bad",["http://127.0.0.1:10100/v1","https://unapproved.example/v1"])
def test_env_proxy_fails_before_network_probe(bad):
    with pytest.raises(runner.CodexUserRunnerRejected,match="MODEL_TRANSPORT_FORBIDDEN"):
        _resolve(["codex","exec","-"],{"OPENAI_BASE_URL":bad})

@pytest.mark.parametrize("bad",["http://127.0.0.1:10100/v1","https://other.example/v1"])
def test_cli_provider_override_fails_closed(bad):
    with pytest.raises(runner.CodexUserRunnerRejected,match="MODEL_TRANSPORT_FORBIDDEN"):
        _resolve(["codex","-c",f'openai_base_url="{bad}"',"exec","-"],{})

def test_explicit_native_cli_override_is_allowed():
    row=_resolve(["codex","-c",f'openai_base_url="{runner.NATIVE_CODEX_BASE_URL}"',
                  "exec","-"],{})
    assert row["transport_route"]=="native_codex"
    assert row["provider_args"]==[]

def test_non_model_codex_commands_not_routed():
    assert _resolve(["codex","login","status"],{"OPENAI_BASE_URL":"http://127.0.0.1:10100/v1"}) is None

def test_legacy_routing_default_not_changed_yet():
    with mock.patch.object(runner,"_opencodex_health",return_value=(False,"offline")):
        row=runner.resolve_provider_transport(["codex","exec","-"],env={})
    assert row["transport_route"]=="native_codex"

def test_strict_forbidden_proxy_prevents_subprocess_launch():
    env={"STORY_OS_MODEL_TRANSPORT_POLICY":"DUAL_ONLY",
         "OPENAI_BASE_URL":"http://127.0.0.1:10100/v1"}
    with mock.patch.object(runner.subprocess, "run") as launch:
        with pytest.raises(runner.CodexUserRunnerRejected,match="MODEL_TRANSPORT_FORBIDDEN"):
            runner.run_codex(["codex","exec","-"], env=env, input="hello", timeout=1)
        launch.assert_not_called()

@pytest.mark.parametrize("bad", [
    'model_provider="custom_gateway"',
    'model_provider="opencodex"',
    'model_providers.custom.base_url="http://127.0.0.1:10100/v1"',
    'openai_base_url="http://127.0.0.1:10100/v1"',
])
def test_dual_only_rejects_poisoned_provider_even_if_native_url_also_present(bad):
    argv=["codex","-c",f'openai_base_url="{runner.NATIVE_CODEX_BASE_URL}"',
          "-c",bad,"exec","-"]
    with pytest.raises(runner.CodexUserRunnerRejected,match="MODEL_TRANSPORT_FORBIDDEN"):
        _resolve(argv,{})

@pytest.mark.parametrize("value",[
    '--config=model_provider="untrusted"',
    '--config=model_providers.alt.base_url="https://thirdparty.invalid/v1"',
    '-cmodel_provider="proxy"',
])
def test_inline_config_proxy_rejected_before_launch(value):
    argv=["codex",value,"-c",f'openai_base_url="{runner.NATIVE_CODEX_BASE_URL}"',"exec","-"]
    with pytest.raises(runner.CodexUserRunnerRejected,match="MODEL_TRANSPORT_FORBIDDEN"):
        _resolve(argv,{})
