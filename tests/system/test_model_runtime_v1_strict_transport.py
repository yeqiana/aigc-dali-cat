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
    assert any("model_provider" in x for x in row["provider_args"])

def test_non_model_codex_commands_not_routed():
    assert _resolve(["codex","login","status"],{"OPENAI_BASE_URL":"http://127.0.0.1:10100/v1"}) is None

def test_legacy_routing_default_not_changed_yet():
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

def test_lower_level_execute_codex_rejects_proxy_before_http():
    task=runner.build_task(
        ["codex","-c",'openai_base_url="http://127.0.0.1:10100/v1"',
         "exec","-"], stdin_bytes=b"prompt",
        env={"STORY_OS_MODEL_TRANSPORT_POLICY":"DUAL_ONLY"})
    with mock.patch.object(runner,"client_credentials") as creds:
        with pytest.raises(runner.CodexUserRunnerRejected,match="MODEL_TRANSPORT_FORBIDDEN"):
            runner.execute_codex(task)
        creds.assert_not_called()

def test_lower_level_execute_task_rejects_proxy_before_codex_resolution():
    task=runner.build_task(["codex","-c",'model_provider="proxy"',"exec","-"],
                           stdin_bytes=b"prompt",env={"STORY_OS_MODEL_TRANSPORT_POLICY":"DUAL_ONLY"})
    with mock.patch.object(runner,"resolve_codex") as resolution:
        with pytest.raises(runner.CodexUserRunnerRejected,match="MODEL_TRANSPORT_FORBIDDEN"):
            runner.execute_task(task)
        resolution.assert_not_called()

def test_lower_level_strict_task_pins_native_without_mutating_request():
    task=runner.build_task(["codex","exec","--json","-"],
                           stdin_bytes=b"prompt",env={"STORY_OS_MODEL_TRANSPORT_POLICY":"DUAL_ONLY"})
    original=list(task.argv)
    prepared,route=runner._prepare_strict_codex_task(task)
    assert prepared is not task
    assert route["transport_route"]=="native_codex"
    assert 'model_provider="openai"' in prepared.argv
    assert any(runner.NATIVE_CODEX_BASE_URL in x for x in prepared.argv)
    assert task.argv==original

def test_lower_level_legacy_task_unchanged_when_not_opted_in():
    task=runner.build_task(["codex","exec","-"],stdin_bytes=b"prompt",env={})
    with mock.patch.dict(runner.os.environ,{"STORY_OS_MODEL_TRANSPORT_POLICY":""}):
        prepared,route=runner._prepare_strict_codex_task(task)
    assert prepared is task and route is None

def test_low_level_strict_overrides_command_proxy_in_both_paths():
    for suffix in ('model_provider="evil"','model_providers.evil.base_url="https://evil.invalid"'):
        task=runner.build_task(["codex","-c",suffix,"exec","-"],
                              env={"STORY_OS_MODEL_TRANSPORT_POLICY":"DUAL_ONLY"})
        with pytest.raises(runner.CodexUserRunnerRejected,match="MODEL_TRANSPORT_FORBIDDEN"):
            runner._prepare_strict_codex_task(task)

def test_explicit_native_cannot_mask_inherited_proxy_endpoint():
    with pytest.raises(runner.CodexUserRunnerRejected, match="MODEL_TRANSPORT_FORBIDDEN"):
        _resolve(["codex", "-c", f'openai_base_url="{runner.NATIVE_CODEX_BASE_URL}"',
                  "exec", "-"], {"OPENAI_BASE_URL": "http://127.0.0.1:10100/v1"})

def test_global_dual_only_policy_cannot_be_disabled_by_run_codex_env():
    with mock.patch.dict(runner.os.environ, {"STORY_OS_MODEL_TRANSPORT_POLICY": "DUAL_ONLY"}):
        with mock.patch.object(runner.subprocess,"run") as child:
            with pytest.raises(runner.CodexUserRunnerRejected,match="MODEL_TRANSPORT_FORBIDDEN"):
                runner.run_codex(["codex", "exec", "-"],
                    env={"STORY_OS_MODEL_TRANSPORT_POLICY": "",
                         "OPENAI_BASE_URL": "http://127.0.0.1:10100/v1"},
                    input="hello",timeout=1)
            child.assert_not_called()

def test_global_dual_only_policy_cannot_be_disabled_by_task_env():
    task=runner.build_task(["codex","-c",'model_provider="proxy"',"exec","-"],
        env={"STORY_OS_MODEL_TRANSPORT_POLICY": ""})
    with mock.patch.dict(runner.os.environ, {"STORY_OS_MODEL_TRANSPORT_POLICY": "DUAL_ONLY"}):
        with pytest.raises(runner.CodexUserRunnerRejected,match="MODEL_TRANSPORT_FORBIDDEN"):
            runner._prepare_strict_codex_task(task)

def test_canonical_model_task_preserves_direct_and_bridge_routing():
    task=runner.build_task(["codex","exec","-"],stdin_bytes=b"test",env={})
    with mock.patch.object(runner,"bridge_required",return_value=False), mock.patch.object(
            runner,"execute_task",return_value="direct") as direct, mock.patch.object(
            runner,"execute_codex") as bridge:
        assert runner.execute_model_task(task)=="direct"
        direct.assert_called_once()
        called = direct.call_args.args[0]
        assert called is not task
        assert called.env["STORY_OS_MODEL_TRANSPORT_POLICY"] == "DUAL_ONLY"
        assert called.stdin_bytes() == task.stdin_bytes()
        assert called.request_id == task.request_id
        bridge.assert_not_called()
    with mock.patch.object(runner,"bridge_required",return_value=True), mock.patch.object(
            runner,"execute_task") as direct, mock.patch.object(
            runner,"execute_codex",return_value="bridge") as bridge:
        assert runner.execute_model_task(task)=="bridge"
        bridge.assert_called_once()
        assert bridge.call_args.args[0].env["STORY_OS_MODEL_TRANSPORT_POLICY"] == "DUAL_ONLY"
        direct.assert_not_called()

def test_model_facade_preserves_runner_execution_semantics():
    sentinel=object()
    with mock.patch.object(runner,"run_codex",return_value=sentinel) as impl:
        result=runner.run_model_codex(["codex","exec","-"],input=b"binary",check=False,
                                      task_type="image",request_id="durable-123")
    assert result is sentinel
    invoked=impl.call_args
    assert invoked.args == (["codex","exec","-"],)
    assert invoked.kwargs["input"] == b"binary"
    assert invoked.kwargs["check"] is False
    assert invoked.kwargs["task_type"] == "image"
    assert invoked.kwargs["request_id"] == "durable-123"
    assert invoked.kwargs["env"]["STORY_OS_MODEL_TRANSPORT_POLICY"] == "DUAL_ONLY"


def test_model_facade_never_accepts_caller_downgrade():
    with mock.patch.object(runner, "run_codex") as dispatched:
        runner.run_model_codex(["codex","exec","-"],env={"STORY_OS_MODEL_TRANSPORT_POLICY":"",
                          "PATH":"c:/fake"},input="text")
    assert dispatched.call_args.kwargs["env"]["STORY_OS_MODEL_TRANSPORT_POLICY"]=="DUAL_ONLY"
    assert dispatched.call_args.kwargs["env"]["PATH"]=="c:/fake"

def test_model_facade_disallowed_proxy_fails_before_subprocess():
    with mock.patch.dict(runner.os.environ, {"OPENAI_BASE_URL":"http://127.0.0.1:10100/v1"}):
        with mock.patch.object(runner.subprocess,"run") as launch:
            with pytest.raises(runner.CodexUserRunnerRejected,match="MODEL_TRANSPORT_FORBIDDEN"):
                runner.run_model_codex(["codex","exec","-"],input="prompt",timeout=1)
            launch.assert_not_called()

def test_canonical_producer_rejects_proxy_without_external_opt_in():
    task=runner.build_task(["codex","-c",'model_provider="opencodex"',"exec","-"],
         stdin_bytes=b"prompt",env={"STORY_OS_MODEL_TRANSPORT_POLICY":""})
    with mock.patch.object(runner,"bridge_required",return_value=False), mock.patch.object(
            runner,"resolve_codex") as resolver:
        with pytest.raises(runner.CodexUserRunnerRejected,match="MODEL_TRANSPORT_FORBIDDEN"):
            runner.execute_model_task(task)
        resolver.assert_not_called()

def test_subscription_image_controller_rejects_api_http_cli_provider(monkeypatch):
    import codex_subscription_image as image
    monkeypatch.setenv("STORY_OS_IMAGE_PROVIDER_ROUTE", "api_http")
    with pytest.raises(image.BackendError, match="API_KEY_DIRECT_IMAGE_EXECUTOR_REQUIRED"):
        image.controller_args()

def test_subscription_image_native_controller_no_longer_injects_custom_provider(monkeypatch):
    import codex_subscription_image as image
    monkeypatch.delenv("STORY_OS_IMAGE_PROVIDER_ROUTE", raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "http://127.0.0.1:10100/v1")
    argv = image.controller_args()
    assert not any("model_providers." in x or "storyos_http" in x for x in argv)
