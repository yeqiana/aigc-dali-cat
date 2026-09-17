#!/usr/bin/env python3
"""Staged Provider Receipt JSON -> MySQL V2 dual-write adapter."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import storage_config

ROOT = Path(__file__).resolve().parents[2]


def _episode_id(ep: Path) -> str:
    state_path = ep / "meta/episode-state.json"
    if state_path.is_file():
        data = json.loads(state_path.read_text(encoding="utf-8-sig"))
        value = str(data.get("episode_id") or "").strip()
        if value:
            return value
    digest = hashlib.sha256(str(ep.resolve()).encode("utf-8")).hexdigest()[:24]
    return f"EP_{digest}"


def receipt_id(ep: Path, receipt: dict) -> str:
    basis = "|".join((
        _episode_id(ep),
        str(receipt.get("frame") or ""),
        str(receipt.get("recorded_at_epoch") or ""),
        str(receipt.get("capability_id") or ""),
        str(receipt.get("raw_sha256") or ""),
    ))
    return "PR_" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:40]


def persist(
    ep: Path,
    receipt: dict,
    *,
    status: str,
    legacy_path: str | None = None,
    legacy_sha256: str | None = None,
) -> dict:
    """Mirror a receipt only when explicit Episode metadata mode is ``dual``."""
    ep = Path(ep).resolve()
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode == "json":
        return {"mode": mode, "mysql_written": False}

    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_provider_receipt_repository import (
        MySqlProviderReceiptRepository,
    )
    from platform.repository.mysql.schema_v2 import DATABASE_NAME

    kwargs = storage_config.mysql_connection_kwargs({"database": DATABASE_NAME})
    connection = MySqlConnection(**kwargs)
    try:
        MySqlProviderReceiptRepository(connection).upsert({
            "receipt_id": receipt_id(ep, receipt),
            "episode_id": _episode_id(ep),
            "attempt_id": receipt.get("attempt_id"),
            "provider": str(receipt.get("provider") or "").strip(),
            "model": receipt.get("model"),
            "status": str(status),
            "error_code": receipt.get("error_code"),
            "request_id": receipt.get("request_id"),
            "legacy_path": legacy_path,
            "legacy_sha256": legacy_sha256,
            "payload": receipt,
        })
    finally:
        connection.close()
    return {"mode": mode, "mysql_written": True}


def load_by_path(ep: Path, legacy_path: str | Path) -> dict | None:
    """Read compatibility JSON first, then MySQL V2 in explicit dual mode."""
    ep = Path(ep).resolve()
    raw = Path(legacy_path)
    file_path = raw.resolve() if raw.is_absolute() else (ROOT / raw).resolve()
    if file_path.is_file():
        payload = json.loads(file_path.read_text(encoding="utf-8-sig"))
        digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
        try:
            rel = file_path.relative_to(ROOT).as_posix()
        except ValueError:
            rel = str(file_path)
        return {
            "source": "json",
            "legacy_path": rel,
            "legacy_sha256": digest,
            "payload": payload,
        }
    if storage_config.episode_meta_store_config()["mode"] != "dual":
        return None
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_provider_receipt_repository import MySqlProviderReceiptRepository
    from platform.repository.mysql.schema_v2 import DATABASE_NAME
    try:
        rel = file_path.relative_to(ROOT).as_posix()
    except ValueError:
        rel = str(file_path)
    connection = MySqlConnection(
        **storage_config.mysql_connection_kwargs({"database": DATABASE_NAME})
    )
    try:
        row = MySqlProviderReceiptRepository(connection).get_by_legacy_path(
            _episode_id(ep), rel
        )
        if not row:
            return None
        return {
            "source": "mysql",
            "legacy_path": row.get("legacy_path") or rel,
            "legacy_sha256": row.get("legacy_sha256"),
            "payload": row["payload"],
            "receipt_id": row.get("receipt_id"),
        }
    finally:
        connection.close()
