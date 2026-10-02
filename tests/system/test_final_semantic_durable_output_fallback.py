from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_critic_runner


def _durable_record(request_id: str, log_text: str) -> dict:
    return {
        "schema_version": 1,
        "request_id": request_id,
        "returncode": 0,
        "output_base64": base64.b64encode(log_text.encode("utf-8")).decode("ascii"),
        "evidence": {},
    }


def test_final_semantic_durable_projection_uses_schema_output_when_agent_message_is_prose(tmp_path, monkeypatch):
    ep = tmp_path / "episode"
    ep.mkdir()
    candidate = ep / "meta" / ".frame-semantic-review.candidate.json"
    candidate.parent.mkdir(parents=True)
    structured = {"frames": [{"frame": "01", "decision": "pass", "issue_codes": []}]}
    candidate.write_text(json.dumps(structured, ensure_ascii=False), encoding="utf-8")

    log_text = "\n".join([
        json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
        json.dumps({"type": "item.completed", "item": {
            "type": "agent_message", "text": "审查完成：帧 01 通过。"
        }}, ensure_ascii=False),
        json.dumps({"type": "turn.completed", "usage": {}}),
    ])
    request_id = "request-01"
    durable = _durable_record(request_id, log_text)
    durable_path = tmp_path / "runner-result.json"
    durable_path.write_text(json.dumps(durable), encoding="utf-8")
    monkeypatch.setattr(codex_critic_runner.codex_user_runner, "task_result_path", lambda _rid: durable_path)
    monkeypatch.setattr(codex_critic_runner.codex_user_runner, "read_task_result", lambda _rid: durable)

    receipt = codex_critic_runner._persist_final_semantic_durable_result(
        ep, {"request_id": request_id}, 0, output_path=candidate)

    assert receipt["durable_result_status"] == "VALIDATED"
    projection = json.loads((ep / receipt["result_ref"]).read_text(encoding="utf-8"))
    assert projection["structured_result"] == structured
    assert projection["structured_result_source"] == "CODEX_OUTPUT_FILE"
    assert projection["turn_completed"] is True


def test_final_semantic_output_fallback_rejects_file_outside_episode(tmp_path, monkeypatch):
    ep = tmp_path / "episode"
    ep.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text('{"decision":"pass"}', encoding="utf-8")
    request_id = "request-02"
    log_text = "\n".join([
        json.dumps({"type": "item.completed", "item": {
            "type": "agent_message", "text": "审查完成。"
        }}, ensure_ascii=False),
        json.dumps({"type": "turn.completed"}),
    ])
    durable = _durable_record(request_id, log_text)
    durable_path = tmp_path / "runner-result-2.json"
    durable_path.write_text(json.dumps(durable), encoding="utf-8")
    monkeypatch.setattr(codex_critic_runner.codex_user_runner, "task_result_path", lambda _rid: durable_path)
    monkeypatch.setattr(codex_critic_runner.codex_user_runner, "read_task_result", lambda _rid: durable)

    receipt = codex_critic_runner._persist_final_semantic_durable_result(
        ep, {"request_id": request_id}, 0, output_path=outside)

    assert receipt == {"durable_result_status": "OUTPUT_PATH_OUTSIDE_EPISODE"}
