from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

import episode_identity
import storage_config
import runtime_workspace
from platform.repository.mysql.payload_policy import MAX_INLINE_PAYLOAD_BYTES, document_reference, payload_bytes, payload_sha256


def _fingerprint(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _observed_time(payload: dict) -> dt.datetime:
    for key in ("generated_at", "observed_at", "at", "updated_at"):
        raw = payload.get(key)
        if not raw:
            continue
        try:
            parsed = dt.datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return parsed.astimezone(dt.timezone.utc)
        except ValueError:
            continue
    return dt.datetime.now(dt.timezone.utc)


def _repo():
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_metric_snapshot_repository import MySqlMetricSnapshotRepository

    connection = MySqlConnection(**storage_config.mysql_connection_kwargs())
    return connection, MySqlMetricSnapshotRepository(connection)


def save(ep: Path, metric_type: str, payload: dict) -> dict | None:
    if storage_config.episode_meta_store_config()["mode"] not in {"dual", "mysql"}:
        return None
    connection, repo = _repo()
    try:
        document_ref = None
        if payload_bytes(payload) > MAX_INLINE_PAYLOAD_BYTES:
            digest = payload_sha256(payload)
            safe_type = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(metric_type))
            document_ref = document_reference(payload, f"meta/runtime/metrics/{safe_type}-{digest}.json")
            external = runtime_workspace.write_json(ep, document_ref["rel"], payload)
            document_ref["bytes"] = external.stat().st_size
        return repo.upsert({
            "episode_id": episode_identity.storage_episode_id(ep),
            "metric_type": str(metric_type),
            "source_fingerprint": _fingerprint(payload),
            "payload": payload,
            "payload_ref": document_ref,
            "observed_time": _observed_time(payload),
        })
    finally:
        connection.close()


def _resolve_row(ep: Path, row: dict | None) -> dict | None:
    if not row:
        return None
    payload = row.get("payload") or {}
    document = (
        payload.get("document")
        if isinstance(payload, dict)
        and payload.get("projection_type") == "METRIC_SNAPSHOT_REF"
        else None
    )
    if isinstance(document, dict):
        full = runtime_workspace.read_json(ep, document.get("rel"), default=None)
        if not isinstance(full, dict):
            raise ValueError("metric snapshot authority document missing")
        if payload_sha256(full) != str(document.get("sha256") or "").lower():
            raise ValueError("metric snapshot authority document sha256 mismatch")
        return full
    return dict(payload) if isinstance(payload, dict) else None


def load_latest(ep: Path, metric_type: str) -> dict | None:
    if storage_config.episode_meta_store_config()["mode"] not in {"dual", "mysql"}:
        return None
    connection, repo = _repo()
    try:
        row = repo.get_latest(episode_identity.storage_episode_id(ep), str(metric_type))
        return _resolve_row(Path(ep).resolve(), row)
    finally:
        connection.close()


def load_by_id(ep: Path, metric_id: str) -> dict | None:
    """Resolve one exact metric row, including externalized full documents."""
    if storage_config.episode_meta_store_config()["mode"] not in {"dual", "mysql"}:
        return None
    connection, repo = _repo()
    try:
        return _resolve_row(Path(ep).resolve(), repo.get_by_id(str(metric_id)))
    finally:
        connection.close()
