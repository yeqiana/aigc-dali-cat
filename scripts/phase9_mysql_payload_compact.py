#!/usr/bin/env python3
"""Compact oversized MySQL JSON rows into bounded projections.

Dry-run is the default. ``--apply`` writes each original payload to the
Runtime Workspace, then updates MySQL with a projection inside the shared
16KB limit. No Episode JSON is deleted by this tool.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
for path in (ROOT, SYSTEM):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import episode_discovery  # noqa: E402
import episode_identity  # noqa: E402
import runtime_workspace  # noqa: E402
import storage_config  # noqa: E402
from platform.repository.frame_contract_projection import is_projection, make_projection  # noqa: E402
from platform.repository.mysql.mysql_connection import MySqlConnection  # noqa: E402
from platform.repository.mysql.payload_policy import (  # noqa: E402
    MAX_INLINE_PAYLOAD_BYTES,
    bounded_json,
    document_reference,
    metric_snapshot_projection,
    payload_bytes,
    payload_sha256,
    approval_projection,
    prompt_package_projection,
    release_projection,
    runtime_review_projection,
)
from platform.repository.mysql.schema_v2 import DATABASE_NAME  # noqa: E402
from scripts.phase9_runtime_launcher import load_runtime_env_file  # noqa: E402


def _slug(value: Any) -> str:
    result = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "")).strip("._-")
    return result or "document"


def _decode(value: Any) -> dict | None:
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        value = json.loads(value)
    return value if isinstance(value, dict) else None


def _quote(value: str) -> str:
    return "`" + str(value).replace("`", "``") + "`"


def _episode_map(episodes_root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for episode in episode_discovery.iter_episode_roots(episodes_root):
        episode = Path(episode).resolve()
        identity = episode_identity.identity_record(episode)
        # Database rows are written with the immutable storage UID. Business
        # episode numbers and directory names are not safe joins: historical
        # episodes can legitimately share them.
        key = identity["storage_episode_id"]
        previous = result.get(key)
        if previous is not None and previous != episode:
            raise ValueError(f"ambiguous episode storage identity: {key}")
        result[key] = episode
    return result


def _frame_ref(payload: dict, _row: dict) -> str:
    return f"meta/runtime/contracts/frames/{int(payload.get('frame') or 0):02d}-{payload_sha256(payload)}.json"


def _prompt_ref(payload: dict, _row: dict) -> str:
    return f"meta/runtime/prompt-packages/{int(payload.get('frame') or 0):02d}-{payload_sha256(payload)}.json"


def _metric_ref(payload: dict, row: dict) -> str:
    return f"meta/runtime/metrics/{_slug(row.get('METRIC_TYPE') or row.get('metric_type'))}-{payload_sha256(payload)}.json"


def _review_ref(payload: dict, row: dict) -> str:
    return f"meta/runtime/review-documents/{_slug(row.get('REVIEW_KIND') or row.get('review_kind'))}-{payload_sha256(payload)}.json"


def _approval_ref(payload: dict, row: dict) -> str:
    return f"meta/runtime/approvals/{_slug(row.get('APPROVAL_TYPE') or row.get('approval_type'))}-{payload_sha256(payload)}.json"


def _release_ref(payload: dict, row: dict) -> str:
    return f"meta/runtime/releases/{_slug(row.get('RELEASE_TYPE') or row.get('release_type'))}-{payload_sha256(payload)}.json"


SPEC: dict[str, dict[str, Any]] = {
    "TB_FRAME_CONTRACT": {
        "id": "FRAME_CONTRACT_ID", "episode": "EPISODE_ID", "projection_type": "FRAME_CONTRACT_REF",
        "reference": _frame_ref, "project": make_projection,
    },
    "TB_PROMPT_PACKAGE": {
        "id": "PROMPT_PACKAGE_ID", "episode": "EPISODE_ID", "projection_type": "PROMPT_PACKAGE_REF",
        "reference": _prompt_ref, "project": prompt_package_projection,
    },
    "TB_METRIC_SNAPSHOT": {
        "id": "METRIC_ID", "episode": "EPISODE_ID", "projection_type": "METRIC_SNAPSHOT_REF",
        "reference": _metric_ref, "project": metric_snapshot_projection,
    },
    "TB_RUNTIME_REVIEW_REQUEST": {
        "id": "RUNTIME_REVIEW_RECORD_ID", "episode": "EPISODE_ID", "projection_type": "RUNTIME_REVIEW_REQUEST_REF",
        "reference": _review_ref, "project": runtime_review_projection,
    },
    "TB_APPROVAL_RECORD": {
        "id": "APPROVAL_ID", "episode": "EPISODE_ID", "projection_type": "APPROVAL_RECORD_REF",
        "reference": _approval_ref, "project": approval_projection,
    },
    "TB_RELEASE_RECORD": {
        "id": "RELEASE_ID", "episode": "EPISODE_ID", "projection_type": "RELEASE_RECORD_REF",
        "reference": _release_ref, "project": release_projection,
    },
}


def plan(connection, episodes_root: Path, tables: tuple[str, ...], threshold: int) -> dict:
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    by_episode = _episode_map(episodes_root)
    rows: list[dict] = []
    errors: list[str] = []
    skipped = 0
    for table in tables:
        spec = SPEC[table]
        raw_rows = connection.query_all(
            f"SELECT *, OCTET_LENGTH({_quote('PAYLOAD')}) AS __db_payload_bytes FROM {_quote(table)}"
        ) or []
        for raw in raw_rows:
            payload = _decode(raw.get("PAYLOAD") or raw.get("payload"))
            identifier = raw.get(spec["id"]) or raw.get(spec["id"].lower())
            if payload is None:
                errors.append(f"{table}/{identifier}: PAYLOAD is not an object")
                continue
            if payload.get("projection_type") == spec["projection_type"]:
                if payload_bytes(payload) > threshold:
                    errors.append(f"{table}/{identifier}: existing projection is over threshold")
                else:
                    skipped += 1
                continue
            original_bytes = int(raw.get("__db_payload_bytes") or payload_bytes(payload))
            if original_bytes <= threshold:
                skipped += 1
                continue
            episode = by_episode.get(str(raw.get(spec["episode"]) or raw.get(spec["episode"].lower()) or ""))
            if episode is None:
                errors.append(f"{table}/{identifier}: episode not found")
                continue
            reference = document_reference(payload, spec["reference"](payload, raw))
            projection = spec["project"](payload, reference)
            projected_bytes = payload_bytes(projection)
            if projected_bytes > threshold:
                errors.append(f"{table}/{identifier}: projection is {projected_bytes} bytes")
                continue
            rows.append({
                "table": table,
                "id_column": spec["id"],
                "id": identifier,
                "episode": episode,
                "payload": payload,
                "reference": reference,
                "projection": projection,
                "original_bytes": original_bytes,
                "projected_bytes": projected_bytes,
            })
    return {"rows": rows, "skipped": skipped, "errors": errors}


def apply(connection, result: dict, *, reconcile: bool) -> dict:
    if result["errors"]:
        raise ValueError("payload compaction plan failed: " + "; ".join(result["errors"][:10]))
    written = 0
    # Files are written before the transaction so a DB rollback never destroys
    # the source document. Orphaned immutable documents are safe to clean up
    # later by SHA-aware maintenance.
    for item in result["rows"]:
        external = runtime_workspace.write_json(item["episode"], item["reference"]["rel"], item["payload"])
        item["reference"]["bytes"] = external.stat().st_size
        item["projection"] = SPEC[item["table"]]["project"](item["payload"], item["reference"])
        if payload_sha256(runtime_workspace.read_json(item["episode"], item["reference"]["rel"], default=None)) != item["reference"]["sha256"]:
            raise ValueError(f"external document SHA mismatch: {item['table']}/{item['id']}")

    with connection.transaction():
        for item in result["rows"]:
            projection_json = bounded_json(item["projection"], entity=f"{item['table']} projection")
            affected = connection.execute(
                f"UPDATE {_quote(item['table'])} SET PAYLOAD=%s WHERE {_quote(item['id_column'])}=%s",
                (projection_json, item["id"]),
            )
            if affected != 1:
                raise ValueError(f"unexpected update count: {item['table']}/{item['id']}: {affected}")
            written += 1

    reconciled = 0
    if reconcile:
        for item in result["rows"]:
            row = connection.query_one(
                f"SELECT PAYLOAD FROM {_quote(item['table'])} WHERE {_quote(item['id_column'])}=%s",
                (item["id"],),
            ) or {}
            payload = _decode(row.get("PAYLOAD") or row.get("payload"))
            if payload != item["projection"]:
                raise ValueError(f"projection reconcile mismatch: {item['table']}/{item['id']}")
            reconciled += 1
    return {"compacted": written, "reconciled": reconciled}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--reconcile", action="store_true")
    parser.add_argument("--threshold", type=int, default=MAX_INLINE_PAYLOAD_BYTES)
    parser.add_argument("--table", action="append", choices=tuple(SPEC), dest="tables")
    parser.add_argument("--episodes-root", type=Path, default=ROOT / "episodes")
    parser.add_argument("--runtime-env-file", default=str(ROOT / ".storyos/runtime-launcher/runtime.env"))
    args = parser.parse_args(argv)
    if args.reconcile and not args.apply:
        parser.error("--reconcile requires --apply")
    env, loaded = load_runtime_env_file(Path(args.runtime_env_file), dict(os.environ))
    os.environ.update(env)
    tables = tuple(args.tables or SPEC)
    connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
    try:
        result = plan(connection, args.episodes_root, tables, args.threshold)
        ready = result["rows"]
        summary = {
            "mode": "apply" if args.apply else "dry-run",
            "tables": list(tables),
            "threshold_bytes": args.threshold,
            "candidate_rows": len(ready),
            "skipped_rows": result["skipped"],
            "original_bytes": sum(row["original_bytes"] for row in ready),
            "projected_bytes": sum(row["projected_bytes"] for row in ready),
            "estimated_saved_bytes": sum(row["original_bytes"] - row["projected_bytes"] for row in ready),
            "errors": result["errors"],
            "episode_json_deleted": 0,
            "read_only": not args.apply,
            "runtime_env_keys": list(loaded),
            "secret_values_printed": False,
        }
        if args.apply:
            summary["result"] = apply(connection, result, reconcile=args.reconcile)
        print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
        return 0 if not result["errors"] else 2
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
