#!/usr/bin/env python3
"""Append-only, explicitly authorized recovery evidence for UNKNOWN image attempts.

This module never changes the historical Generation Attempt or Provider Receipt.
The one-use entitlement is enforced by the existing asset row lock, the shared
two-dispatch counter, and the canonical Attempt 2 row.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
from pathlib import Path

import logical_asset_identity
import storage_config
from platform.repository.mysql.mysql_connection import MySqlConnection
from platform.repository.mysql.schema_v2 import DATABASE_NAME

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class UnknownRecoveryDenied(RuntimeError):
    pass


_CONNECTION_FACTORY = MySqlConnection


def _connect():
    return _CONNECTION_FACTORY(**storage_config.mysql_connection_kwargs({"database": DATABASE_NAME}))


def _canonical_evidence(evidence: list[dict]) -> tuple[str, str]:
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("UNKNOWN_RECOVERY_EVIDENCE_REQUIRED")
    rows = []
    for item in evidence:
        if not isinstance(item, dict):
            raise ValueError("UNKNOWN_RECOVERY_EVIDENCE_INVALID")
        kind = str(item.get("kind") or "").strip()
        reference = str(item.get("reference") or "").strip()
        digest = str(item.get("sha256") or "").strip().lower()
        if not kind or not reference or not SHA256_RE.fullmatch(digest):
            raise ValueError("UNKNOWN_RECOVERY_EVIDENCE_INVALID")
        rows.append({"kind": kind, "reference": reference, "sha256": digest})
    rows.sort(key=lambda item: (item["kind"], item["reference"], item["sha256"]))
    blob = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return blob, hashlib.sha256(blob.encode("utf-8")).hexdigest()


def valid_authorization_record(row: dict | None) -> bool:
    if not row or not str(row.get("AUTHORIZATION_ID") or "").strip():
        return False
    if not str(row.get("AUTHORIZED_BY") or "").strip() or not str(row.get("RISK_ASSESSMENT") or "").strip():
        return False
    if int(row.get("DUPLICATE_CHARGE_ACK") or 0) != 1:
        return False
    try:
        evidence = row.get("EVIDENCE_JSON")
        if isinstance(evidence, str):
            evidence = json.loads(evidence)
        _blob, digest = _canonical_evidence(evidence)
        return digest == str(row.get("EVIDENCE_SHA256") or "").lower()
    except (TypeError, ValueError, json.JSONDecodeError):
        return False


def authorize_attempt_two(ep: str | Path, logical_asset_key: str, *,
                          authorized_by: str, risk_assessment: str,
                          evidence: list[dict],
                          acknowledge_possible_duplicate_charge: bool,
                          authorization_id: str | None = None) -> dict:
    """Record a human authorization for exactly one Attempt 2 after Attempt 1 UNKNOWN.

    Callers must supply a responsible human identity and explicit duplicate-charge
    acknowledgement. The function writes only the new authorization row; it does
    not change old attempts, queue state, provider receipts, or dispatch anything.
    """
    actor = str(authorized_by or "").strip()
    risk = str(risk_assessment or "").strip()
    if not actor:
        raise ValueError("UNKNOWN_RECOVERY_AUTHORIZER_REQUIRED")
    if not risk:
        raise ValueError("UNKNOWN_RECOVERY_RISK_ASSESSMENT_REQUIRED")
    if acknowledge_possible_duplicate_charge is not True:
        raise UnknownRecoveryDenied("UNKNOWN_RECOVERY_DUPLICATE_CHARGE_ACK_REQUIRED")
    key = str(logical_asset_key or "").strip()
    episode = Path(ep).resolve()
    episode_id = logical_asset_identity.episode_id(episode)
    if not key or not key.startswith(episode_id + "/"):
        raise ValueError("UNKNOWN_RECOVERY_ASSET_KEY_INVALID")
    evidence_blob, evidence_sha = _canonical_evidence(evidence)
    auth_id = str(authorization_id or "unknown-recovery-" + secrets.token_hex(16))
    if len(auth_id) > 96:
        raise ValueError("UNKNOWN_RECOVERY_AUTHORIZATION_ID_INVALID")
    connection = _connect()
    try:
        with connection.transaction():
            state = connection.query_one(
                "SELECT ATTEMPTS_CONSUMED, ACTIVE_ATTEMPT_INDEX FROM TB_GENERATION_ASSET_STATE "
                "WHERE EPISODE_ID=%s AND LOGICAL_ASSET_KEY=%s FOR UPDATE", (episode_id, key))
            if not state or int(state.get("ATTEMPTS_CONSUMED") or 0) != 1 or state.get("ACTIVE_ATTEMPT_INDEX") is not None:
                raise UnknownRecoveryDenied("UNKNOWN_RECOVERY_ATTEMPT_STATE_MISMATCH")
            old = connection.query_one(
                "SELECT ATTEMPT_INDEX, GENERATION_KEY, STATUS FROM TB_GENERATION_ATTEMPT "
                "WHERE EPISODE_ID=%s AND LOGICAL_ASSET_KEY=%s AND ATTEMPT_INDEX=1 FOR UPDATE",
                (episode_id, key))
            if not old or old.get("STATUS") != "OUTCOME_UNKNOWN":
                raise UnknownRecoveryDenied("UNKNOWN_RECOVERY_SOURCE_NOT_UNKNOWN")
            prior_authorization = connection.query_one(
                "SELECT AUTHORIZATION_ID, UNKNOWN_GENERATION_KEY, EVIDENCE_SHA256, AUTHORIZED_BY, "
                "RISK_ASSESSMENT, DUPLICATE_CHARGE_ACK FROM TB_GENERATION_UNKNOWN_RECOVERY_AUTHORIZATION "
                "WHERE EPISODE_ID=%s AND LOGICAL_ASSET_KEY=%s AND TARGET_ATTEMPT_INDEX=2 FOR UPDATE",
                (episode_id, key))
            if prior_authorization:
                exact = (str(prior_authorization.get("AUTHORIZATION_ID")) == auth_id
                         and str(prior_authorization.get("UNKNOWN_GENERATION_KEY")) == str(old.get("GENERATION_KEY"))
                         and str(prior_authorization.get("EVIDENCE_SHA256")) == evidence_sha
                         and str(prior_authorization.get("AUTHORIZED_BY")) == actor
                         and str(prior_authorization.get("RISK_ASSESSMENT")) == risk
                         and int(prior_authorization.get("DUPLICATE_CHARGE_ACK") or 0) == 1)
                if exact:
                    return {"status": "ALREADY_AUTHORIZED", "authorization_id": auth_id,
                            "attempt_index": 2, "evidence_sha256": evidence_sha}
                raise UnknownRecoveryDenied("UNKNOWN_RECOVERY_ALREADY_AUTHORIZED_DIFFERENT_EVIDENCE")
            connection.execute(
                "INSERT INTO TB_GENERATION_UNKNOWN_RECOVERY_AUTHORIZATION "
                "(AUTHORIZATION_ID,EPISODE_ID,LOGICAL_ASSET_KEY,UNKNOWN_ATTEMPT_INDEX,UNKNOWN_GENERATION_KEY,"
                "TARGET_ATTEMPT_INDEX,EVIDENCE_JSON,EVIDENCE_SHA256,RISK_ASSESSMENT,AUTHORIZED_BY,AUTHORIZED_AT,"
                "DUPLICATE_CHARGE_ACK) VALUES (%s,%s,%s,1,%s,2,%s,%s,%s,%s,UTC_TIMESTAMP(6),1)",
                (auth_id, episode_id, key, old["GENERATION_KEY"], evidence_blob, evidence_sha, risk, actor))
        return {"status": "AUTHORIZED_FOR_ATTEMPT_2", "authorization_id": auth_id,
                "attempt_index": 2, "evidence_sha256": evidence_sha,
                "historical_attempt_changed": False, "dispatch_performed": False}
    finally:
        connection.close()


def authorization_for_attempt_two(connection, episode_id: str, key: str,
                                  unknown_generation_key: str) -> dict | None:
    return connection.query_one(
        "SELECT AUTHORIZATION_ID, UNKNOWN_GENERATION_KEY, EVIDENCE_JSON, EVIDENCE_SHA256, "
        "AUTHORIZED_BY, RISK_ASSESSMENT, DUPLICATE_CHARGE_ACK "
        "FROM TB_GENERATION_UNKNOWN_RECOVERY_AUTHORIZATION "
        "WHERE EPISODE_ID=%s AND LOGICAL_ASSET_KEY=%s AND UNKNOWN_ATTEMPT_INDEX=1 "
        "AND TARGET_ATTEMPT_INDEX=2 AND UNKNOWN_GENERATION_KEY=%s FOR UPDATE",
        (episode_id, key, unknown_generation_key))


def has_authorized_attempt_two(connection, episode_id: str, key: str,
                               unknown_generation_key: str) -> bool:
    row = connection.query_one(
        "SELECT AUTHORIZATION_ID, EVIDENCE_JSON, EVIDENCE_SHA256, AUTHORIZED_BY, RISK_ASSESSMENT, DUPLICATE_CHARGE_ACK "
        "FROM TB_GENERATION_UNKNOWN_RECOVERY_AUTHORIZATION "
        "WHERE EPISODE_ID=%s AND LOGICAL_ASSET_KEY=%s AND UNKNOWN_ATTEMPT_INDEX=1 "
        "AND TARGET_ATTEMPT_INDEX=2 AND UNKNOWN_GENERATION_KEY=%s LIMIT 1",
        (episode_id, key, unknown_generation_key))
    return valid_authorization_record(row)


def load_authorized_attempt_two(ep: str | Path, logical_asset_key: str,
                                unknown_generation_key: str) -> dict | None:
    episode_id = logical_asset_identity.episode_id(Path(ep).resolve())
    connection = _connect()
    try:
        return connection.query_one(
            "SELECT AUTHORIZATION_ID, EVIDENCE_JSON, EVIDENCE_SHA256, AUTHORIZED_BY, RISK_ASSESSMENT, DUPLICATE_CHARGE_ACK "
            "FROM TB_GENERATION_UNKNOWN_RECOVERY_AUTHORIZATION "
            "WHERE EPISODE_ID=%s AND LOGICAL_ASSET_KEY=%s AND UNKNOWN_ATTEMPT_INDEX=1 "
            "AND TARGET_ATTEMPT_INDEX=2 AND UNKNOWN_GENERATION_KEY=%s LIMIT 1",
            (episode_id, logical_asset_key, unknown_generation_key))
    finally:
        connection.close()
