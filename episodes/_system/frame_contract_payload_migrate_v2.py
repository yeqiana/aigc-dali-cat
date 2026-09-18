#!/usr/bin/env python3
"""Compact existing Frame Contract payloads without changing contract facts.

The default mode is read-only. ``--apply`` first writes each full contract to
the Runtime Workspace, then replaces only the MySQL PAYLOAD with its bounded
projection. No Episode JSON is deleted by this tool.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import episode_discovery  # noqa: E402
import episode_identity  # noqa: E402
import frame_contract_persistence  # noqa: E402
import storage_config  # noqa: E402
from platform.repository.frame_contract_projection import (  # noqa: E402
    is_projection,
    make_projection,
)
from platform.repository.mysql.mysql_connection import MySqlConnection  # noqa: E402
from platform.repository.mysql.mysql_frame_contract_repository import (  # noqa: E402
    MySqlFrameContractRepository,
)
from platform.repository.mysql.schema_v2 import DATABASE_NAME  # noqa: E402


def _encoded_bytes(value: dict) -> int:
    return len(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def episode_map(episodes_root: Path = ROOT / "episodes") -> dict[str, Path]:
    result: dict[str, Path] = {}
    for ep in episode_discovery.iter_episode_roots(episodes_root):
        identity = episode_identity.identity_record(ep)
        for key in (identity["storage_episode_id"], identity["business_episode_id"], ep.name):
            previous = result.get(key)
            if previous is not None and previous != ep:
                raise ValueError(f"ambiguous episode identity: {key}")
            result[key] = ep
    return result


def plan(repository, episodes_root: Path = ROOT / "episodes") -> dict:
    by_id = episode_map(episodes_root)
    rows = []
    errors = []
    for raw in repository.list_versions():
        item = raw or {}
        payload = item.get("payload")
        if not isinstance(payload, dict):
            errors.append(f"{item.get('frame_contract_id')}: payload is not an object")
            continue
        if is_projection(payload):
            rows.append({"status": "SKIP_COMPACT", "frame_contract_id": item.get("frame_contract_id")})
            continue
        ep = by_id.get(str(item.get("episode_id") or ""))
        if ep is None:
            errors.append(f"{item.get('frame_contract_id')}: episode not found")
            continue
        ref = frame_contract_persistence.document_reference_for(payload)
        projection = make_projection(payload, ref)
        rows.append({
            "status": "READY",
            "frame_contract_id": item.get("frame_contract_id"),
            "episode": ep,
            "payload_bytes": _encoded_bytes(payload),
            "projected_bytes": _encoded_bytes(projection),
            "payload": payload,
        })
    return {"rows": rows, "errors": errors}


def apply(plan_result: dict, repository, *, reconcile: bool = False) -> dict:
    if plan_result["errors"]:
        raise ValueError("payload compaction plan failed: " + "; ".join(plan_result["errors"][:10]))
    compacted = reconciled = 0
    for item in plan_result["rows"]:
        if item["status"] != "READY":
            continue
        ref = frame_contract_persistence.externalize(item["episode"], item["payload"])
        repository.compact_payload(item["frame_contract_id"], item["payload"], ref)
        compacted += 1
        if reconcile:
            loaded = repository.get_by_id(item["frame_contract_id"])
            if not loaded or not is_projection(loaded.get("payload")):
                raise ValueError(f"compact reconcile mismatch: {item['frame_contract_id']}")
            if loaded["payload"].get("document", {}).get("sha256") != ref["sha256"]:
                raise ValueError(f"document reconcile mismatch: {item['frame_contract_id']}")
            reconciled += 1
    return {"compacted": compacted, "reconciled": reconciled}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write external documents and compact MySQL payloads")
    parser.add_argument("--reconcile", action="store_true", help="read compacted rows back")
    parser.add_argument("--episodes-root", type=Path, default=ROOT / "episodes")
    args = parser.parse_args(argv)

    connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
    try:
        repository = MySqlFrameContractRepository(connection)
        result = plan(repository, args.episodes_root)
        ready = [row for row in result["rows"] if row["status"] == "READY"]
        summary = {
            "mode": "apply" if args.apply else "dry-run",
            "db_rows": len(result["rows"]),
            "ready_rows": len(ready),
            "skipped_rows": len(result["rows"]) - len(ready),
            "payload_bytes": sum(row.get("payload_bytes", 0) for row in ready),
            "projected_bytes": sum(row.get("projected_bytes", 0) for row in ready),
            "errors": result["errors"],
            "episode_json_deleted": 0,
        }
        if args.apply:
            summary["result"] = apply(result, repository, reconcile=args.reconcile)
        print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
        return 0 if not result["errors"] else 2
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
