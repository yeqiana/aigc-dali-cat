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


VISUAL_LOCK_ROLES = (
    "ordinary_baseline", "worst_capture_condition",
    "first_major_anomaly", "high_impact_admission",
)


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
    scope = str(context.get("production_scope") or context.get("scope") or "batch")
    try:
        head = connection.query_one(
            "SELECT ACTIVE_REVISION_ID, FENCING_COUNTER FROM TB_PRODUCTION_REVISION_HEAD WHERE EPISODE_ID=%s FOR UPDATE",
            (str(episode_id),),
        )
        active = str((head or {}).get("ACTIVE_REVISION_ID") or "") or None
        head_fence = int((head or {}).get("FENCING_COUNTER") or 0)
    except Exception as exc:
        # V2 schema rollout is opt-in. Preserve legacy Episodes before the new
        # tables are migrated, but never accept a claimed Revision without its
        # durable authority.
        if supplied:
            raise ProductionRevisionDenied("PRODUCTION_REVISION_AUTHORITY_UNAVAILABLE") from exc
        return None
    selected_revision = active
    if supplied and supplied != active:
        pending = connection.query_one(
            "SELECT STATUS, EPISODE_ID FROM TB_PRODUCTION_REVISION WHERE PRODUCTION_REVISION_ID=%s",
            (supplied,),
        )
        if (scope != "visual_lock" or not pending
                or str(pending.get("EPISODE_ID") or "") != str(episode_id)
                or str(pending.get("STATUS") or "") != "VISUAL_LOCK_PENDING"):
            raise ProductionRevisionDenied("PRODUCTION_REVISION_BINDING_REQUIRED")
        selected_revision = supplied
    elif supplied is None and active is not None:
        raise ProductionRevisionDenied("PRODUCTION_REVISION_BINDING_REQUIRED")
    elif supplied is None:
        return None
    if selected_revision is None:
        raise ProductionRevisionDenied("PRODUCTION_REVISION_NOT_ACTIVE")
    row = connection.query_one(
        "SELECT STATUS, EPISODE_ID FROM TB_PRODUCTION_REVISION WHERE PRODUCTION_REVISION_ID=%s",
        (selected_revision,),
    )
    status = str((row or {}).get("STATUS") or "")
    visual_pending = status == "VISUAL_LOCK_PENDING" and scope == "visual_lock"
    if (not row or str(row.get("EPISODE_ID") or "") != str(episode_id)
            or not (status == "ACTIVE" or visual_pending)):
        raise ProductionRevisionDenied("PRODUCTION_REVISION_AUTHORITY_MISMATCH")
    expected_fence = context.get("production_revision_fencing_token")
    if expected_fence is not None and int(expected_fence) != head_fence:
        raise ProductionRevisionDenied("PRODUCTION_REVISION_STALE_FENCE")
    match = re.fullmatch(re.escape(str(episode_id)) + r"/frame-(\d{2})", str(logical_asset_key or ""))
    if not match:
        raise ProductionRevisionDenied("PRODUCTION_REVISION_FRAME_BINDING_REQUIRED")
    frame_no = int(match.group(1))
    frame = connection.query_one(
        "SELECT FRAME_CONTRACT_SHA256, PROMPT_SHA256 FROM TB_PRODUCTION_REVISION_FRAME "
        "WHERE PRODUCTION_REVISION_ID=%s AND EPISODE_ID=%s AND FRAME_NO=%s",
        (selected_revision, str(episode_id), frame_no),
    )
    if not frame:
        raise ProductionRevisionDenied("PRODUCTION_REVISION_FRAME_BINDING_MISSING")
    contract_sha = str(context.get("frame_contract_sha256") or "").lower()
    prompt_sha = str(context.get("prompt_package_sha256") or "").lower()
    if (contract_sha != str(frame.get("FRAME_CONTRACT_SHA256") or "").lower()
            or prompt_sha != str(frame.get("PROMPT_SHA256") or "").lower()):
        raise ProductionRevisionDenied("PRODUCTION_REVISION_FRAME_INPUT_MISMATCH")
    context["production_revision_fencing_token"] = head_fence
    return selected_revision


def create_preparing(ep: str | Path, *, input_sha256: str, frames: list[dict], visual_lock_sha256: str | None = None) -> dict:
    """Append a CREATED revision. This never activates or dispatches it."""
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
                "INSERT INTO TB_PRODUCTION_REVISION (PRODUCTION_REVISION_ID,EPISODE_ID,REVISION_NO,STATUS,INPUT_SHA256,SNAPSHOT_SHA256,BYTE_SIZE,VISUAL_LOCK_SHA256,PARENT_REVISION_ID) VALUES (%s,%s,%s,'CREATED',%s,%s,%s,%s,%s)",
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
        return {"production_revision_id": revision_id, "revision_no": revision_no, "status": "CREATED",
                "episode_id": episode_id, "snapshot_sha256": snapshot["sha256"], "active": False}
    finally:
        connection.close()


def _load_revision(connection, episode_id: str, revision_id: str, *, lock: bool = False) -> dict:
    suffix = " FOR UPDATE" if lock else ""
    row = connection.query_one(
        "SELECT PRODUCTION_REVISION_ID, EPISODE_ID, REVISION_NO, STATUS, INPUT_SHA256, SNAPSHOT_SHA256, "
        "VISUAL_LOCK_SHA256, PARENT_REVISION_ID FROM TB_PRODUCTION_REVISION "
        "WHERE PRODUCTION_REVISION_ID=%s AND EPISODE_ID=%s" + suffix,
        (str(revision_id), str(episode_id)),
    )
    if not row:
        raise ProductionRevisionDenied("PRODUCTION_REVISION_NOT_FOUND")
    return row


def load_frame_bindings(ep: str | Path, revision_id: str) -> list[dict]:
    episode_id = _episode_id(ep)
    connection = _connect()
    try:
        revision = _load_revision(connection, episode_id, revision_id)
        rows = connection.query_all(
            "SELECT FRAME_NO, FRAME_CONTRACT_SHA256, PROMPT_SHA256 FROM TB_PRODUCTION_REVISION_FRAME "
            "WHERE PRODUCTION_REVISION_ID=%s AND EPISODE_ID=%s ORDER BY FRAME_NO",
            (str(revision_id), episode_id),
        ) or []
        if len(rows) != 25:
            raise ProductionRevisionDenied("PRODUCTION_REVISION_FRAME_BINDING_INCOMPLETE")
        return [{"frame": int(row.get("FRAME_NO") or 0),
                 "frame_contract_sha256": str(row.get("FRAME_CONTRACT_SHA256") or "").lower(),
                 "prompt_sha256": str(row.get("PROMPT_SHA256") or "").lower(),
                 "input_sha256": str(revision.get("INPUT_SHA256") or "").lower()}
                for row in rows]
    finally:
        connection.close()


def _transition(ep: str | Path, revision_id: str, allowed: set[str], target: str) -> dict:
    episode_id = _episode_id(ep)
    connection = _connect()
    try:
        with connection.transaction():
            connection.execute("INSERT IGNORE INTO TB_PRODUCTION_REVISION_HEAD (EPISODE_ID) VALUES (%s)", (episode_id,))
            connection.query_one(
                "SELECT EPISODE_ID FROM TB_PRODUCTION_REVISION_HEAD WHERE EPISODE_ID=%s FOR UPDATE",
                (episode_id,),
            )
            revision = _load_revision(connection, episode_id, revision_id, lock=True)
            status = str(revision.get("STATUS") or "")
            if status == target:
                return {"production_revision_id": revision_id, "status": target, "idempotent": True}
            if status not in allowed:
                raise ProductionRevisionDenied(f"PRODUCTION_REVISION_INVALID_TRANSITION:{status}->{target}")
            updated = connection.execute(
                "UPDATE TB_PRODUCTION_REVISION SET STATUS=%s WHERE PRODUCTION_REVISION_ID=%s AND EPISODE_ID=%s AND STATUS=%s",
                (target, str(revision_id), episode_id, status),
            )
            if updated != 1:
                raise ProductionRevisionDenied("PRODUCTION_REVISION_TRANSITION_CAS_FAILED")
        return {"production_revision_id": revision_id, "status": target, "idempotent": False}
    finally:
        connection.close()


def prepare_revision(ep: str | Path, revision_id: str) -> dict:
    episode_id = _episode_id(ep)
    connection = _connect()
    try:
        with connection.transaction():
            revision = _load_revision(connection, episode_id, revision_id, lock=True)
            rows = connection.query_all(
                "SELECT FRAME_NO, FRAME_CONTRACT_SHA256, PROMPT_SHA256 FROM TB_PRODUCTION_REVISION_FRAME "
                "WHERE PRODUCTION_REVISION_ID=%s AND EPISODE_ID=%s ORDER BY FRAME_NO",
                (str(revision_id), episode_id),
            ) or []
            if len(rows) != 25 or [int(row.get("FRAME_NO") or 0) for row in rows] != list(range(1, 26)):
                raise ProductionRevisionDenied("PRODUCTION_REVISION_FRAME_BINDING_INCOMPLETE")
            for row in rows:
                _sha(row.get("FRAME_CONTRACT_SHA256"), "frame contract sha")
                _sha(row.get("PROMPT_SHA256"), "prompt sha")
            status = str(revision.get("STATUS") or "")
            if status == "PREPARED":
                return {"production_revision_id": revision_id, "status": status, "idempotent": True}
            if status != "CREATED":
                raise ProductionRevisionDenied(f"PRODUCTION_REVISION_INVALID_TRANSITION:{status}->PREPARED")
            changed = connection.execute(
                "UPDATE TB_PRODUCTION_REVISION SET STATUS='PREPARED' WHERE PRODUCTION_REVISION_ID=%s AND EPISODE_ID=%s AND STATUS='CREATED'",
                (str(revision_id), episode_id),
            )
            if changed != 1:
                raise ProductionRevisionDenied("PRODUCTION_REVISION_TRANSITION_CAS_FAILED")
        return {"production_revision_id": revision_id, "status": "PREPARED", "idempotent": False}
    finally:
        connection.close()


def begin_visual_lock(ep: str | Path, revision_id: str) -> dict:
    return _transition(Path(ep), revision_id, {"PREPARED"}, "VISUAL_LOCK_PENDING")


def _payload_sha(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _stored_payload_sha(payload: dict) -> str:
    if payload.get("projection_type") == "EPISODE_REVIEW_REF":
        return str(payload.get("source_sha256") or "").lower()
    return _payload_sha(payload)


def record_visual_lock_review(ep: str | Path, *, revision_id: str, review_id: str,
                              review_sha256: str, payload: dict, assets: list[dict]) -> dict:
    """Persist the official four-admission review against one preparing Revision.

    Callers must first save the review using visual_profile_review_persistence;
    this method then independently reads the MySQL Review Authority row and
    verifies payload SHA, frame, prompt, contract, and actual pixel bindings.
    """
    episode_id = _episode_id(ep)
    review_sha = _sha(review_sha256, "review_sha256")
    if _payload_sha(payload) != review_sha:
        raise ProductionRevisionDenied("PRODUCTION_REVISION_REVIEW_PAYLOAD_SHA_MISMATCH")
    if str(payload.get("production_revision_id") or "") != str(revision_id):
        raise ProductionRevisionDenied("PRODUCTION_REVISION_VISUAL_LOCK_ID_MISMATCH")
    review_rows = {str(row.get("id") or ""): row for row in (payload.get("calibration") or []) if isinstance(row, dict)}
    asset_rows = {str(row.get("id") or ""): row for row in assets if isinstance(row, dict)}
    if len(review_rows) != 4 or len(asset_rows) != 4:
        raise ProductionRevisionDenied("PRODUCTION_REVISION_VISUAL_LOCK_INCOMPLETE")
    import visual_lock_v21
    required_checks = visual_lock_v21.checks_for_version(visual_lock_v21.episode_version(Path(ep)))
    connection = _connect()
    try:
        with connection.transaction():
            revision = _load_revision(connection, episode_id, revision_id, lock=True)
            if str(revision.get("STATUS") or "") != "VISUAL_LOCK_PENDING":
                raise ProductionRevisionDenied("PRODUCTION_REVISION_VISUAL_LOCK_NOT_PENDING")
            review = connection.query_one(
                "SELECT REVIEW_TYPE, DECISION, PAYLOAD FROM TB_REVIEW_RECORD WHERE REVIEW_ID=%s AND EPISODE_ID=%s",
                (str(review_id), episode_id),
            )
            stored_payload = review.get("PAYLOAD") if isinstance(review, dict) else None
            if isinstance(stored_payload, str):
                stored_payload = json.loads(stored_payload)
            if (not review or review.get("REVIEW_TYPE") != "VISUAL_PROFILE"
                    or review.get("DECISION") != "PASS"
                    or _stored_payload_sha(stored_payload if isinstance(stored_payload, dict) else {}) != review_sha):
                raise ProductionRevisionDenied("PRODUCTION_REVISION_REVIEW_AUTHORITY_MISSING")
            if (review.get("DECISION") == "PASS"
                    and ((payload.get("summary") or {}).get("passed") is not True
                         or payload.get("issue_codes") not in ([], None))):
                raise ProductionRevisionDenied("PRODUCTION_REVISION_VISUAL_LOCK_REVIEW_NOT_PASS")
            bindings = connection.query_all(
                "SELECT FRAME_NO, FRAME_CONTRACT_SHA256, PROMPT_SHA256 FROM TB_PRODUCTION_REVISION_FRAME "
                "WHERE PRODUCTION_REVISION_ID=%s AND EPISODE_ID=%s",
                (str(revision_id), episode_id),
            ) or []
            by_frame = {int(row.get("FRAME_NO") or 0): row for row in bindings}
            decisions = []
            for role in VISUAL_LOCK_ROLES:
                asset = next((row for row in asset_rows.values() if row.get("role") == role), None)
                if not asset:
                    raise ProductionRevisionDenied("PRODUCTION_REVISION_VISUAL_LOCK_ROLE_MISSING:" + role)
                rid = str(asset.get("id") or "")
                reviewed = review_rows.get(rid)
                frame_no = int(asset.get("frame") or 0)
                binding_row = by_frame.get(frame_no)
                if not reviewed or not binding_row:
                    raise ProductionRevisionDenied("PRODUCTION_REVISION_VISUAL_LOCK_FRAME_MISSING:" + role)
                contract_sha = _sha(asset.get("frame_contract_sha256"), "frame contract sha")
                prompt_sha = _sha(binding_row.get("PROMPT_SHA256"), "prompt sha")
                asset_sha = _sha(asset.get("sha256"), "asset sha")
                if contract_sha != str(binding_row.get("FRAME_CONTRACT_SHA256") or "").lower():
                    raise ProductionRevisionDenied("PRODUCTION_REVISION_VISUAL_LOCK_CONTRACT_MISMATCH:" + role)
                if (str(asset.get("production_revision_id") or "") != str(revision_id)
                        or str(asset.get("input_sha256") or "").lower() != str(revision.get("INPUT_SHA256") or "").lower()
                        or str(asset.get("prompt_sha256") or "").lower() != prompt_sha
                        or str(reviewed.get("sha256") or "").lower() != asset_sha
                        or str(reviewed.get("frame_contract_sha256") or "").lower() != contract_sha
                        or int(reviewed.get("frame") or 0) != frame_no
                        or str(reviewed.get("role") or "") != role):
                    raise ProductionRevisionDenied("PRODUCTION_REVISION_VISUAL_LOCK_BINDING_MISMATCH:" + role)
                checks = reviewed.get("checks") or {}
                passed = (reviewed.get("issues") in ([], None)
                          and all(check in checks for check in required_checks)
                          and bool(required_checks)
                          and all(value is True for value in checks.values()))
                decision = "PASS" if passed else "FAIL"
                decisions.append(decision)
                connection.execute(
                    "INSERT INTO TB_PRODUCTION_REVISION_VISUAL_ADMISSION "
                    "(PRODUCTION_REVISION_ID,EPISODE_ID,ADMISSION_ROLE,FRAME_NO,INPUT_SHA256,FRAME_CONTRACT_SHA256,PROMPT_SHA256,ASSET_SHA256,REVIEW_ID,REVIEW_SHA256,DECISION) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                    "ON DUPLICATE KEY UPDATE FRAME_NO=VALUES(FRAME_NO),INPUT_SHA256=VALUES(INPUT_SHA256),"
                    "FRAME_CONTRACT_SHA256=VALUES(FRAME_CONTRACT_SHA256),PROMPT_SHA256=VALUES(PROMPT_SHA256),"
                    "ASSET_SHA256=VALUES(ASSET_SHA256),REVIEW_SHA256=VALUES(REVIEW_SHA256),DECISION=VALUES(DECISION)",
                    (str(revision_id), episode_id, role, frame_no, str(revision.get("INPUT_SHA256") or ""),
                     contract_sha, prompt_sha, asset_sha, str(review_id), review_sha, decision),
                )
            if review.get("DECISION") == "PASS" and decisions == ["PASS"] * 4:
                digest = hashlib.sha256("|".join((str(revision_id), review_sha,
                    *[str(asset_rows[next(rid for rid, row in asset_rows.items() if row.get("role") == role)].get("sha256") or "").lower()
                      for role in VISUAL_LOCK_ROLES])).encode("utf-8")).hexdigest()
                connection.execute(
                    "UPDATE TB_PRODUCTION_REVISION SET STATUS='READY',VISUAL_LOCK_SHA256=%s "
                    "WHERE PRODUCTION_REVISION_ID=%s AND EPISODE_ID=%s AND STATUS='VISUAL_LOCK_PENDING'",
                    (digest, str(revision_id), episode_id),
                )
                status = "READY"
            else:
                connection.execute(
                    "UPDATE TB_PRODUCTION_REVISION SET VISUAL_LOCK_SHA256=NULL "
                    "WHERE PRODUCTION_REVISION_ID=%s AND EPISODE_ID=%s AND STATUS='VISUAL_LOCK_PENDING'",
                    (str(revision_id), episode_id),
                )
                status = "VISUAL_LOCK_PENDING"
        return {"production_revision_id": revision_id, "status": status,
                "review_id": review_id, "review_sha256": review_sha,
                "admissions": dict(zip(VISUAL_LOCK_ROLES, decisions))}
    finally:
        connection.close()


def activate_revision(ep: str | Path, revision_id: str, *, expected_fencing_counter: int,
                      expected_active_revision_id: str | None) -> dict:
    """CAS-activate a READY Revision and fence all leases from its predecessor."""
    episode_id = _episode_id(ep)
    connection = _connect()
    try:
        with connection.transaction():
            head = connection.query_one(
                "SELECT ACTIVE_REVISION_ID, FENCING_COUNTER FROM TB_PRODUCTION_REVISION_HEAD WHERE EPISODE_ID=%s FOR UPDATE",
                (episode_id,),
            )
            if not head:
                raise ProductionRevisionDenied("PRODUCTION_REVISION_HEAD_UNAVAILABLE")
            active = str(head.get("ACTIVE_REVISION_ID") or "") or None
            fence = int(head.get("FENCING_COUNTER") or 0)
            revision = _load_revision(connection, episode_id, revision_id, lock=True)
            if active == revision_id and revision.get("STATUS") == "ACTIVE":
                return {"production_revision_id": revision_id, "status": "ACTIVE",
                        "fencing_counter": fence, "idempotent": True}
            if (fence != int(expected_fencing_counter)
                    or active != (str(expected_active_revision_id) if expected_active_revision_id else None)):
                raise ProductionRevisionDenied("PRODUCTION_REVISION_ACTIVATION_CAS_FAILED")
            if str(revision.get("STATUS") or "") != "READY" or not revision.get("VISUAL_LOCK_SHA256"):
                raise ProductionRevisionDenied("PRODUCTION_REVISION_NOT_READY")
            frame_rows = connection.query_all(
                "SELECT FRAME_NO, FRAME_CONTRACT_SHA256, PROMPT_SHA256 FROM TB_PRODUCTION_REVISION_FRAME "
                "WHERE PRODUCTION_REVISION_ID=%s AND EPISODE_ID=%s ORDER BY FRAME_NO",
                (str(revision_id), episode_id),
            ) or []
            if len(frame_rows) != 25 or [int(row.get("FRAME_NO") or 0) for row in frame_rows] != list(range(1, 26)):
                raise ProductionRevisionDenied("PRODUCTION_REVISION_FRAME_BINDING_INCOMPLETE")
            admissions = connection.query_all(
                "SELECT a.ADMISSION_ROLE, a.FRAME_NO, a.INPUT_SHA256, a.FRAME_CONTRACT_SHA256, a.PROMPT_SHA256, "
                "a.ASSET_SHA256, a.REVIEW_ID, a.REVIEW_SHA256, a.DECISION "
                "FROM TB_PRODUCTION_REVISION_VISUAL_ADMISSION a "
                "JOIN TB_REVIEW_RECORD r ON r.REVIEW_ID=a.REVIEW_ID AND r.EPISODE_ID=a.EPISODE_ID "
                "WHERE a.PRODUCTION_REVISION_ID=%s AND a.EPISODE_ID=%s "
                "ORDER BY r.CREATE_TIME DESC, r.ATTEMPT_NO DESC, a.REVIEW_ID DESC",
                (str(revision_id), episode_id),
            ) or []
            latest = {}
            for row in admissions:
                latest.setdefault(str(row.get("ADMISSION_ROLE") or ""), row)
            if set(latest) != set(VISUAL_LOCK_ROLES):
                raise ProductionRevisionDenied("PRODUCTION_REVISION_VISUAL_LOCK_INCOMPLETE")
            for role in VISUAL_LOCK_ROLES:
                admission = latest[role]
                frame = int(admission.get("FRAME_NO") or 0)
                bound = next((row for row in frame_rows if int(row.get("FRAME_NO") or 0) == frame), None)
                if (admission.get("DECISION") != "PASS"
                        or admission.get("INPUT_SHA256") != revision.get("INPUT_SHA256")
                        or not bound
                        or admission.get("FRAME_CONTRACT_SHA256") != bound.get("FRAME_CONTRACT_SHA256")
                        or admission.get("PROMPT_SHA256") != bound.get("PROMPT_SHA256")
                        or not admission.get("ASSET_SHA256")
                        or not admission.get("REVIEW_ID")
                        or not admission.get("REVIEW_SHA256")):
                    raise ProductionRevisionDenied("PRODUCTION_REVISION_VISUAL_LOCK_ADMISSION_INVALID:" + role)
            if len({(str(row.get("REVIEW_ID") or ""), str(row.get("REVIEW_SHA256") or ""))
                    for row in latest.values()}) != 1:
                raise ProductionRevisionDenied("PRODUCTION_REVISION_VISUAL_LOCK_REVIEW_SET_MISMATCH")
            if any(int(row.get("FRAME_NO") or 0) < 1 or int(row.get("FRAME_NO") or 0) > 25
                   for row in latest.values()):
                raise ProductionRevisionDenied("PRODUCTION_REVISION_VISUAL_LOCK_FRAME_INVALID")
            for role in VISUAL_LOCK_ROLES:
                admission = latest[role]
                review = connection.query_one(
                    "SELECT DECISION, PAYLOAD FROM TB_REVIEW_RECORD WHERE REVIEW_ID=%s AND EPISODE_ID=%s AND REVIEW_TYPE='VISUAL_PROFILE'",
                    (str(admission.get("REVIEW_ID") or ""), episode_id),
                )
                review_payload = review.get("PAYLOAD") if isinstance(review, dict) else None
                if isinstance(review_payload, str):
                    review_payload = json.loads(review_payload)
                if (not review or review.get("DECISION") != "PASS"
                        or _stored_payload_sha(review_payload if isinstance(review_payload, dict) else {})
                        != admission.get("REVIEW_SHA256")):
                    raise ProductionRevisionDenied("PRODUCTION_REVISION_REVIEW_AUTHORITY_INVALID:" + role)
            if active:
                retired = connection.execute(
                    "UPDATE TB_PRODUCTION_REVISION SET STATUS='RETIRED',RETIRED_AT=UTC_TIMESTAMP(6) "
                    "WHERE PRODUCTION_REVISION_ID=%s AND EPISODE_ID=%s AND STATUS='ACTIVE'",
                    (active, episode_id),
                )
                if retired != 1:
                    raise ProductionRevisionDenied("PRODUCTION_REVISION_ACTIVE_POINTER_MISMATCH")
            changed = connection.execute(
                "UPDATE TB_PRODUCTION_REVISION SET STATUS='ACTIVE',ACTIVATED_AT=UTC_TIMESTAMP(6) "
                "WHERE PRODUCTION_REVISION_ID=%s AND EPISODE_ID=%s AND STATUS='READY'",
                (str(revision_id), episode_id),
            )
            if changed != 1:
                raise ProductionRevisionDenied("PRODUCTION_REVISION_ACTIVATION_CAS_FAILED")
            updated = connection.execute(
                "UPDATE TB_PRODUCTION_REVISION_HEAD SET ACTIVE_REVISION_ID=%s,FENCING_COUNTER=FENCING_COUNTER+1 "
                "WHERE EPISODE_ID=%s AND FENCING_COUNTER=%s AND (ACTIVE_REVISION_ID <=> %s)",
                (str(revision_id), episode_id, fence, active),
            )
            if updated != 1:
                raise ProductionRevisionDenied("PRODUCTION_REVISION_ACTIVATION_CAS_FAILED")
        return {"production_revision_id": revision_id, "status": "ACTIVE",
                "fencing_counter": fence + 1, "idempotent": False}
    finally:
        connection.close()
