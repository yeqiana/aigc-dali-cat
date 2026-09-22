#!/usr/bin/env python3
"""Backfill Prompt Package JSON into MySQL and optionally delete reconciled files.

Dry-run is the default. ``--apply --reconcile --delete-after-reconcile`` is the
only mode that removes source JSON, and each file is deleted only after its
deterministic MySQL row is read back with the same package SHA and payload.
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
import episode_identity
import runtime_workspace
import storage_config
import story_json
from platform.repository.mysql.payload_policy import MAX_INLINE_PAYLOAD_BYTES, document_reference, payload_bytes, payload_sha256
from prompt_package_persistence import PACKAGE_TYPE, REL
from scripts.phase9_runtime_launcher import load_runtime_env_file


def _load_runtime_env(path: Path) -> tuple[str, ...]:
    env, loaded = load_runtime_env_file(path, dict(os.environ))
    os.environ.update(env)
    return loaded


def scan() -> dict:
    rows = []
    errors = []
    for ep in episode_discovery.iter_episode_roots(ROOT / "episodes"):
        ep = Path(ep).resolve()
        candidates = []
        legacy = ep / REL
        workspace = runtime_workspace.workspace_path(ep, REL)
        if legacy.is_dir():
            candidates.extend(("episode", path) for path in sorted(legacy.glob("*.json")))
        if workspace.is_dir():
            candidates.extend(("runtime_workspace", path) for path in sorted(workspace.glob("*.json")))
        seen = set()
        for source, path in candidates:
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            payload = story_json.read_json(path, default={}) or {}
            frame = int(payload.get("frame") or path.stem or 0)
            sha = str(payload.get("package_sha256") or "").lower()
            if frame < 1 or not sha:
                errors.append(f"invalid prompt package: {path}")
                continue
            rows.append({
                "episode": ep,
                "source": source,
                "path": path,
                "frame": frame,
                "sha256": sha,
                "payload": payload,
            })
    return {"rows": rows, "errors": errors}


def apply(plan: dict, *, reconcile: bool, delete_after_reconcile: bool) -> dict:
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_prompt_package_repository import MySqlPromptPackageRepository
    from platform.repository.mysql.schema_v2 import DATABASE_NAME

    if plan["errors"]:
        raise ValueError("prompt package scan failed: " + "; ".join(plan["errors"][:10]))
    if delete_after_reconcile and not reconcile:
        raise ValueError("--delete-after-reconcile requires --reconcile")
    connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
    written = reconciled = deleted = 0
    try:
        repo = MySqlPromptPackageRepository(connection)
        for item in plan["rows"]:
            document_ref = None
            if payload_bytes(item["payload"]) > MAX_INLINE_PAYLOAD_BYTES:
                digest = payload_sha256(item["payload"])
                document_ref = document_reference(
                    item["payload"],
                    f"meta/runtime/prompt-packages/{item['frame']:02d}-{digest}.json",
                )
                external = runtime_workspace.write_json(item["episode"], document_ref["rel"], item["payload"])
                document_ref["bytes"] = external.stat().st_size
            saved = repo.upsert({
                "episode_id": episode_identity.storage_episode_id(item["episode"]),
                "frame_no": item["frame"],
                "package_type": PACKAGE_TYPE,
                "sha256": item["sha256"],
                "payload": item["payload"],
                "payload_ref": document_ref,
            })
            written += 1
            verified = False
            if reconcile:
                loaded = repo.get_by_id(saved["prompt_package_id"])
                verified = bool(
                    loaded
                    and str(loaded.get("sha256") or "").lower() == item["sha256"]
                    and (
                        loaded.get("payload") == item["payload"]
                        or (
                            isinstance(loaded.get("payload"), dict)
                            and loaded["payload"].get("projection_type") == "PROMPT_PACKAGE_REF"
                            and loaded["payload"].get("document", {}).get("sha256") == payload_sha256(item["payload"])
                        )
                    )
                )
                if not verified:
                    raise ValueError(f"prompt package reconcile mismatch: {item['path']}")
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
        summary["result"] = apply(
            plan,
            reconcile=args.reconcile,
            delete_after_reconcile=args.delete_after_reconcile,
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not plan["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
