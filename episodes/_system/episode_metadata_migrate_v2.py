#!/usr/bin/env python3
"""Backfill legacy Episode Provider Receipt / Frame Contract JSON into MySQL V2.

Dry-run is the default.  ``--apply`` performs idempotent upserts but never
deletes compatibility JSON.  ``--reconcile`` verifies every migrated source
against MySQL after the write.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import episode_discovery
import episode_identity
import frame_contract_persistence
import provider_receipt_persistence
import storage_config
import story_json
from scripts.phase9_runtime_launcher import load_runtime_env_file


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _receipt_status(payload: dict) -> str:
    if payload.get("release_canvas") or payload.get("normalization"):
        return "FINALIZED"
    return "RECORDED"


def _episode_row(ep: Path) -> dict:
    state = story_json.read_json(ep / "meta/episode-state.json", default={}) or {}
    identity = episode_identity.identity_record(ep)
    return {
        "episode_id": identity["storage_episode_id"],
        "business_episode_id": identity["business_episode_id"],
        "episode_namespace": identity["namespace"],
        "series_id": identity["series"],
        "title": identity["title"],
        "tool_version": state.get("tool_version"),
        "disposition": str(state.get("disposition") or "ACTIVE").upper(),
    }


def scan(episodes_root: Path = ROOT / "episodes") -> dict:
    roots = episode_discovery.iter_episode_roots(episodes_root)
    rows = []
    storage_ids: dict[str, str] = {}
    provider_count = frame_count = 0
    errors: list[str] = []
    for ep in roots:
        ep = Path(ep).resolve()
        identity = episode_identity.identity_record(ep)
        storage_id = identity["storage_episode_id"]
        prior = storage_ids.get(storage_id)
        if prior and prior != identity["namespace"]:
            errors.append(f"storage id collision: {storage_id}: {prior} vs {identity['namespace']}")
        storage_ids[storage_id] = identity["namespace"]
        providers = sorted(ep.glob("meta/provider-receipts/*.json"))
        frames = sorted(ep.glob("meta/runtime/contracts/frames/*.json"))
        provider_count += len(providers)
        frame_count += len(frames)
        for path in providers:
            payload = story_json.read_json(path, default={}) or {}
            if not str(payload.get("provider") or "").strip():
                errors.append(f"provider missing: {path}")
        for path in frames:
            payload = story_json.read_json(path, default={}) or {}
            if not str(payload.get("contract_sha256") or "").strip():
                errors.append(f"frame contract sha missing: {path}")
        rows.append({
            "episode": ep,
            "identity": identity,
            "provider_files": providers,
            "frame_files": frames,
        })
    return {
        "episodes": len(rows),
        "provider_files": provider_count,
        "frame_files": frame_count,
        "errors": errors,
        "rows": rows,
    }


def _ensure_episode_identity_columns(connection) -> list[str]:
    added = []
    for column, ddl in (
        (
            "BUSINESS_EPISODE_ID",
            "ALTER TABLE TB_EPISODE ADD COLUMN BUSINESS_EPISODE_ID VARCHAR(128) NOT NULL DEFAULT '' COMMENT 'Episode业务编号或兼容ID' AFTER EPISODE_ID",
        ),
        (
            "EPISODE_NAMESPACE",
            "ALTER TABLE TB_EPISODE ADD COLUMN EPISODE_NAMESPACE VARCHAR(512) NOT NULL DEFAULT '' COMMENT '仓库内Episode命名空间' AFTER BUSINESS_EPISODE_ID",
        ),
    ):
        exists = connection.query_one(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND COLUMN_NAME=%s",
            ("TB_EPISODE", column),
        )
        if not exists:
            connection.execute(ddl)
            added.append(column)
    return added


def apply_backfill(plan: dict, *, reconcile: bool = False) -> dict:
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_episode_repository import MySqlEpisodeRepository
    from platform.repository.mysql.mysql_frame_contract_repository import MySqlFrameContractRepository
    from platform.repository.mysql.mysql_provider_receipt_repository import MySqlProviderReceiptRepository
    from platform.repository.mysql.schema_v2 import DATABASE_NAME

    if plan["errors"]:
        raise ValueError("migration scan failed: " + "; ".join(plan["errors"][:10]))
    connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
    provider_written = frame_written = reconciled = 0
    try:
        added_columns = _ensure_episode_identity_columns(connection)
        episodes = MySqlEpisodeRepository(connection)
        providers = MySqlProviderReceiptRepository(connection)
        frames = MySqlFrameContractRepository(connection)
        for item in plan["rows"]:
            ep = item["episode"]
            identity = item["identity"]
            storage_id = identity["storage_episode_id"]
            episodes.upsert(_episode_row(ep))
            for path in item["provider_files"]:
                payload = story_json.read_json(path, default={}) or {}
                rel = path.resolve().relative_to(ROOT).as_posix()
                digest = _sha256(path)
                providers.upsert({
                    "receipt_id": provider_receipt_persistence.receipt_id(ep, payload),
                    "episode_id": storage_id,
                    "attempt_id": payload.get("attempt_id"),
                    "provider": str(payload.get("provider") or "").strip(),
                    "model": payload.get("model"),
                    "status": _receipt_status(payload),
                    "error_code": payload.get("error_code"),
                    "request_id": payload.get("request_id"),
                    "legacy_path": rel,
                    "legacy_sha256": digest,
                    "payload": payload,
                })
                provider_written += 1
                if reconcile:
                    loaded = providers.get_by_legacy_path(storage_id, rel)
                    if not loaded or loaded.get("legacy_sha256") != digest or loaded.get("payload") != payload:
                        raise ValueError(f"provider reconcile mismatch: {rel}")
                    reconciled += 1
            for path in item["frame_files"]:
                payload = story_json.read_json(path, default={}) or {}
                document_ref = frame_contract_persistence.externalize(ep, payload)
                saved = frames.save_version({
                    "episode_id": storage_id,
                    "frame_no": int(payload["frame"]),
                    "status": "ACTIVE",
                    "sha256": payload["contract_sha256"],
                    "source_sha256": frame_contract_persistence._source_sha(payload),
                    "payload": payload,
                    "payload_ref": document_ref,
                })
                frame_written += 1
                if reconcile:
                    loaded = frames.get_latest(storage_id, int(payload["frame"]))
                    if not loaded or loaded.get("sha256") != saved["sha256"]:
                        raise ValueError(f"frame reconcile mismatch: {path}")
                    loaded_payload = loaded.get("payload") or {}
                    if loaded_payload.get("document", {}).get("sha256") != document_ref["sha256"]:
                        raise ValueError(f"frame document reconcile mismatch: {path}")
                    reconciled += 1
        return {
            "episode_rows": plan["episodes"],
            "provider_rows": provider_written,
            "frame_rows": frame_written,
            "reconciled_rows": reconciled,
            "episode_identity_columns_added": added_columns,
        }
    finally:
        connection.close()


def _load_runtime_env(path: Path) -> tuple[str, ...]:
    env, loaded = load_runtime_env_file(path, dict(os.environ))
    os.environ.update(env)
    return loaded


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write to MySQL; default is dry-run")
    parser.add_argument("--reconcile", action="store_true", help="read every written row back and compare")
    parser.add_argument(
        "--runtime-env-file",
        default=str(ROOT / ".storyos/runtime-launcher/runtime.env"),
    )
    args = parser.parse_args(argv)
    loaded = _load_runtime_env(Path(args.runtime_env_file))
    plan = scan()
    summary = {
        "mode": "apply" if args.apply else "dry-run",
        "episodes": plan["episodes"],
        "provider_files": plan["provider_files"],
        "frame_files": plan["frame_files"],
        "errors": plan["errors"],
        "runtime_env_keys": list(loaded),
        "secret_values_printed": False,
    }
    if args.apply:
        summary["result"] = apply_backfill(plan, reconcile=args.reconcile)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not plan["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
