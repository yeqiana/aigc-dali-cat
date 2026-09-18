from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import delegated_release_persistence as persistence
import episode_discovery
import story_json
from scripts.phase9_runtime_launcher import load_runtime_env_file


SOURCES = (
    (persistence.REL, persistence.RELEASE_TYPE),
    (persistence.LEGACY_REL, persistence.LEGACY_RELEASE_TYPE),
)


def scan() -> dict:
    rows = []
    errors = []
    for ep in episode_discovery.iter_episode_roots(ROOT / "episodes"):
        ep = Path(ep).resolve()
        for rel, release_type in SOURCES:
            path = ep / rel
            if not path.is_file():
                continue
            try:
                payload = story_json.read_json(path, default={}) or {}
                if not isinstance(payload, dict):
                    raise ValueError("root must be object")
                rows.append({"episode": ep, "release_type": release_type, "path": path, "payload": payload})
            except Exception as exc:
                errors.append(f"invalid delegated release {path}: {exc}")
    return {"rows": rows, "errors": errors}


def apply(plan: dict, *, reconcile: bool, delete_after_reconcile: bool) -> dict:
    if plan["errors"]:
        raise ValueError("delegated release scan failed: " + "; ".join(plan["errors"][:10]))
    if delete_after_reconcile and not reconcile:
        raise ValueError("--delete-after-reconcile requires --reconcile")
    written = reconciled = deleted = 0
    persisted = []
    verified = []
    for row in plan["rows"]:
        saved = persistence.persist(row["episode"], row["payload"], release_type=row["release_type"])
        if not saved.get("mysql_written"):
            raise RuntimeError(f"delegated release MySQL write unavailable: {row['path']}")
        written += 1
        persisted.append((row, saved["release_id"]))
    if reconcile:
        import storage_config
        from platform.repository.mysql.mysql_connection import MySqlConnection
        from platform.repository.mysql.mysql_release_record_repository import MySqlReleaseRecordRepository
        from platform.repository.mysql.schema_v2 import DATABASE_NAME

        connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
        try:
            repo = MySqlReleaseRecordRepository(connection)
            for row, release_id in persisted:
                exact = repo.get_by_id(release_id)
                if not exact or exact.get("payload") != row["payload"]:
                    raise ValueError(f"delegated release exact-id reconcile mismatch: {row['path']}")
                reconciled += 1
                verified.append(row["path"])
        finally:
            connection.close()
    if delete_after_reconcile:
        if len(verified) != len(plan["rows"]):
            raise RuntimeError("delegated release deletion blocked: not every row reconciled")
        for path in verified:
            path.unlink()
            deleted += 1
    return {"written": written, "reconciled": reconciled, "deleted": deleted}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--reconcile", action="store_true")
    ap.add_argument("--delete-after-reconcile", action="store_true")
    ap.add_argument("--runtime-env-file", default=str(ROOT / ".storyos/runtime-launcher/runtime.env"))
    args = ap.parse_args(argv)
    env, loaded = load_runtime_env_file(Path(args.runtime_env_file), dict(os.environ))
    os.environ.update(env)
    plan = scan()
    summary = {"mode": "apply" if args.apply else "dry-run", "files": len(plan["rows"]), "errors": plan["errors"],
               "runtime_env_keys": list(loaded), "secret_values_printed": False}
    if args.apply:
        summary["result"] = apply(plan, reconcile=args.reconcile, delete_after_reconcile=args.delete_after_reconcile)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not plan["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
