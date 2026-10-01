from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_critic_runner


def _durable_jsonl(*, turn_completed: bool = True) -> bytes:
    rows = [{
        "type": "item.completed",
        "item": {"type": "agent_message", "text": '{"decision":"pass"}'},
    }]
    if turn_completed:
        rows.append({"type": "turn.completed"})
    return ("\n".join(json.dumps(row) for row in rows) + "\n").encode("utf-8")


def _launch_final_receipt(tmp_path, monkeypatch, durable):
    episode = tmp_path / "episode"
    episode.mkdir()
    monkeypatch.setattr(codex_critic_runner, "prefix", lambda _codex: ["codex"])
    monkeypatch.setattr(codex_critic_runner, "resolve_sandbox", lambda _sandbox: "read-only")
    monkeypatch.setattr("runtime_trace.current", lambda _ep: {})
    durable_path = tmp_path / "runner-result.json"

    def fake_run(_cmd, **kwargs):
        kwargs["stdout"].write('{"type":"turn.completed"}\n')
        return SimpleNamespace(returncode=0, remote={"request_id": "a" * 32, "thread_id": "thread-1"})

    def fake_read_task_result(request_id):
        value = durable(request_id)
        if value:
            durable_path.write_text(json.dumps(value), encoding="utf-8")
        return value

    monkeypatch.setattr("codex_user_runner.run_codex", fake_run)
    monkeypatch.setattr("codex_user_runner.task_result_path", lambda _request_id: durable_path)
    monkeypatch.setattr("codex_user_runner.read_task_result", fake_read_task_result)
    result = codex_critic_runner.launch(
        "TEST_ONLY final review", codex="codex", root=tmp_path, timeout=10,
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
    return episode, json.loads(receipt_path.read_text(encoding="utf-8"))


def test_final_semantic_receipt_is_always_provisional_and_binds_durable_bytes(tmp_path, monkeypatch):
    raw = _durable_jsonl()
    episode, receipt = _launch_final_receipt(
        tmp_path,
        monkeypatch,
        lambda request_id: {
            "request_id": request_id,
            "returncode": 0,
            "output_base64": base64.b64encode(raw).decode("ascii"),
        },
    )

    assert receipt["status"] == "PENDING_VALIDATION"
    assert "defer_final_semantic_success" not in receipt
    assert receipt["runner_request_id"] == "a" * 32
    assert receipt["result_sha256_source"] == "USER_RUNNER_DURABLE_RESULT_PROJECTION"
    assert receipt["execution_completion_source"] == "USER_RUNNER_DURABLE_RESULT"
    result_path = episode / receipt["result_ref"]
    projection_bytes = result_path.read_bytes()
    projection = json.loads(projection_bytes)
    assert hashlib.sha256(projection_bytes).hexdigest() == receipt["result_sha256"]
    assert projection["request_id"] == receipt["runner_request_id"]
    assert projection["turn_completed"] is True
    assert projection["structured_result"] == {"decision": "pass"}
    assert projection["output_sha256"] == hashlib.sha256(raw).hexdigest()


def test_final_semantic_missing_durable_result_cannot_become_success(tmp_path, monkeypatch):
    _episode, receipt = _launch_final_receipt(tmp_path, monkeypatch, lambda _request_id: {})

    assert receipt["status"] == "PENDING_VALIDATION"
    assert receipt["durable_result_status"] == "MISSING_OR_MISMATCHED"
    assert "result_ref" not in receipt
    assert "result_sha256" not in receipt


def test_final_semantic_missing_turn_completion_cannot_become_success(tmp_path, monkeypatch):
    raw = _durable_jsonl(turn_completed=False)
    _episode, receipt = _launch_final_receipt(
        tmp_path,
        monkeypatch,
        lambda request_id: {
            "request_id": request_id,
            "returncode": 0,
            "output_base64": base64.b64encode(raw).decode("ascii"),
        },
    )

    assert receipt["status"] == "PENDING_VALIDATION"
    assert receipt["durable_result_status"] == "TURN_NOT_COMPLETED"
    assert "result_ref" not in receipt
    assert "result_sha256" not in receipt


def test_final_semantic_missing_structured_result_cannot_become_success(tmp_path, monkeypatch):
    raw = (json.dumps({"type": "turn.completed"}) + "\n").encode("utf-8")
    _episode, receipt = _launch_final_receipt(
        tmp_path,
        monkeypatch,
        lambda request_id: {
            "request_id": request_id,
            "returncode": 0,
            "output_base64": base64.b64encode(raw).decode("ascii"),
        },
    )

    assert receipt["status"] == "PENDING_VALIDATION"
    assert receipt["durable_result_status"] == "STRUCTURED_RESULT_MISSING"
    assert "result_ref" not in receipt
    assert "result_sha256" not in receipt
