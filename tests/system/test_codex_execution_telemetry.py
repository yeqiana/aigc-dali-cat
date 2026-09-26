from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_execution_telemetry as telemetry


def _result(rows, *, elapsed=12.5, rc=0, timed_out=False):
    output = "\n".join(json.dumps(row) for row in rows).encode()
    return SimpleNamespace(
        returncode=rc,
        output=output,
        remote={
            "elapsed_seconds": elapsed,
            "timed_out": timed_out,
            "request_id": "abc",
            "task_type": "scoped_step",
            "codex_resolution": "runner_resolved",
        },
    )


def test_turn_completed_usage_and_runner_receipt_form_complete_telemetry():
    result = _result([
        {"type": "thread.started", "thread_id": "t"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": '{"character":{}}'}},
        {"type": "turn.completed", "usage": {
            "input_tokens": 100,
            "cached_input_tokens": 20,
            "output_tokens": 30,
            "reasoning_output_tokens": 4,
        }},
    ])
    row = telemetry.model_execution(
        result, provider="codex", model="default", authority_capsule_read_once=True
    )
    assert row["wall_seconds"] == 12.5
    assert row["input_tokens"] == 100
    assert row["output_tokens"] == 30
    assert row["repeated_reads"] == 0
    assert row["failure"] is False
    assert row["timeout"] is False
    assert row["tool_free"] is True


def test_tool_activity_does_not_guess_repeated_reads():
    result = _result([
        {"type": "item.completed", "item": {"type": "command_execution", "command": "cat x"}},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}},
        {"type": "turn.completed", "usage": {"input_tokens": 5, "output_tokens": 1}},
    ])
    row = telemetry.model_execution(
        result, provider="codex", model="default", authority_capsule_read_once=True
    )
    assert row["repeated_reads"] is None
    assert row["tool_free"] is False


def test_missing_usage_stays_missing():
    row = telemetry.model_execution(
        _result([{"type": "item.completed", "item": {"type": "agent_message", "text": "{}"}}]),
        provider="codex",
        model="default",
        authority_capsule_read_once=True,
    )
    assert row["input_tokens"] is None
    assert row["output_tokens"] is None


def test_final_agent_message_and_json_parser():
    fence = chr(96) * 3
    result = _result([
        {"type": "item.completed", "item": {"type": "agent_message", "text": fence + 'json\n{"a":1}\n' + fence}},
        {"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}},
    ])
    assert telemetry.parse_json_object(telemetry.final_agent_message(result)) == {"a": 1}