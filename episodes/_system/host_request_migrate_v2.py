#!/usr/bin/env python3
"""Backfill Host Request JSON into MySQL and delete only reconciled sources."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import episode_discovery
import host_request_persistence
import runtime_workspace
import storage_config
import story_json
from scripts.phase9_runtime_launcher import load_runtime_env_file


def _load_runtime_env(path: Path) -> tuple[str, ...]:
    env, loaded = load_runtime_env_file(path, dict(os.environ))
    os.environ.update(env)
    return loaded


def scan() -> dict:
    rows = []
    errors = []
    seen_paths = set()
    owners: dict[str, str] = {}
    for ep in episode_discovery.iter_episode_roots(ROOT / "episodes"):
        ep = Path(ep).resolve()
        namespace = runtime_workspace.episode_namespace(ep).as_posix()
        for source, root in (
            ("episode", ep / host_request_persistence.REL),
            ("runtime_workspace", runtime_workspace.workspace_path(ep, host_request_persistence.REL)),
        ):
            if not root.is_dir():
                continue
            for path in sorted(root.glob("*.json")):
                resolved = path.resolve()
                if resolved in seen_paths:
                    continue
                seen_paths.add(resolved)
                payload = story_json.read_json(path, default={}) or {}
                request_id = str(payload.get("request_id") or "").strip()
                if not request_id:
                    errors.append(f"host request id missing: {path}")
                    continue
                prior = owners.get(request_id)
                if prior and prior != namespace:
                    errors.append(f"host request id collision: {request_id}: {prior} vs {namespace}")
                    continue
                owners[request_id] = namespace
                rows.append({
                    "episode": ep,
                    "source": source,
                    "path": path,
                    "request_id": request_id,
                    "payload": payload,
                })
    return {"rows": rows, "errors": errors}


def apply(plan: dict, *, reconcile: bool, delete_after_reconcile: bool) -> dict:
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_host_request_repository import MySqlHostRequestRepository
    from platform.repository.mysql.schema_v2 import DATABASE_NAME

    if plan["errors"]:
        raise ValueError("host request scan failed: " + "; ".join(plan["errors"][:10]))
    if delete_after_reconcile and not reconcile:
        raise ValueError("--delete-after-reconcile requires --reconcile")
    connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
    written = reconciled = deleted = 0
    try:
        repo = MySqlHostRequestRepository(connection)
        for item in plan["rows"]:
            repo.upsert(host_request_persistence._record(item["episode"], item["payload"]))
            written += 1
            verified = False
            if reconcile:
                loaded = repo.get_by_id(item["request_id"])
                verified = bool(loaded and loaded.get("payload") == item["payload"])
                if not verified:
                    raise ValueError(f"host request reconcile mismatch: {item['path']}")
                reconciled += 1
            if delete_after_reconcile and verified:
                item["path"].unlink()
                deleted += 1
        return {"written": written, "reconciled": reconciled, "deleted": deleted}
    finally:
        connection.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--reconcile", action="store_true")
    parser.add_argument("--delete-after-reconcile", action="store_true")
    parser.add_argument(
        "--runtime-env-file",
        default=str(ROOT / ".storyos/runtime-launcher/runtime.env"),
    )
    args = parser.parse_args(argv)
    loaded = _load_runtime_env(Path(args.runtime_env_file))
    plan = scan()
    summary = {
        "mode": "apply" if args.apply else "dry-run",
        "files": len(plan["rows"]),
        "episode_files": sum(1 for row in plan["rows"] if row["source"] == "episode"),
        "runtime_workspace_files": sum(1 for row in plan["rows"] if row["source"] == "runtime_workspace"),
        "errors": plan["errors"],
        "runtime_env_keys": list(loaded),
        "secret_values_printed": False,
    }
    if args.apply:
        summary["result"] = apply(plan, reconcile=args.reconcile, delete_after_reconcile=args.delete_after_reconcile)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not plan["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
