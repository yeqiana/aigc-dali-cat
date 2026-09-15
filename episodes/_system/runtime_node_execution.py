"""Append-only node execution facts; these records are not Gate verdicts."""
from __future__ import annotations
import datetime as dt, hashlib, threading
import json
from pathlib import Path

REL = Path("meta/runtime/node-execution.jsonl")
_LOCK=threading.RLock()
OUTPUT_INLINE_BYTES = 512
OUTPUT_PREVIEW_CHARS = 240

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def compact_output(output):
    """Keep node evidence useful without embedding whole planner/result documents.

    Small values remain verbatim for backwards-readable diagnostics. Large values
    become a deterministic fingerprint + size + short preview. No production
    decision reads this field; formal artifacts stay referenced through
    ``evidence`` / ``output_sha`` instead.
    """
    if output is None:
        return None
    try:
        raw = json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        kind = type(output).__name__
    except (TypeError, ValueError):
        raw = str(output)
        kind = type(output).__name__
    encoded = raw.encode("utf-8", errors="replace")
    if len(encoded) <= OUTPUT_INLINE_BYTES:
        return output
    return {
        "compacted": True,
        "type": kind,
        "bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "preview": raw[:OUTPUT_PREVIEW_CHARS],
    }


def record(ep: Path, *, node_id: str, start_time: str, end_time: str, status: str,
           attempt: int = 1, output=None, evidence=None, task_id=None, snapshot_id=None,
           worker_id=None, input_sha=None, output_sha=None, stale=False, failure_type=None) -> dict:
    if isinstance(attempt, bool) or int(attempt) < 1:
        raise ValueError("attempt must be at least 1")
    row = {"node_id": str(node_id), "start_time": str(start_time), "end_time": str(end_time),
           "status": str(status), "attempt": int(attempt), "output": compact_output(output),
           "evidence": list(evidence or []), "gate_pass": None, "episode_state_mutated": False}
    row.update({"task_id":task_id,"snapshot_id":snapshot_id,"worker_id":worker_id,"input_sha":input_sha,
                "output_sha":output_sha,"stale":bool(stale),"failure_type":failure_type})
    path = Path(ep) / REL; path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return row
