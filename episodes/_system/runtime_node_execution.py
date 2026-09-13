"""Append-only node execution facts; these records are not Gate verdicts."""
from __future__ import annotations
import datetime as dt, threading
import json
from pathlib import Path

REL = Path("meta/runtime/node-execution.jsonl")
_LOCK=threading.RLock()

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def record(ep: Path, *, node_id: str, start_time: str, end_time: str, status: str,
           attempt: int = 1, output=None, evidence=None, task_id=None, snapshot_id=None,
           worker_id=None, input_sha=None, output_sha=None, stale=False, failure_type=None) -> dict:
    if isinstance(attempt, bool) or int(attempt) < 1:
        raise ValueError("attempt must be at least 1")
    row = {"node_id": str(node_id), "start_time": str(start_time), "end_time": str(end_time),
           "status": str(status), "attempt": int(attempt), "output": output,
           "evidence": list(evidence or []), "gate_pass": None, "episode_state_mutated": False}
    row.update({"task_id":task_id,"snapshot_id":snapshot_id,"worker_id":worker_id,"input_sha":input_sha,
                "output_sha":output_sha,"stale":bool(stale),"failure_type":failure_type})
    path = Path(ep) / REL; path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return row
