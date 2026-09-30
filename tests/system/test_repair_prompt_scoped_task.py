from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_observability
import scoped_codex_worker


def test_repair_prompt_is_policy_bound_fingerprinted_and_receipt_reused(tmp_path):
    policy_sha = "d" * 64
    binding = {"role": "prompt.repair", "profile": "structured_text", "model": "gpt-6-luna",
               "reasoning_effort": "high", "policy_version": "frozen-v1",
               "model_policy_sha256": policy_sha}
    task_input = {
        "logical_asset_key": "episode/frame-03",
        "source_generation_key": "GK-1-F03",
        "source_artifact_sha256": "a" * 64,
        "review_receipt_sha256": "b" * 64,
        "failure_codes": ["KEY_PROP_DRIFT"],
        "failure_summary": "left hand prop missing",
        "original_production_prompt": "P01 in the same jacket holds the red folder at the gate",
        "frame_contract": {"character": "P01", "wardrobe": "same jacket"},
        "continuity_tags": {"character": "P01", "key_prop": "red folder"},
        "policy_sha256": policy_sha,
        "repair_wave_id": "episode/production/repair-wave-1",
    }
    stream_event = json.dumps({"type": "item.completed", "item": {"type": "agent_message",
        "text": json.dumps({"repair_instruction": "保持人物、外套、门口和机位，只补上左手红文件夹。"}, ensure_ascii=False)}})
    stream = stream_event + "\n" + json.dumps({"type": "turn.completed"}) + "\n"
    calls = []

    def fake_execute(_ep, step, _binding, _prompt, *, call_id, output_handle, receipt_fields, **_kwargs):
        calls.append((step, call_id, receipt_fields))
        output_handle.write(stream)
        receipt = {"receipt_schema_version": 1, "episode_id": "external/test", "run_id": "run",
            "trace_id": "trace", "step": step, "call_id": call_id, "model_role": "prompt.repair",
            "profile": "structured_text", "requested_model": "gpt-6-luna", "effective_model": "gpt-6-luna",
            "reasoning_effort": "high", "model_policy_version": "frozen-v1",
            "model_policy_sha256": policy_sha, "provider": "codex_subscription", "runner": "codex exec",
            "started_at": "2026-01-01T00:00:00+00:00", "finished_at": "2026-01-01T00:00:01+00:00",
            "duration_ms": 1000, "status": "SUCCESS", "model_binding_source": "EPISODE_BOUND_MODEL_POLICY",
                "effective_model_source": "EXPLICIT_RUNTIME_BINDING", "scoped_output_stream": stream, **receipt_fields}
        runtime_observability.write_model_execution_receipt(_ep, receipt=receipt)
        return 0, receipt

    with patch.object(scoped_codex_worker.model_policy, "resolve", return_value=binding), \
         patch.object(scoped_codex_worker, "execute_model_call", side_effect=fake_execute):
        first = scoped_codex_worker.run_repair_prompt_task(tmp_path, task_input=task_input)
        second = scoped_codex_worker.run_repair_prompt_task(tmp_path, task_input=task_input)
        Path(second["prompt_path"]).unlink()
        crash_recovered = scoped_codex_worker.run_repair_prompt_task(tmp_path, task_input=task_input)

    assert first["status"] == "SUCCESS"
    assert second["status"] == "REUSED"
    assert crash_recovered["status"] == "REUSED"
    assert first["fingerprint"] == second["fingerprint"]
    assert len(calls) == 1
    assert calls[0][0] == "REPAIR_PROMPT"
    assert calls[0][2]["source_generation_key"] == "GK-1-F03"
    assert calls[0][2]["source_artifact_sha256"] == "a" * 64
    assert calls[0][2]["review_receipt_sha256"] == "b" * 64
    output = Path(first["prompt_path"]).read_text(encoding="utf-8")
    assert "只补上左手红文件夹" in output
