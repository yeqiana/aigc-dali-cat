from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import phase5a_collaborative_canary as canary  # noqa: E402
import codex_user_runner  # noqa: E402
import model_policy  # noqa: E402
import runtime_observability  # noqa: E402
import scoped_codex_worker  # noqa: E402
import image_payload_transport  # noqa: E402


def test_exact_probe_uses_regular_scoped_text_route_and_does_not_enable_image_tool(monkeypatch, tmp_path):
    episode = tmp_path / "episode"
    episode.mkdir()
    calls = {}
    binding = {
        "role": "image.controller", "profile": "image_controller",
        "model": "gpt-6-luna", "reasoning_effort": "high",
        "policy_version": "frozen-v1", "model_policy_sha256": "a" * 64,
    }
    original_resolve = model_policy.resolve
    monkeypatch.setattr(model_policy, "validate_bound_policy", lambda _ep: [])
    monkeypatch.setattr(model_policy, "resolve", lambda role, **kwargs:
                        dict(binding) if role == "image.controller" else original_resolve(role, **kwargs))
    monkeypatch.setattr(codex_user_runner, "bridge_required", lambda: True)

    def execute_model_call(_ep, step, actual_binding, prompt, **kwargs):
        calls.update(step=step, binding=actual_binding, prompt=prompt, kwargs=kwargs)
        kwargs["output_handle"].write(
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"{\\"capability_probe\\":\\"PASS\\"}"}}\n'
            '{"type":"turn.completed","usage":{}}\n'
        )
        return 0, {
            "receipt_schema_version": 1, "status": "SUCCESS", "call_id": kwargs["call_id"],
            "step": step, "codex_argv": ["codex", "exec", "-m", "gpt-6-luna", "-c",
                                           'model_reasoning_effort="high"'],
            "model_role": actual_binding["role"], "profile": actual_binding["profile"],
            "requested_model": actual_binding["model"], "effective_model": actual_binding["model"],
            "reasoning_effort": actual_binding["reasoning_effort"],
            "model_policy_version": actual_binding["policy_version"],
            "model_policy_sha256": actual_binding["model_policy_sha256"],
            "started_at": "2026-10-01T00:00:00Z", "finished_at": "2026-10-01T00:00:01Z",
            "duration_ms": 1000,
        }

    monkeypatch.setattr(scoped_codex_worker, "execute_model_call", execute_model_call)
    monkeypatch.setattr(runtime_observability, "write_model_execution_receipt",
                        lambda _ep, *, receipt: episode / (receipt["call_id"] + ".json"))

    result = canary.exact_controller_capability_preflight(episode, codex="codex.exe", timeout=5)

    assert result["status"] == "PASS"
    assert calls["step"] == "EXACT_CONTROLLER_CAPABILITY_PREFLIGHT"
    assert calls["kwargs"]["sandbox"] == "read-only"
    assert calls["kwargs"].get("image_paths", ()) == ()
    assert calls["kwargs"]["receipt_fields"]["image_generation_enabled"] is False
    assert calls["prompt"].find('"capability_probe":"PASS"') >= 0
    assert "-m" in result["receipt"]["codex_argv"]
    assert "gpt-6-luna" in result["receipt"]["codex_argv"]
    assert 'model_reasoning_effort="high"' in result["receipt"]["codex_argv"]
    assert result["receipt"]["effective_model_source"] == "EXPLICIT_RUNTIME_BINDING"
    assert result["receipt"]["model_policy_sha256"] == "a" * 64
    assert result["receipt"]["image_generation_called"] is False
    assert result["receipt"]["image_attempt_authority_called"] is False
    assert result["receipt"]["probe_result_valid"] is True
    assert "stdout" not in result["receipt"]
    assert "token" not in result["receipt"]


def test_unsupported_controller_blocks_before_global_claim_scheduler_or_attempt(monkeypatch, tmp_path):
    episode = tmp_path / "canary"
    episode.mkdir()
    (episode / "meta").mkdir()
    (episode / "meta/release-manifest.json").write_text("{}", encoding="utf-8")
    calls = []
    monkeypatch.setattr(canary, "_preflight", lambda *_a, **_k: {
        "episode": episode, "logical_asset_key": "canary/frame-01",
        "runtime_request_id": "request-1", "policy_sha256": "a" * 64,
    })
    monkeypatch.setattr(image_payload_transport, "payload_capability_preflight", lambda **_k: {
        "status": "PASS", "provider": "codex_subscription",
        "transport_model": "gpt-5.6-sol", "transport_effort": "low",
    })
    original_resolve = model_policy.resolve
    monkeypatch.setattr(model_policy, "resolve", lambda role, **kwargs:
                        ({"model": "gpt-image-2.5-flare", "quality": "high"}
                         if role == "image.payload" else original_resolve(role, **kwargs)))
    monkeypatch.setattr(canary, "exact_controller_capability_preflight", lambda *_a, **_k: {
        "status": "BLOCKED", "failure_class": "MODEL_UNAVAILABLE",
    })
    monkeypatch.setattr(canary, "claim_global_canary", lambda *_a, **_k: calls.append("claim"))
    monkeypatch.setattr(canary, "_telemetry", lambda *_a, **_k: None)
    monkeypatch.setattr(__import__("runtime_trace"), "start_run",
                        lambda *_a, **_k: calls.append("trace") or "trace")
    monkeypatch.setattr(__import__("generation_attempt_authority"), "reserve",
                        lambda *_a, **_k: calls.append("reserve"))
    monkeypatch.setattr(__import__("image_scheduler"), "run_scheduler_async",
                        lambda *_a, **_k: calls.append("scheduler"))

    result = canary.run_production_subpath(episode, canary_id="test-canary")

    assert result["status"] == "CANARY_CONTROLLER_PREFLIGHT_BLOCKED"
    assert result["image_attempt_reserve_called"] is False
    assert result["image_scheduler_called"] is False
    assert calls == []


def test_payload_provider_missing_blocks_before_controller_or_attempt(monkeypatch, tmp_path):
    episode = tmp_path / "canary"
    episode.mkdir()
    calls = []
    monkeypatch.setattr(canary, "_preflight", lambda *_a, **_k: {
        "episode": episode, "logical_asset_key": "canary/frame-01",
        "runtime_request_id": "request-1", "policy_sha256": "a" * 64,
    })
    original_resolve = model_policy.resolve
    monkeypatch.setattr(model_policy, "resolve", lambda role, **kwargs:
                        ({"model": "gpt-image-2.5-flare", "quality": "high"}
                         if role == "image.payload" else original_resolve(role, **kwargs)))
    monkeypatch.setattr(image_payload_transport, "payload_capability_preflight", lambda **_k: {
        "status": "BLOCKED", "failure_class": "LOGIN_AUTH_IMAGE_TOOL_UNAVAILABLE",
        "provider": "codex_subscription", "image_attempt_authority_called": False,
    })
    monkeypatch.setattr(canary, "exact_controller_capability_preflight",
                        lambda *_a, **_k: calls.append("controller"))
    monkeypatch.setattr(canary, "claim_global_canary", lambda *_a, **_k: calls.append("claim"))
    monkeypatch.setattr(canary, "_telemetry", lambda *_a, **_k: None)
    monkeypatch.setattr(__import__("generation_attempt_authority"), "reserve",
                        lambda *_a, **_k: calls.append("reserve"))
    monkeypatch.setattr(__import__("image_scheduler"), "run_scheduler_async",
                        lambda *_a, **_k: calls.append("scheduler"))

    result = canary.run_production_subpath(episode, canary_id="test-canary")

    assert result["status"] == "CANARY_PAYLOAD_PREFLIGHT_BLOCKED"
    assert result["failure_class"] == "LOGIN_AUTH_IMAGE_TOOL_UNAVAILABLE"
    assert result["image_attempt_reserve_called"] is False
    assert result["image_scheduler_called"] is False
    assert result["controller_preflight_called"] is False
    assert calls == []


def test_probe_nonzero_result_is_blocked_and_records_exact_model_binding(monkeypatch, tmp_path):
    episode = tmp_path / "episode"
    episode.mkdir()
    binding = {
        "role": "image.controller", "profile": "image_controller",
        "model": "gpt-6-luna", "reasoning_effort": "high",
        "policy_version": "frozen-v1", "model_policy_sha256": "b" * 64,
    }
    original_resolve = model_policy.resolve
    monkeypatch.setattr(model_policy, "validate_bound_policy", lambda _ep: [])
    monkeypatch.setattr(model_policy, "resolve", lambda role, **kwargs:
                        dict(binding) if role == "image.controller" else original_resolve(role, **kwargs))
    monkeypatch.setattr(codex_user_runner, "bridge_required", lambda: False)
    def unsupported(_ep, step, actual_binding, _prompt, **kwargs):
        kwargs["output_handle"].write("HTTP 400 model unsupported")
        return 1, {"status": "FAILED", "call_id": kwargs["call_id"], "step": step,
                   "codex_argv": ["codex", "exec", "-m", "gpt-6-luna", "-c",
                                  'model_reasoning_effort="high"'],
                   "model_role": actual_binding["role"], "profile": actual_binding["profile"],
                   "requested_model": actual_binding["model"],
                   "reasoning_effort": actual_binding["reasoning_effort"],
                   "model_policy_version": actual_binding["policy_version"],
                   "model_policy_sha256": actual_binding["model_policy_sha256"],
                   "started_at": "start", "finished_at": "finish", "duration_ms": 1}
    monkeypatch.setattr(scoped_codex_worker, "execute_model_call", unsupported)
    saved = {}
    monkeypatch.setattr(runtime_observability, "write_model_execution_receipt",
                        lambda _ep, *, receipt: saved.update(receipt) or episode / "probe.json")

    result = canary.exact_controller_capability_preflight(episode, timeout=5)

    assert result["status"] == "BLOCKED"
    assert result["failure_class"] == "MODEL_UNAVAILABLE"
    assert saved["requested_model"] == "gpt-6-luna"
    assert saved["reasoning_effort"] == "high"
    assert saved["returncode"] == 1
    assert saved["image_attempt_authority_called"] is False
    assert "stdout" not in saved
    assert "token" not in saved


def test_zero_exit_without_exact_completed_sentinel_fails_closed(monkeypatch, tmp_path):
    episode = tmp_path / "episode"
    episode.mkdir()
    binding = {
        "role": "image.controller", "profile": "image_controller",
        "model": "gpt-6-luna", "reasoning_effort": "high",
        "policy_version": "frozen-v1", "model_policy_sha256": "c" * 64,
    }
    original_resolve = model_policy.resolve
    monkeypatch.setattr(model_policy, "validate_bound_policy", lambda _ep: [])
    monkeypatch.setattr(model_policy, "resolve", lambda role, **kwargs:
                        dict(binding) if role == "image.controller" else original_resolve(role, **kwargs))
    monkeypatch.setattr(codex_user_runner, "bridge_required", lambda: False)
    def wrong_sentinel(_ep, step, actual_binding, _prompt, **kwargs):
        kwargs["output_handle"].write(
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"{\\"capability_probe\\":\\"NOT_PASS\\"}"}}\n'
            '{"type":"turn.completed","usage":{}}\n'
        )
        return 0, {"status": "SUCCESS", "call_id": kwargs["call_id"], "step": step,
                   "codex_argv": ["codex", "exec", "-m", "gpt-6-luna", "-c",
                                  'model_reasoning_effort="high"'],
                   "model_role": actual_binding["role"], "profile": actual_binding["profile"],
                   "requested_model": actual_binding["model"],
                   "reasoning_effort": actual_binding["reasoning_effort"],
                   "model_policy_version": actual_binding["policy_version"],
                   "model_policy_sha256": actual_binding["model_policy_sha256"],
                   "started_at": "start", "finished_at": "finish", "duration_ms": 1}
    monkeypatch.setattr(scoped_codex_worker, "execute_model_call", wrong_sentinel)
    saved = {}
    monkeypatch.setattr(runtime_observability, "write_model_execution_receipt",
                        lambda _ep, *, receipt: saved.update(receipt) or episode / "probe.json")

    result = canary.exact_controller_capability_preflight(episode, timeout=5)

    assert result["status"] == "BLOCKED"
    assert result["failure_class"] == "PROBE_RESULT_INVALID"
    assert saved["probe_result_valid"] is False
    assert saved["image_attempt_authority_called"] is False


def test_controller_diagnostics_classify_local_websocket_426_without_raw_output():
    failure, evidence = canary._controller_failure_diagnostics(
        "failed to connect to websocket: HTTP error: 426 Upgrade Required "
        "URL ws://127.0.0.1:10100/v1/responses",
        1,
        {"request_id": "req-safe-id", "durable_result_present": True},
    )

    assert failure == "CONTROLLER_PROTOCOL_FAILURE"
    assert evidence == {
        "protocol_failure_type": "TRANSPORT_WEBSOCKET_UPGRADE_REJECTED",
        "http_status": 426,
        "websocket_attempted": True,
        "endpoint_class": "LOCAL_PROXY",
        "runner_request_id": "req-safe-id",
        "durable_result_present": True,
    }


def test_controller_diagnostics_do_not_classify_any_model_mention_as_unavailable():
    failure, evidence = canary._controller_failure_diagnostics(
        "model policy execution failed in scoped runtime", 1
    )

    assert failure == "CONTROLLER_EXECUTION_FAILED"
    assert evidence["http_status"] is None
    assert evidence["protocol_failure_type"] is None
    assert evidence["endpoint_class"] == "UNKNOWN"
