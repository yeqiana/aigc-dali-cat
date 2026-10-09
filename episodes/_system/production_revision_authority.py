"""MySQL authority for append-only, Episode-scoped production revisions.

Revision identity is audit metadata only: Generation Attempt identity, leases,
fencing and attempt counters remain scoped to the existing Episode/logical asset
key so a new revision cannot reset the shared dispatch budget.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import logical_asset_identity
import storage_config
from platform.repository.mysql.mysql_connection import MySqlConnection
from platform.repository.mysql.schema_v2 import DATABASE_NAME


class ProductionRevisionDenied(RuntimeError):
    pass


def _connect():
    return MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))


def _episode_id(ep: str | Path) -> str:
    # Match Generation Attempt's existing global budget namespace exactly.
    return logical_asset_identity.episode_id(Path(ep).resolve())


def _sha(value: Any, field: str) -> str:
    value = str(value or "").strip().lower()
    if not re.fullmatch(r"[a-f0-9]{64}", value):
        raise ValueError(f"{field} must be a SHA-256 hex digest")
    return value


def canonical_snapshot(*, input_sha256: str, frames: list[dict], visual_lock_sha256: str | None = None) -> dict:
    """Validate and canonicalize all frame and frozen input bindings."""
    source_sha = _sha(input_sha256, "input_sha256")
    if not isinstance(frames, list) or len(frames) != 25:
        raise ValueError("production revision requires exactly 25 frame bindings")
    normalized = []
    for expected, row in enumerate(sorted(frames, key=lambda item: int(item.get("frame") or 0)), 1):
        if not isinstance(row, dict) or int(row.get("frame") or 0) != expected:
            raise ValueError("production revision frames must be numbered 1..25")
        normalized.append({
            "frame": expected,
            "frame_contract_sha256": _sha(row.get("frame_contract_sha256"), f"frame {expected} contract SHA"),
            "prompt_sha256": _sha(row.get("prompt_sha256"), f"frame {expected} prompt SHA"),
        })
    visual_sha = _sha(visual_lock_sha256, "visual_lock_sha256") if visual_lock_sha256 else None
    payload = {"schema": "storyos-production-revision/v1", "input_sha256": source_sha,
               "visual_lock_sha256": visual_sha, "frames": normalized}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"payload": payload, "sha256": hashlib.sha256(encoded).hexdigest(), "byte_size": len(encoded)}


def active_revision_id(connection, episode_id: str, *, lock: bool = False) -> str | None:
    suffix = " FOR UPDATE" if lock else ""
    row = connection.query_one(
        "SELECT ACTIVE_REVISION_ID FROM TB_PRODUCTION_REVISION_HEAD WHERE EPISODE_ID=%s" + suffix,
        (str(episode_id),),
    )
    return str(row.get("ACTIVE_REVISION_ID") or "") or None if row else None


def validate_dispatch_binding(connection, episode_id: str, context: dict,
                              logical_asset_key: str | None = None) -> str | None:
    """Require the current Revision on revision-enabled Episodes.

    Episodes without a revision head retain their current compatibility path.
    Once a head exists, requests without its exact active ID are denied. The
    Attempt table remains keyed by the global logical asset identity.
    """
    supplied = str(context.get("production_revision_id") or "").strip() or None
    try:
        active = active_revision_id(connection, episode_id, lock=True)
    except Exception as exc:
        # V2 schema rollout is opt-in. Preserve legacy Episodes before the new
        # tables are migrated, but never accept a claimed Revision without its
        # durable authority.
        if supplied:
            raise ProductionRevisionDenied("PRODUCTION_REVISION_AUTHORITY_UNAVAILABLE") from exc
        return None
    if active is None:
        if supplied:
            raise ProductionRevisionDenied("PRODUCTION_REVISION_NOT_ACTIVE")
        return None
    if supplied != active:
        raise ProductionRevisionDenied("PRODUCTION_REVISION_BINDING_REQUIRED")
    row = connection.query_one(
        "SELECT STATUS, EPISODE_ID FROM TB_PRODUCTION_REVISION WHERE PRODUCTION_REVISION_ID=%s",
        (active,),
    )
    if not row or str(row.get("EPISODE_ID") or "") != str(episode_id) or str(row.get("STATUS") or "") != "ACTIVE":
        raise ProductionRevisionDenied("PRODUCTION_REVISION_AUTHORITY_MISMATCH")
    match = re.fullmatch(re.escape(str(episode_id)) + r"/frame-(\d{2})", str(logical_asset_key or ""))
    if not match:
        raise ProductionRevisionDenied("PRODUCTION_REVISION_FRAME_BINDING_REQUIRED")
    frame_no = int(match.group(1))
    frame = connection.query_one(
        "SELECT FRAME_CONTRACT_SHA256, PROMPT_SHA256 FROM TB_PRODUCTION_REVISION_FRAME "
        "WHERE PRODUCTION_REVISION_ID=%s AND EPISODE_ID=%s AND FRAME_NO=%s",
        (active, str(episode_id), frame_no),
    )
    if not frame:
        raise ProductionRevisionDenied("PRODUCTION_REVISION_FRAME_BINDING_MISSING")
    contract_sha = str(context.get("frame_contract_sha256") or "").lower()
    prompt_sha = str(context.get("prompt_package_sha256") or "").lower()
    if (contract_sha != str(frame.get("FRAME_CONTRACT_SHA256") or "").lower()
            or prompt_sha != str(frame.get("PROMPT_SHA256") or "").lower()):
        raise ProductionRevisionDenied("PRODUCTION_REVISION_FRAME_INPUT_MISMATCH")
    return active


def create_preparing(ep: str | Path, *, input_sha256: str, frames: list[dict], visual_lock_sha256: str | None = None) -> dict:
    """Append a PREPARING revision. This never activates or dispatches it."""
    episode_id = _episode_id(ep)
    snapshot = canonical_snapshot(input_sha256=input_sha256, frames=frames, visual_lock_sha256=visual_lock_sha256)
    connection = _connect()
    try:
        connection.execute("INSERT IGNORE INTO TB_PRODUCTION_REVISION_HEAD (EPISODE_ID) VALUES (%s)", (episode_id,))
        with connection.transaction():
            head = connection.query_one(
                "SELECT NEXT_REVISION_NO, ACTIVE_REVISION_ID FROM TB_PRODUCTION_REVISION_HEAD WHERE EPISODE_ID=%s FOR UPDATE",
                (episode_id,),
            )
            if not head:
                raise RuntimeError("PRODUCTION_REVISION_HEAD_UNAVAILABLE")
            revision_no = int(head.get("NEXT_REVISION_NO") or 1)
            parent = head.get("ACTIVE_REVISION_ID")
            revision_id = f"PR_{hashlib.sha256(episode_id.encode()).hexdigest()[:16]}_{revision_no:04d}_{snapshot['sha256'][:16]}"
            connection.execute(
                "INSERT INTO TB_PRODUCTION_REVISION (PRODUCTION_REVISION_ID,EPISODE_ID,REVISION_NO,STATUS,INPUT_SHA256,SNAPSHOT_SHA256,BYTE_SIZE,VISUAL_LOCK_SHA256,PARENT_REVISION_ID) VALUES (%s,%s,%s,'PREPARING',%s,%s,%s,%s,%s)",
                (revision_id, episode_id, revision_no, snapshot["payload"]["input_sha256"], snapshot["sha256"],
                 snapshot["byte_size"], snapshot["payload"]["visual_lock_sha256"], parent),
            )
            for row in snapshot["payload"]["frames"]:
                connection.execute(
                    "INSERT INTO TB_PRODUCTION_REVISION_FRAME (PRODUCTION_REVISION_ID,EPISODE_ID,FRAME_NO,FRAME_CONTRACT_SHA256,PROMPT_SHA256) VALUES (%s,%s,%s,%s,%s)",
                    (revision_id, episode_id, row["frame"], row["frame_contract_sha256"], row["prompt_sha256"]),
                )
            connection.execute(
                "UPDATE TB_PRODUCTION_REVISION_HEAD SET NEXT_REVISION_NO=NEXT_REVISION_NO+1 WHERE EPISODE_ID=%s",
                (episode_id,),
            )
        return {"production_revision_id": revision_id, "revision_no": revision_no, "status": "PREPARING",
                "episode_id": episode_id, "snapshot_sha256": snapshot["sha256"], "active": False}
    finally:
        connection.close()
