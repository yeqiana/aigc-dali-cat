from __future__ import annotations

import hashlib
import json
from pathlib import Path

import episode_identity
import storage_config
import story_json
from platform.repository.mysql.payload_policy import MAX_INLINE_PAYLOAD_BYTES, bounded_json, payload_bytes


REVIEW_TYPE_PREFIX = "VALIDATION_"
MAX_INLINE_DETAIL_BYTES = 512


def _canonical_sha(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _review_type(stage: str) -> str:
    value = str(stage or "").strip().upper()
    if value not in {"BOOTSTRAP", "PREPRODUCTION"}:
        raise ValueError(f"unsupported validation stage: {stage}")
    return REVIEW_TYPE_PREFIX + value


def _detail_projection(detail) -> dict:
    if detail is None:
        return {}
    if isinstance(detail, str):
        raw = detail.encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        fields = {"detail_sha256": digest, "detail_bytes": len(raw)}
        if len(raw) <= MAX_INLINE_DETAIL_BYTES:
            fields["detail"] = detail
        else:
            fields["detail_preview"] = detail[:256]
        return fields
    raw = json.dumps(detail, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return {
        "detail_sha256": hashlib.sha256(raw).hexdigest(),
        "detail_bytes": len(raw),
        "detail_type": type(detail).__name__,
    }


def _checks_projection(checks: list[dict]) -> list[dict]:
    projected = []
    for check in checks:
        item = {
            "name": str(check.get("name") or "").strip(),
            "status": str(check.get("status") or "").strip().upper(),
            "path": check.get("path"),
        }
        item.update(_detail_projection(check.get("detail")))
        projected.append(item)
    return projected


def structured_payload(result: dict) -> dict:
    if not isinstance(result, dict):
        raise ValueError("validation result must be an object")
    stage = str(result.get("stage") or "").strip().lower()
    review_type = _review_type(stage)
    checks = result.get("checks")
    if not isinstance(checks, list):
        raise ValueError("validation result checks must be a list")
    normalized_checks = []
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("validation check must be an object")
        name = str(check.get("name") or "").strip()
        status = str(check.get("status") or "").strip().upper()
        if not name or not status:
            raise ValueError("validation check requires name and status")
        normalized_checks.append(check)
    status = str(result.get("status") or "").strip().upper()
    if not status:
        raise ValueError("validation result requires status")
    projected_checks = _checks_projection(normalized_checks)
    payload = {
        "schema_version": 1,
        "validation_version": result.get("story_os_validation_version"),
        "stage": stage,
        "status": status,
        "next_state": result.get("next_state"),
        "review_type": review_type,
        "checks": projected_checks,
    }
    if payload_bytes(payload) <= MAX_INLINE_PAYLOAD_BYTES:
        return payload
    statuses = [item["status"] for item in projected_checks]
    return {
        key: payload[key]
        for key in ("schema_version", "validation_version", "stage", "status", "next_state", "review_type")
        if payload.get(key) is not None
    } | {
        "check_count": len(projected_checks),
        "pass_count": sum(1 for value in statuses if value == "PASS"),
        "fail_count": sum(1 for value in statuses if value == "FAIL"),
        "checks_sha256": _canonical_sha(normalized_checks),
    }


def _repository(ep: Path):
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_review_record_repository import MySqlReviewRecordRepository
    from platform.repository.mysql.schema_v2 import DATABASE_NAME

    connection = MySqlConnection(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))
    return connection, MySqlReviewRecordRepository(connection)


def persist(ep: Path, result: dict) -> dict:
    payload = structured_payload(result)
    bounded_json(payload, entity="validation report projection")
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode == "json":
        return {"mode": mode, "mysql_written": False, "payload": payload}
    connection, repository = _repository(Path(ep).resolve())
    try:
        saved = repository.upsert({
            "episode_id": episode_identity.storage_episode_id(Path(ep).resolve()),
            "review_type": payload["review_type"],
            "attempt_no": 1,
            "decision": "PASS" if payload["status"].endswith("_PASS") else "FAIL",
            "source_sha256": _canonical_sha(payload),
            "reviewer_type": "POLICY",
            "payload": payload,
        })
        return {"mode": mode, "mysql_written": True, **saved, "payload": payload}
    finally:
        connection.close()


def load(ep: Path, stage: str, *, legacy_path: Path | None = None) -> dict | None:
    mode = storage_config.episode_meta_store_config()["mode"]
    if mode in {"dual", "mysql"}:
        connection = None
        try:
            connection, repository = _repository(Path(ep).resolve())
            from platform.repository.mysql.mysql_review_record_repository import review_id

            row = repository.get_by_id(review_id(
                episode_identity.storage_episode_id(Path(ep).resolve()),
                _review_type(stage),
                1,
            ))
            if row and isinstance(row.get("payload"), dict):
                return row["payload"]
        except Exception:
            pass
        finally:
            if connection is not None:
                connection.close()
    if legacy_path and Path(legacy_path).is_file():
        data = story_json.read_json(Path(legacy_path), default=None)
        return data if isinstance(data, dict) else None
    return None
