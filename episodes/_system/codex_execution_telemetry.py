"""Normalize explicit Codex JSONL and user-runner receipts into model telemetry.

No missing value is estimated. Token counts come only from turn.completed usage;
wall, timeout and failure come from the user-runner receipt. repeated_reads=0 is
emitted only when the JSONL contains no tool/command item and the caller says
all authority was embedded in one frozen capsule.
"""
from __future__ import annotations

import json


def jsonl_rows(output: bytes | str) -> list[dict]:
    text = output.decode("utf-8", "replace") if isinstance(output, bytes) else str(output or "")
    rows: list[dict] = []
    for line in text.splitlines():
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def summarize_jsonl(output: bytes | str) -> dict:
    rows = jsonl_rows(output)
    input_tokens = 0
    output_tokens = 0
    cached_input_tokens = 0
    reasoning_output_tokens = 0
    cached_usage_complete = True
    reasoning_usage_complete = True
    usage_events = 0
    final_messages: list[str] = []
    non_message_items: list[str] = []
    for row in rows:
        if row.get("type") == "turn.completed":
            usage = row.get("usage") or {}
            if isinstance(usage, dict):
                inp = usage.get("input_tokens")
                out = usage.get("output_tokens")
                if type(inp) is int and type(out) is int:
                    usage_events += 1
                    input_tokens += inp
                    output_tokens += out
                    cached = usage.get("cached_input_tokens")
                    reasoning = usage.get("reasoning_output_tokens")
                    if type(cached) is int:
                        cached_input_tokens += cached
                    else:
                        cached_usage_complete = False
                    if type(reasoning) is int:
                        reasoning_output_tokens += reasoning
                    else:
                        reasoning_usage_complete = False
        if row.get("type") == "item.completed":
            item = row.get("item") or {}
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type") or "")
            if item_type == "agent_message":
                text = item.get("text")
                if isinstance(text, str):
                    final_messages.append(text)
            elif item_type:
                non_message_items.append(item_type)
    return {
        "rows": rows,
        "usage_events": usage_events,
        "input_tokens": input_tokens if usage_events else None,
        "output_tokens": output_tokens if usage_events else None,
        "cached_input_tokens": cached_input_tokens if usage_events and cached_usage_complete else None,
        "reasoning_output_tokens": reasoning_output_tokens if usage_events and reasoning_usage_complete else None,
        "usage_fields_complete": bool(usage_events and cached_usage_complete and reasoning_usage_complete),
        "final_message": final_messages[-1] if final_messages else None,
        "non_message_item_types": non_message_items,
        "tool_free": not non_message_items,
    }


def model_execution(
    result,
    *,
    provider: str,
    model: str,
    authority_capsule_read_once: bool,
) -> dict:
    parsed = summarize_jsonl(getattr(result, "output", b""))
    remote = dict(getattr(result, "remote", {}) or {})
    elapsed = remote.get("elapsed_seconds")
    timed_out = remote.get("timed_out")
    returncode = getattr(result, "returncode", None)
    repeated_reads = 0 if authority_capsule_read_once and parsed["tool_free"] else None
    return {
        "independent_task": True,
        "real_model_execution": True,
        "wall_seconds": float(elapsed) if isinstance(elapsed, (int, float)) and not isinstance(elapsed, bool) else None,
        "input_tokens": parsed["input_tokens"],
        "output_tokens": parsed["output_tokens"],
        "cached_input_tokens": parsed["cached_input_tokens"],
        "reasoning_output_tokens": parsed["reasoning_output_tokens"],
        "repeated_reads": repeated_reads,
        "failure": (returncode != 0) if type(returncode) is int else None,
        "timeout": bool(timed_out) if isinstance(timed_out, bool) else None,
        "returncode": returncode if type(returncode) is int else None,
        "provider": str(provider),
        "model": str(model),
        "telemetry_source": "codex_cli_jsonl.turn.completed+codex_user_runner.receipt",
        "usage_event_count": parsed["usage_events"],
        "tool_free": parsed["tool_free"],
        "non_message_item_types": list(parsed["non_message_item_types"]),
        "runner_request_id": remote.get("request_id"),
        "runner_task_type": remote.get("task_type"),
        "codex_resolution": remote.get("codex_resolution"),
    }


def final_agent_message(result) -> str:
    parsed = summarize_jsonl(getattr(result, "output", b""))
    text = parsed.get("final_message")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Codex JSONL has no final agent_message")
    return text.strip()


def parse_json_object(text: str) -> dict:
    raw = str(text or "").strip()
    fence = chr(96) * 3
    if raw.startswith(fence):
        lines = raw.splitlines()
        if lines and lines[0].startswith(fence):
            lines = lines[1:]
        if lines and lines[-1].strip() == fence:
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    try:
        value = json.loads(raw)
    except Exception:
        first = raw.find("{")
        last = raw.rfind("}")
        if first < 0 or last <= first:
            raise ValueError("model final message is not a JSON object")
        value = json.loads(raw[first:last + 1])
    if not isinstance(value, dict):
        raise ValueError("model final message must be a JSON object")
    return value
