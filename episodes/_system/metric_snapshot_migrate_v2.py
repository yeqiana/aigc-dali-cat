#!/usr/bin/env python3
"""Backfill active Episode metric JSON into MySQL and optionally delete them.

Dry-run is the default. Deletion is allowed only after the same payload has
been read back from MySQL for every source file in the plan.
"""
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
import metric_snapshot_persistence
import runtime_observability
import story_json
from scripts.phase9_runtime_launcher import load_runtime_env_file


def scan(episodes_root: Path = ROOT / "episodes") -> dict:
    rows: list[dict] = []
    errors: list[str] = []
    for ep in episode_discovery.iter_episode_roots(episodes_root):
        ep = Path(ep).resolve()
        for metric_type, rel in runtime_observability.KNOWN_PATHS.items():
            path = ep / rel
            if not path.is_file():
                continue
            try:
                payload = story_json.read_json(path, require_object=False)
            except Exception as exc:
                errors.append(f"read failed: {path}: {exc}")
                continue
            if not isinstance(payload, dict):
                errors.append(f"metric root must be object: {path}")
                continue
            rows.append({"episode": ep, "metric_type": metric_type, "path": path, "payload": payload})
    return {"files": len(rows), "errors": errors, "rows": rows}


def apply(plan: dict, *, reconcile: bool, delete_after_reconcile: bool) -> dict:
    if plan["errors"]:
        raise ValueError("metric scan failed: " + "; ".join(plan["errors"][:10]))
    written = reconciled = deleted = 0
    persisted = []
    for row in plan["rows"]:
        saved = metric_snapshot_persistence.save(row["episode"], row["metric_type"], row["payload"])
        if not saved:
            raise RuntimeError(f"metric MySQL write unavailable: {row['path']}")
        written += 1
        persisted.append((row, str(saved["metric_id"])))

    if reconcile or delete_after_reconcile:
        from platform.repository.mysql.mysql_connection import MySqlConnection
        from platform.repository.mysql.mysql_metric_snapshot_repository import MySqlMetricSnapshotRepository
        import storage_config

        connection = MySqlConnection(**storage_config.mysql_connection_kwargs())
        try:
            repo = MySqlMetricSnapshotRepository(connection)
            for row, metric_id_value in persisted:
                loaded = repo.get_by_id(metric_id_value)
                if not loaded or loaded.get("payload") != row["payload"]:
                    raise ValueError(f"metric reconcile mismatch: {row['path']}")
                reconciled += 1
        finally:
            connection.close()

    # Delete only after the complete batch has been reconciled successfully.
    if delete_after_reconcile:
        for row, _metric_id_value in persisted:
            row["path"].unlink()
            deleted += 1
    return {"written": written, "reconciled": reconciled, "deleted": deleted}


def _load_env(path: Path) -> tuple[str, ...]:
    env, loaded = load_runtime_env_file(path, dict(os.environ))
    os.environ.update(env)
    return loaded


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--reconcile", action="store_true")
    ap.add_argument("--delete-after-reconcile", action="store_true")
    ap.add_argument("--runtime-env-file", default=str(ROOT / ".storyos/runtime-launcher/runtime.env"))
    args = ap.parse_args(argv)
    loaded = _load_env(Path(args.runtime_env_file))
    plan = scan()
    summary = {
        "mode": "apply" if args.apply else "dry-run",
        "files": plan["files"],
        "errors": plan["errors"],
        "runtime_env_keys": list(loaded),
        "secret_values_printed": False,
    }
    if args.apply:
        summary["result"] = apply(
            plan,
            reconcile=args.reconcile or args.delete_after_reconcile,
            delete_after_reconcile=args.delete_after_reconcile,
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not plan["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
