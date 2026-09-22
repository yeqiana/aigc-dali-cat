from __future__ import annotations

import hashlib
import json
from copy import deepcopy


_UPSERT_SQL = """
INSERT INTO TB_PRODUCTION_LEDGER_AUTHORITY (
    EPISODE_ID, SCHEMA_VERSION, ENGINE_VERSION, DOCUMENT_BLOB, SHA256, BYTE_SIZE
) VALUES (%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    SCHEMA_VERSION=VALUES(SCHEMA_VERSION),
    ENGINE_VERSION=VALUES(ENGINE_VERSION),
    DOCUMENT_BLOB=VALUES(DOCUMENT_BLOB),
    SHA256=VALUES(SHA256),
    BYTE_SIZE=VALUES(BYTE_SIZE),
    UPDATE_TIME=CURRENT_TIMESTAMP(6)
""".strip()

_GET_SQL = """
SELECT EPISODE_ID, SCHEMA_VERSION, ENGINE_VERSION, DOCUMENT_BLOB,
       SHA256, BYTE_SIZE, CREATE_TIME, UPDATE_TIME
FROM TB_PRODUCTION_LEDGER_AUTHORITY
WHERE EPISODE_ID=%s
LIMIT 1
""".strip()


def canonical_bytes(document: dict) -> bytes:
    if not isinstance(document, dict):
        raise ValueError("production ledger authority must be an object")
    return json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


class MySqlProductionLedgerAuthorityRepository:
    """Lossless MySQL authority for the complete production ledger document.

    Typed frame/attempt tables remain the query projection.  This table closes
    the mysql-only cutover gap by keeping every extension field losslessly in
    MySQL without adding another MySQL JSON column.
    """

    def __init__(self, connection):
        self.connection = connection

    def upsert(self, episode_id: str, document: dict) -> dict:
        payload = canonical_bytes(deepcopy(document))
        digest = hashlib.sha256(payload).hexdigest()
        self.connection.execute(
            _UPSERT_SQL,
            (
                str(episode_id),
                int(document.get("schema_version") or 1),
                str(document.get("engine_version") or "") or None,
                payload,
                digest,
                len(payload),
            ),
        )
        return {
            "episode_id": str(episode_id),
            "sha256": digest,
            "byte_size": len(payload),
        }

    def get(self, episode_id: str) -> dict | None:
        row = self.connection.query_one(_GET_SQL, (str(episode_id),))
        if not row:
            return None
        raw = row.get("DOCUMENT_BLOB") if "DOCUMENT_BLOB" in row else row.get("document_blob")
        if isinstance(raw, memoryview):
            raw = raw.tobytes()
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        if not isinstance(raw, (bytes, bytearray)):
            raise ValueError("production ledger authority blob is invalid")
        payload = bytes(raw)
        expected_size = int(row.get("BYTE_SIZE") or row.get("byte_size") or 0)
        expected_sha = str(row.get("SHA256") or row.get("sha256") or "").lower()
        if expected_size and expected_size != len(payload):
            raise ValueError("production ledger authority byte-size mismatch")
        actual_sha = hashlib.sha256(payload).hexdigest()
        if expected_sha and expected_sha != actual_sha:
            raise ValueError("production ledger authority sha256 mismatch")
        decoded = json.loads(payload.decode("utf-8"))
        if not isinstance(decoded, dict):
            raise ValueError("production ledger authority document must decode to object")
        return {
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "schema_version": row.get("SCHEMA_VERSION") or row.get("schema_version"),
            "engine_version": row.get("ENGINE_VERSION") or row.get("engine_version"),
            "sha256": actual_sha,
            "byte_size": len(payload),
            "document": decoded,
            "create_time": row.get("CREATE_TIME") or row.get("create_time"),
            "update_time": row.get("UPDATE_TIME") or row.get("update_time"),
        }
