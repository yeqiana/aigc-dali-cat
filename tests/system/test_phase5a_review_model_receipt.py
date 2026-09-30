from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_critic_runner


def test_critic_runner_records_bound_model_receipt_without_provider_attestation(tmp_path, monkeypatch):
    episode = tmp_path / "episodes" / "_canary" / "phase5a-test"
    episode.mkdir(parents=True)
    monkeypatch.setattr(codex_critic_runner, "prefix", lambda _codex: ["codex"])
    monkeypatch.setattr(codex_critic_runner, "resolve_sandbox", lambda _sandbox: "workspace-write")
    monkeypatch.setattr("runtime_trace.current", lambda _ep: {"run_id": "canary-run", "trace_id": "canary-trace"})

    def fake_run(_cmd, **kwargs):
        kwargs["stdout"].write('{"type":"turn.completed"}\n')
        return SimpleNamespace(returncode=0, remote={})

    monkeypatch.setattr("codex_user_runner.run_codex", fake_run)
    result = codex_critic_runner.launch(
        "TEST_ONLY review", codex="codex", root=tmp_path, timeout=10,
        model="gpt-6-luna", reasoning_effort="high",
        log_path=episode / "meta" / "critic.jsonl",
        model_execution_context={
            "episode": episode,
            "model_role": "vision.final",
            "profile": "vision_final",
            "model_policy_version": "test-frozen-policy",
            "model_policy_sha256": "a" * 64,
            "logical_asset_key": "canary/frame-01",
            "generation_key": "canary/frame-01/attempt-1",
            "attempt_index": 1,
            "artifact_sha256": "b" * 64,
        },
    )

    receipt_path = tmp_path / result.model_execution_receipt
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["model_role"] == "vision.final"
    assert receipt["profile"] == "vision_final"
    assert receipt["effective_model"] == "gpt-6-luna"
    assert receipt["reasoning_effort"] == "high"
    assert receipt["model_policy_sha256"] == "a" * 64
    assert receipt["provider"] == "codex"
    assert receipt["runner"] == "codex_user_runner"
    assert receipt["run_id"] == "canary-run"
    assert receipt["trace_id"] == "canary-trace"
    assert receipt["effective_model_source"] == "EXPLICIT_RUNTIME_BINDING"
    assert receipt["model_binding_source"] == "EPISODE_BOUND_POLICY"

