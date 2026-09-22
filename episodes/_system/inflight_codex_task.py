#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Attach a restarted Driver to the Codex task its predecessor already started.

2026-09-15 尸解仙: the host killed the Driver 300s into CREATIVE_STORY. Codex did
not die with it -- it is hosted by the resident `codex_user_runner.py serve`
process -- so the step ran to completion and its whole output landed in
`runtime/codex-user-runner/task-results/<request_id>.json`. The next Driver
called `run_codex()` with `uuid4()`, minting a new request_id, and paid for the
same step a second time while the first result sat unread on disk.

The fix is a durable record of what was in flight, written *before* the task is
submitted, so a later Driver can ask one question instead of guessing:

    does a task I already paid for answer exactly this question?

Three answers are possible and none of them is "submit again by default":

    ADOPT     a durable, complete, rc=0 result for this exact fingerprint
    WAIT      the task is still running; adopting is impossible and a second
              submission would be a double execution
    RESUBMIT  nothing is running and nothing usable was produced

Fail-closed throughout: every missing, unreadable, truncated or ambiguous input
resolves to RESUBMIT, never to ADOPT. Adopting a result that does not satisfy the
current step would silently substitute one step's output for another's, which is
strictly worse than paying twice.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
from pathlib import Path

import codex_user_runner
import runtime_atomic_store
import story_json
import hot_state_bridge

REL = Path("meta/runtime/in-flight-codex.json")
SCHEMA_VERSION = 1

ADOPT = "ADOPT"
WAIT = "WAIT"
RESUBMIT = "RESUBMIT"

# Only a scoped step's own output can be attached to a scoped step.
EXPECTED_TASK_TYPE = "scoped_step"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def _path(ep: Path) -> Path:
    return Path(ep) / REL


def _read(ep: Path) -> dict:
    hot = hot_state_bridge.read(ep, "INFLIGHT")
    value = hot_state_bridge.value_or_fallback(
        hot,
        lambda: story_json.read_json(_path(ep), default={}),
        default={},
    )
    return value if isinstance(value, dict) else {}


def _write(ep: Path, data: dict) -> None:
    if hot_state_bridge.compatibility_write_allowed():
        path = _path(ep)
        path.parent.mkdir(parents=True, exist_ok=True)
        runtime_atomic_store.atomic_write_json(path, data)
    hot_state_bridge.mirror(ep, "INFLIGHT", data)


def fingerprint(*, step: str, prompt: str, source_sha256: str = "") -> str:
    """Stable identity of the business question answered by one scoped task.

    ``source_sha256`` is the preferred v2 identity.  A scoped worker prompt embeds
    derived capsules, timestamps and observability, and some steps create their own
    helper files before submission.  Hashing those volatile bytes made a restarted
    Driver believe that the still-running task answered a different question and
    submit it twice.  When a caller can provide a stable authority projection, bind
    to that projection + step instead.  Legacy callers without such a projection
    keep the exact-prompt v1 behaviour and therefore fail closed rather than gaining
    a broader attach surface accidentally.
    """
    source = str(source_sha256 or "").strip().lower()
    if source:
        material = {
            "identity_schema_version": 2,
            "step": str(step),
            "source_sha256": source,
        }
    else:
        material = {
            "identity_schema_version": 1,
            "step": str(step),
            "prompt_sha256": hashlib.sha256(str(prompt).encode("utf-8")).hexdigest(),
        }
    raw = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def begin(
    ep: Path,
    *,
    step: str,
    request_id: str,
    fingerprint_value: str,
    stdin_sha256: str,
    timeout_seconds: int,
    source_sha256: str = "",
) -> dict:
    """Record the task about to be submitted, before it is submitted.

    Written first on purpose. A record written after the call returns would be
    missing in exactly the case it exists for -- the Driver dying mid-task.
    """
    data = _read(ep)
    steps = data.get("steps") if isinstance(data.get("steps"), dict) else {}
    started = now()
    try:
        deadline = (dt.datetime.fromisoformat(started)
                    + dt.timedelta(seconds=max(0, int(timeout_seconds)))).isoformat(timespec="seconds")
    except (TypeError, ValueError):
        deadline = ""
    steps[str(step)] = {
        "step": str(step),
        "request_id": str(request_id),
        "fingerprint": str(fingerprint_value),
        "stdin_sha256": str(stdin_sha256).lower(),
        "identity_schema_version": 2 if str(source_sha256 or "").strip() else 1,
        "source_sha256": str(source_sha256 or "").strip().lower(),
        "timeout_seconds": int(timeout_seconds),
        "started_at": started,
        "deadline_at": deadline,
    }
    _write(ep, {"schema_version": SCHEMA_VERSION, "updated_at": started, "steps": steps})
    return steps[str(step)]


def lookup(ep: Path, step: str) -> dict | None:
    row = (_read(ep).get("steps") or {}).get(str(step))
    return row if isinstance(row, dict) and row.get("request_id") else None


def clear(ep: Path, step: str) -> None:
    data = _read(ep)
    steps = data.get("steps") if isinstance(data.get("steps"), dict) else {}
    if steps.pop(str(step), None) is None:
        return
    _write(ep, {"schema_version": SCHEMA_VERSION, "updated_at": now(), "steps": steps})


# --- result validation -------------------------------------------------------

def validate_result(result: dict, record: dict) -> tuple[bool, str, bytes]:
    """(adoptable, reason, output). Anything not proven adoptable is refused.

    A truncated or half-written result file is indistinguishable from a complete
    one by mere existence, so the payload is verified against its own hashes
    rather than trusted.
    """
    if not isinstance(result, dict) or not result:
        return False, "NO_DURABLE_RESULT", b""
    evidence = result.get("evidence")
    if not isinstance(evidence, dict):
        return False, "EVIDENCE_MISSING", b""
    if str(evidence.get("request_id") or "") != str(record.get("request_id") or ""):
        return False, "REQUEST_ID_MISMATCH", b""
    if str(evidence.get("task_type") or "") != EXPECTED_TASK_TYPE:
        return False, f"TASK_TYPE_NOT_{EXPECTED_TASK_TYPE.upper()}", b""
    if evidence.get("timed_out") is True:
        # A timed-out task reports rc=124; treating its partial stdout as an
        # answer would let a killed step close as if it had finished.
        return False, "TASK_TIMED_OUT", b""
    try:
        returncode = int(result.get("returncode"))
    except (TypeError, ValueError):
        return False, "RETURNCODE_MISSING", b""
    if returncode != 0:
        return False, f"RETURNCODE_{returncode}", b""
    recorded_stdin = str(evidence.get("stdin_sha256") or "").lower()
    if not recorded_stdin or recorded_stdin != str(record.get("stdin_sha256") or "").lower():
        # The step's inputs changed between the interrupted run and now, so this
        # output answers a question that is no longer being asked.
        return False, "STDIN_DRIFT", b""
    encoded = result.get("output_base64")
    if not isinstance(encoded, str) or not encoded:
        return False, "OUTPUT_MISSING", b""
    try:
        output = base64.b64decode(encoded, validate=True)
    except Exception:
        return False, "OUTPUT_UNDECODABLE", b""
    if len(output) != int(result.get("output_bytes") or -1):
        return False, "OUTPUT_TRUNCATED", b""
    if hashlib.sha256(output).hexdigest() != str(result.get("output_sha256") or "").lower():
        return False, "OUTPUT_SHA_MISMATCH", b""
    return True, "OK", output


RUNNER_TASK_RUNNING = "RUNNING"
RUNNER_TASK_NOT_RUNNING = "NOT_RUNNING"
RUNNER_TASK_UNOBSERVABLE = "UNOBSERVABLE"
RUNNER_TASK_UNREACHABLE = "UNREACHABLE"


def _runner_inflight_state(request_id: str) -> str:
    """Return whether the resident runner can prove this exact task is running.

    A reachable *old* runner is different from an unreachable runner.  Older
    processes do not expose ``inflight_request_ids`` at all.  Treating that as a
    negative answer can duplicate an expensive task after its nominal deadline,
    so protocol-old is fail-closed to WAIT until the runner is upgraded.
    """
    try:
        health = codex_user_runner.runner_health()
    except Exception:
        return RUNNER_TASK_UNREACHABLE
    inflight = health.get("inflight_request_ids")
    if not isinstance(inflight, list):
        return RUNNER_TASK_UNOBSERVABLE
    return (RUNNER_TASK_RUNNING
            if str(request_id) in {str(x) for x in inflight}
            else RUNNER_TASK_NOT_RUNNING)


def _within_deadline(record: dict) -> bool:
    """Has the task's own timeout window not yet elapsed?

    Past its deadline the runner would itself have persisted a rc=124 result, so
    an absent result after the deadline means the task is definitively gone. Before
    it, an absent result may mean "still running inside a runner that restarted
    and lost its in-flight map", and that is not something a second submission
    may assume away.
    """
    raw = str(record.get("deadline_at") or "")
    if not raw:
        return False
    try:
        return dt.datetime.now(dt.timezone.utc).astimezone() < dt.datetime.fromisoformat(raw)
    except (TypeError, ValueError):
        return False


def classify(ep: Path, *, step: str, fingerprint_value: str) -> dict:
    """Decide what to do about the step's previous task, if any."""
    record = lookup(ep, step)
    if record is None:
        return {"decision": RESUBMIT, "reason": "NO_IN_FLIGHT_RECORD", "record": None}
    if str(record.get("fingerprint") or "") != str(fingerprint_value):
        return {"decision": RESUBMIT, "reason": "FINGERPRINT_DRIFT", "record": record}
    try:
        result = codex_user_runner.read_task_result(str(record["request_id"]))
    except Exception as exc:
        return {"decision": RESUBMIT, "reason": f"RESULT_UNREADABLE:{exc}", "record": record}
    adoptable, reason, output = validate_result(result, record)
    if adoptable:
        return {"decision": ADOPT, "reason": reason, "record": record, "output": output,
                "returncode": int(result["returncode"])}
    runner_state = _runner_inflight_state(str(record["request_id"]))
    if runner_state == RUNNER_TASK_RUNNING:
        return {"decision": WAIT, "reason": "TASK_STILL_RUNNING", "record": record,
                "validation": reason}
    if runner_state == RUNNER_TASK_UNOBSERVABLE:
        return {"decision": WAIT, "reason": "RUNNER_INFLIGHT_VISIBILITY_UNAVAILABLE",
                "record": record, "validation": reason}
    if _within_deadline(record):
        return {"decision": WAIT, "reason": "WITHIN_TASK_DEADLINE", "record": record,
                "validation": reason}
    return {"decision": RESUBMIT, "reason": reason, "record": record, "validation": reason}


def status(ep: Path) -> dict:
    """Read-only projection for next-action / doctor. Never submits anything."""
    data = _read(ep)
    steps = data.get("steps") if isinstance(data.get("steps"), dict) else {}
    rows = []
    for step, record in sorted(steps.items()):
        if not isinstance(record, dict):
            continue
        verdict = classify(ep, step=step, fingerprint_value=str(record.get("fingerprint") or ""))
        rows.append({
            "step": step,
            "request_id": record.get("request_id"),
            "started_at": record.get("started_at"),
            "deadline_at": record.get("deadline_at"),
            "decision": verdict["decision"],
            "reason": verdict["reason"],
        })
    return {"schema_version": SCHEMA_VERSION, "episode_relative": REL.as_posix(), "tasks": rows}


def self_test() -> None:
    assert fingerprint(step="A", prompt="p") != fingerprint(step="B", prompt="p")
    assert fingerprint(step="A", prompt="p") == fingerprint(step="A", prompt="p")
    ok, reason, out = validate_result(
        {"returncode": 0, "output_base64": base64.b64encode(b"hi").decode(),
         "output_bytes": 2, "output_sha256": hashlib.sha256(b"hi").hexdigest(),
         "evidence": {"request_id": "r", "task_type": "scoped_step", "stdin_sha256": "s"}},
        {"request_id": "r", "stdin_sha256": "s"})
    assert (ok, reason, out) == (True, "OK", b"hi"), (ok, reason, out)
    bad, reason, _ = validate_result(
        {"returncode": 0, "output_base64": "",
         "evidence": {"request_id": "r", "task_type": "scoped_step", "stdin_sha256": "s"}},
        {"request_id": "r", "stdin_sha256": "s"})
    assert not bad and reason == "OUTPUT_MISSING", reason
    print("IN-FLIGHT CODEX TASK SELF-TEST PASS")


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="in-flight scoped Codex task attach/resume")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("status"); p.add_argument("episode_dir")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test(); return 0
    print(json.dumps(status(Path(args.episode_dir).resolve()), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
