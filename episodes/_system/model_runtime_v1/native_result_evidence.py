"""Post-dispatch native Codex CLI evidence inspection (never a preflight attestation).

Only describes a completed CLI process with runner-owned provenance. This is NOT
an independent proof of its selected model, tool registry, image capability or
Review Authority.
"""
from __future__ import annotations
import json

OFFICIAL_BACKEND="https://chatgpt.com/backend-api/codex"
COMPLETED={"turn.completed"}
FAILED={"turn.failed","error"}

def inspect(result) -> dict:
    remote=getattr(result,"remote",None)
    if not isinstance(remote,dict):
        return {"status":"UNVERIFIED","reason":"RUNNER_REMOTE_EVIDENCE_MISSING","actual_model":None}
    if (remote.get("transport_route")!="native_codex" or
        str(remote.get("transport_base_url") or "").rstrip("/")!=OFFICIAL_BACKEND):
        return {"status":"UNVERIFIED","reason":"NATIVE_ROUTE_NOT_ATTESTED","actual_model":None}
    if remote.get("timed_out") is not False or getattr(result,"returncode",None)!=0:
        return {"status":"UNVERIFIED","reason":"RUNNER_NOT_COMPLETED","actual_model":None}
    raw=getattr(result,"stdout",None)
    if isinstance(raw,bytes):
        try:
            raw=raw.decode("utf-8")
        except UnicodeDecodeError:
            return {"status":"UNVERIFIED","reason":"CODEX_JSONL_INVALID","actual_model":None}
    if not isinstance(raw,str) or not raw.strip():
        return {"status":"UNVERIFIED","reason":"CODEX_JSONL_MISSING","actual_model":None}
    events=[]
    try:
        for line in raw.splitlines():
            if line.strip():
                value=json.loads(line)
                if not isinstance(value,dict):
                    raise ValueError("non-object")
                events.append(value)
    except (ValueError,TypeError):
        return {"status":"UNVERIFIED","reason":"CODEX_JSONL_INVALID","actual_model":None}
    kinds=[row.get("type") for row in events]
    if any(kind in FAILED for kind in kinds):
        return {"status":"UNVERIFIED","reason":"CODEX_EXECUTION_FAILED_EVENT","actual_model":None}
    if not any(kind in COMPLETED for kind in kinds):
        return {"status":"UNVERIFIED","reason":"CODEX_TERMINAL_EVENT_MISSING","actual_model":None}
    messages=[row["item"]["text"] for row in events
              if row.get("type")=="item.completed"
              and isinstance(row.get("item"),dict)
              and row["item"].get("type")=="agent_message"
              and isinstance(row["item"].get("text"),str)
              and row["item"]["text"].strip()]
    return {"status":"OBSERVED","reason":"NATIVE_CLI_COMPLETED",
            "transport":"CODEX_NATIVE","actual_model":None,
            "output_text":messages[-1] if messages else None,
            "capability_status":"UNKNOWN","tool_session_attested":False,
            "review_authority_granted":False}
