"""Append-only node execution facts; these records are not Gate verdicts."""
from __future__ import annotations
import argparse
import datetime as dt, hashlib, threading
import json
from pathlib import Path
from episode_performance import seconds_between

REL = Path("meta/runtime/node-execution.jsonl")
_LOCK=threading.RLock()
OUTPUT_INLINE_BYTES = 512
OUTPUT_PREVIEW_CHARS = 240

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="milliseconds")


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
           "evidence": list(evidence or []), "gate_pass": None, "episode_state_mutated": False,
           "duration_seconds": seconds_between(start_time, end_time)}
    row.update({"task_id":task_id,"snapshot_id":snapshot_id,"worker_id":worker_id,"input_sha":input_sha,
                "output_sha":output_sha,"stale":bool(stale),"failure_type":failure_type})
    path = Path(ep) / REL; path.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return row


def timing_report(ep: Path) -> dict:
    """Return every recorded node attempt, including failures and reused nodes."""
    path = Path(ep) / REL
    rows = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict) or not row.get("node_id"):
                continue
            duration = row.get("duration_seconds")
            if not isinstance(duration, (int, float)):
                duration = seconds_between(row.get("start_time"), row.get("end_time"))
            rows.append({"node_id": row["node_id"], "task_id": row.get("task_id"),
                         "attempt": row.get("attempt"), "status": row.get("status"),
                         "start_time": row.get("start_time"), "end_time": row.get("end_time"),
                         "duration_seconds": duration})
    return {"episode": str(Path(ep).resolve()), "node_attempts": rows,
            "missing_duration_count": sum(row["duration_seconds"] is None for row in rows)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["report"])
    parser.add_argument("episode_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(timing_report(args.episode_dir), ensure_ascii=False, indent=2))
