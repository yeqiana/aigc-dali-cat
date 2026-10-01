from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import phase5a_collaborative_canary as canary  # noqa: E402
import codex_subscription_image  # noqa: E402
import codex_user_runner  # noqa: E402
import model_policy  # noqa: E402
import runtime_observability  # noqa: E402


def test_exact_probe_uses_episode_bound_luna_high_and_codex_auth_context(monkeypatch, tmp_path):
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
    monkeypatch.setattr(codex_subscription_image, "resolve_codex",
                        lambda _codex: Path("codex.exe"))
    monkeypatch.setattr(codex_subscription_image, "image_runtime_preflight",
                        lambda **_kwargs: {"auth_context_present": True})
    monkeypatch.setattr(codex_subscription_image, "command_prefix",
                        lambda _exe: ["codex.exe"])
    monkeypatch.setattr(codex_subscription_image, "controller_args",
                        lambda _ep: ["-m", "gpt-6-luna", "-c", 'model_reasoning_effort="high"'])
    monkeypatch.setattr(codex_user_runner, "bridge_required", lambda: True)

    def run_codex(argv, **kwargs):
        calls["argv"] = argv
        calls["kwargs"] = kwargs
        stream = (
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"{\\"capability_probe\\":\\"PASS\\"}"}}\n'
            '{"type":"turn.completed","usage":{}}\n'
        )
        return subprocess.CompletedProcess(argv, 0, stream)

    monkeypatch.setattr(codex_user_runner, "run_codex", run_codex)
    monkeypatch.setattr(runtime_observability, "write_model_execution_receipt",
                        lambda _ep, *, receipt: episode / (receipt["call_id"] + ".json"))

    result = canary.exact_controller_capability_preflight(episode, codex="codex.exe", timeout=5)

    assert result["status"] == "PASS"
    assert calls["argv"][calls["argv"].index("-m") + 1] == "gpt-6-luna"
    assert 'model_reasoning_effort="high"' in calls["argv"]
    assert calls["kwargs"]["task_type"] == "smoke"
    assert calls["kwargs"]["input"].find('"capability_probe":"PASS"') >= 0
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
    image = codex_subscription_image
    monkeypatch.setattr(image, "resolve_codex", lambda _codex: Path("codex.exe"))
    monkeypatch.setattr(image, "image_runtime_preflight", lambda **_kwargs: {})
    monkeypatch.setattr(image, "command_prefix", lambda _exe: ["codex.exe"])
    monkeypatch.setattr(image, "controller_args",
                        lambda _ep: ["-m", "gpt-6-luna", "-c", 'model_reasoning_effort="high"'])
    runner = codex_user_runner
    monkeypatch.setattr(runner, "bridge_required", lambda: False)
    monkeypatch.setattr(runner, "run_codex", lambda argv, **_kwargs:
                        subprocess.CompletedProcess(argv, 1, "HTTP 400 model unsupported"))
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
    monkeypatch.setattr(codex_subscription_image, "resolve_codex", lambda _codex: Path("codex.exe"))
    monkeypatch.setattr(codex_subscription_image, "image_runtime_preflight", lambda **_kwargs: {})
    monkeypatch.setattr(codex_subscription_image, "command_prefix", lambda _exe: ["codex.exe"])
    monkeypatch.setattr(codex_subscription_image, "controller_args",
                        lambda _ep: ["-m", "gpt-6-luna", "-c", 'model_reasoning_effort="high"'])
    monkeypatch.setattr(codex_user_runner, "bridge_required", lambda: False)
    stream = (
        '{"type":"item.completed","item":{"type":"agent_message",'
        '"text":"{\\"capability_probe\\":\\"NOT_PASS\\"}"}}\n'
        '{"type":"turn.completed","usage":{}}\n'
    )
    monkeypatch.setattr(codex_user_runner, "run_codex", lambda argv, **_kwargs:
                        subprocess.CompletedProcess(argv, 0, stream))
    saved = {}
    monkeypatch.setattr(runtime_observability, "write_model_execution_receipt",
                        lambda _ep, *, receipt: saved.update(receipt) or episode / "probe.json")

    result = canary.exact_controller_capability_preflight(episode, timeout=5)

    assert result["status"] == "BLOCKED"
    assert result["failure_class"] == "PROBE_RESULT_INVALID"
    assert saved["probe_result_valid"] is False
    assert saved["image_attempt_authority_called"] is False
