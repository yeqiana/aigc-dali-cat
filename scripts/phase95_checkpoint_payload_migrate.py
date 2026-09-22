#!/usr/bin/env python3
"""Externalize oversized Runtime Checkpoint runner events.

The command is dry-run by default.  ``--apply`` rewrites only the selected
``RUNTIME_CHECKPOINT_META`` projections after the full checkpoint has been
verified and writes runner events to the Runtime Workspace with SHA-256
metadata.  It never deletes the source document; the MySQL projection is
rebuilt in one transaction so the checkpoint remains recoverable.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
for path in (ROOT, SYSTEM):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import runtime_checkpoint_persistence as persistence  # noqa: E402
import storage_config  # noqa: E402
from platform.repository.mysql.mysql_connection import MySqlConnection  # noqa: E402
from platform.repository.mysql.payload_policy import (  # noqa: E402
    MAX_INLINE_PAYLOAD_BYTES,
    document_reference,
    payload_bytes,
    payload_sha256,
)
from platform.repository.mysql.schema_v2 import DATABASE_NAME  # noqa: E402
from scripts.phase9_runtime_launcher import load_runtime_env_file  # noqa: E402


def _decode(value):
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        value = json.loads(value)
    return value if isinstance(value, dict) else None


def _episode_map(connection, episodes_root: Path) -> dict[str, Path]:
    rows = connection.query_all(
        "SELECT EPISODE_ID, EPISODE_NAMESPACE FROM TB_EPISODE "
        "WHERE EPISODE_NAMESPACE IS NOT NULL AND EPISODE_NAMESPACE <> ''"
    )
    result = {}
    root = episodes_root.resolve()
    for row in rows:
        namespace = str(row.get("EPISODE_NAMESPACE") or "").replace("\\", "/")
        candidate = (root / namespace).resolve()
        if root not in candidate.parents and candidate != root:
            continue
        if candidate.is_dir():
            result[str(row.get("EPISODE_ID"))] = candidate
    return result


def _candidates(connection, threshold: int, task_id: str | None) -> list[dict]:
    params = [persistence.META_TASK_TYPE, threshold]
    sql = (
        "SELECT TASK_ID, EPISODE_ID, WORKFLOW_RUN_ID, PAYLOAD, "
        "OCTET_LENGTH(PAYLOAD) AS PAYLOAD_BYTES "
        "FROM TB_TASK WHERE TASK_TYPE=%s AND OCTET_LENGTH(PAYLOAD)>%s"
    )
    if task_id:
        sql += " AND TASK_ID=%s"
        params.append(task_id)
    sql += " ORDER BY UPDATE_TIME, TASK_ID"
    return connection.query_all(sql, tuple(params))


def _projected_bytes(data: dict) -> tuple[int, str | None]:
    events = data.get("runner_events")
    meta = copy.deepcopy(data)
    meta.pop("step_runs", None)
    meta.pop("runner_events", None)
    if isinstance(events, list):
        digest = payload_sha256(events)
        rel = f"{persistence.RUNNER_EVENTS_REL}/{digest}.json"
        reference = document_reference(events, rel)
        meta["runner_events_ref"] = {
            "projection_type": persistence.RUNNER_EVENTS_PROJECTION,
            "projection_version": 1,
            "event_count": len(events),
            "source_sha256": digest,
            "source_bytes": payload_bytes(events),
            "document": reference,
        }
    meta["_step_runs_present"] = "step_runs" in data
    return payload_bytes({"_checkpoint_seq": 0, **meta}), rel if isinstance(events, list) else None


def plan(connection, episodes_root: Path, threshold: int, task_id: str | None) -> dict:
    by_episode = _episode_map(connection, episodes_root)
    rows = []
    errors = []
    for raw in _candidates(connection, threshold, task_id):
        episode_id = str(raw.get("EPISODE_ID") or "")
        episode = by_episode.get(episode_id)
        if episode is None:
            errors.append(f"{raw.get('TASK_ID')}: episode namespace not found on disk")
            continue
        payload = _decode(raw.get("PAYLOAD"))
        if not isinstance(payload, dict):
            errors.append(f"{raw.get('TASK_ID')}: PAYLOAD is not an object")
            continue
        data = persistence._load_mysql(episode)
        if not isinstance(data, dict):
            errors.append(f"{raw.get('TASK_ID')}: checkpoint could not be reconstructed")
            continue
        projected, rel = _projected_bytes(data)
        rows.append({
            "task_id": str(raw.get("TASK_ID")),
            "episode_id": episode_id,
            "episode": episode,
            "workflow_run_id": str(raw.get("WORKFLOW_RUN_ID") or ""),
            "db_bytes_before": int(raw.get("PAYLOAD_BYTES") or 0),
            "projection_bytes_after": projected,
            "events": len(data.get("runner_events") or []),
            "artifact_rel": rel,
        })
    return {"rows": rows, "errors": errors}


def apply(connection, result: dict) -> dict:
    if result["errors"]:
        raise ValueError("checkpoint migration plan failed: " + "; ".join(result["errors"][:10]))
    migrated = []
    for item in result["rows"]:
        data = persistence._load_mysql(item["episode"])
        if not isinstance(data, dict):
            raise ValueError(f"checkpoint disappeared before apply: {item['task_id']}")
        persistence.persist(item["episode"], data)
        migrated.append(item["task_id"])
    return {"migrated": len(migrated), "task_ids": migrated}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true", help="显式执行只读计划（默认模式）")
    parser.add_argument("--task-id")
    parser.add_argument("--threshold", type=int, default=MAX_INLINE_PAYLOAD_BYTES)
    parser.add_argument("--episodes-root", type=Path, default=ROOT / "episodes")
    parser.add_argument("--runtime-env-file", default=str(ROOT / ".storyos/runtime-launcher/runtime.env"))
    args = parser.parse_args(argv)
    if args.threshold <= 0:
        parser.error("--threshold must be positive")
    env, loaded = load_runtime_env_file(Path(args.runtime_env_file), dict(os.environ))
    os.environ.update(env)
    connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
    try:
        result = plan(connection, args.episodes_root, args.threshold, args.task_id)
        summary = {
            "mode": "apply" if args.apply else "dry-run",
            "threshold_bytes": args.threshold,
            "candidate_rows": len(result["rows"]),
            "rows": [
                {key: (str(value) if isinstance(value, Path) else value) for key, value in row.items() if key != "episode"}
                for row in result["rows"]
            ],
            "errors": result["errors"],
            "episode_json_deleted": 0,
            "read_only": not args.apply,
            "runtime_env_keys": list(loaded),
            "secret_values_printed": False,
        }
        if args.apply:
            summary["result"] = apply(connection, result)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if not result["errors"] else 2
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
