#!/usr/bin/env python3
"""Produce durable P0 Agent protocol acceptance evidence."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes/_system"
sys.path[:0] = [str(SYSTEM), str(ROOT)]

TESTS = (
    "tests/system/test_preimage_execution_idempotency.py",
    "tests/system/test_preimage_execution_mysql_parity.py",
    "tests/system/test_preimage_protocol_replay_barrier.py",
    "tests/system/test_agent_execution_envelope.py",
    "tests/platform/test_mysql_workflow_task_repositories.py",
    "tests/system/test_episode_storage_policy.py",
)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def load_runtime_env() -> None:
    from scripts.phase9_runtime_launcher import load_runtime_env_file
    env, _ = load_runtime_env_file(
        ROOT / ".storyos/runtime-launcher/runtime.env", dict(os.environ)
    )
    os.environ.update(env)


def mysql_rollback_smoke() -> dict:
    load_runtime_env()
    from platform.repository.mysql.mysql_connection_pool import set_process_role
    set_process_role("scheduler")
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_task_repository import MySqlTaskRepository
    from platform.repository.mysql.mysql_workflow_run_repository import MySqlWorkflowRunRepository
    from platform.repository.mysql.schema_v2 import DATABASE_NAME
    import storage_config

    conn = MySqlConnection(
        **storage_config.mysql_connection_kwargs({"database": DATABASE_NAME})
    )
    run_id = "WR_P0_ACCEPTANCE_ROLLBACK"
    task_id = "TASK_P0_ACCEPTANCE_ROLLBACK"
    episode_id = "EP_P0_ACCEPTANCE_ROLLBACK"
    tasks = MySqlTaskRepository(conn)
    runs = MySqlWorkflowRunRepository(conn)

    # A stale row means a previous smoke violated rollback semantics.
    if tasks.get(task_id) is not None:
        return {"pass": False, "reason": "stale smoke task exists before transaction"}

    class RollbackExpected(Exception):
        pass

    inside = {}
    try:
        try:
            with conn.transaction():
                runs.upsert({
                    "workflow_run_id": run_id,
                    "episode_id": episode_id,
                    "runtime_type": "AGENT",
                    "run_reason": "P0_ACCEPTANCE_ROLLBACK",
                    "status": "CURRENT",
                })
                payload = {
                    "schema_version": 1,
                    "snapshot_id": "p0-acceptance",
                    "task_id": "character-finalize",
                    "execution_id": "exec-p0-acceptance",
                    "attempt": 1,
                    "idempotency_key": "idem-p0-acceptance",
                    "status": "PREPARED",
                    "eligible": True,
                    "commit_receipt": {
                        "status": "PREPARED",
                        "input_sha": "a" * 64,
                        "output_sha": "b" * 64,
                    },
                }
                tasks.upsert({
                    "task_id": task_id,
                    "episode_id": episode_id,
                    "workflow_run_id": run_id,
                    "task_type": "PREIMAGE_AGENT_EXECUTION",
                    "status": "PREPARED",
                    "attempt_no": 1,
                    "owner_id": "exec-p0-acceptance",
                    "payload": payload,
                })
                prepared = tasks.get(task_id)
                if not prepared or prepared["status"] != "PREPARED":
                    raise RuntimeError("PREPARED receipt did not round-trip")
                payload["status"] = "COMMITTED"
                payload["eligible"] = False
                payload["commit_receipt"] = {
                    **payload["commit_receipt"],
                    "status": "COMMITTED",
                    "commit_id": "p0-acceptance",
                }
                tasks.upsert({
                    "task_id": task_id,
                    "episode_id": episode_id,
                    "workflow_run_id": run_id,
                    "task_type": "PREIMAGE_AGENT_EXECUTION",
                    "status": "COMMITTED",
                    "attempt_no": 1,
                    "owner_id": "exec-p0-acceptance",
                    "payload": payload,
                })
                committed = tasks.get(task_id)
                inside = {
                    "prepared_roundtrip": True,
                    "committed_roundtrip": bool(
                        committed
                        and committed["status"] == "COMMITTED"
                        and committed["payload"]["commit_receipt"]["status"] == "COMMITTED"
                    ),
                }
                raise RollbackExpected()
        except RollbackExpected:
            pass

        task_after = tasks.get(task_id)
        run_after = conn.query_one(
            "SELECT WORKFLOW_RUN_ID FROM TB_WORKFLOW_RUN WHERE WORKFLOW_RUN_ID=%s",
            (run_id,),
        )
        health = conn.health_check()
        return {
            "pass": bool(
                inside.get("prepared_roundtrip")
                and inside.get("committed_roundtrip")
                and task_after is None
                and run_after is None
                and health.get("alive")
            ),
            "inside_transaction": inside,
            "rolled_back_task_absent": task_after is None,
            "rolled_back_workflow_absent": run_after is None,
            "mysql_alive": health.get("alive"),
            "database": health.get("database"),
        }
    finally:
        conn.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--output", default="reports/p0-agent-acceptance-20260926.json"
    )
    args = ap.parse_args()

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *TESTS, "-q"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    mysql = mysql_rollback_smoke()
    report = {
        "schema_version": 1,
        "kind": "p0_agent_protocol_acceptance",
        "generated_at": now(),
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "tests": list(TESTS),
        "pytest": {
            "return_code": proc.returncode,
            "stdout_tail": "\n".join(proc.stdout.splitlines()[-8:]),
            "stderr_tail": "\n".join(proc.stderr.splitlines()[-8:]),
        },
        "mysql_receipt_rollback_smoke": mysql,
        "gates": {
            "replay": proc.returncode == 0,
            "attempt_supersede": proc.returncode == 0,
            "execution_eligibility": proc.returncode == 0,
            "storage_parity": proc.returncode == 0 and mysql.get("pass") is True,
            "d1_d4": proc.returncode == 0,
        },
    }
    report["commit_gate_ready"] = all(report["gates"].values())
    path = ROOT / args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["commit_gate_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
