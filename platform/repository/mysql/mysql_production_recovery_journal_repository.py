from __future__ import annotations

import hashlib
import json
from copy import deepcopy


_UPSERT_SQL = """
INSERT INTO TB_PRODUCTION_RECOVERY_JOURNAL (
    TRANSACTION_ID, EPISODE_ID, PHASE, ITEM_ID, FRAME_NO,
    DOCUMENT_BLOB, SHA256, BYTE_SIZE
) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    EPISODE_ID=VALUES(EPISODE_ID),
    PHASE=VALUES(PHASE),
    ITEM_ID=VALUES(ITEM_ID),
    FRAME_NO=VALUES(FRAME_NO),
    DOCUMENT_BLOB=VALUES(DOCUMENT_BLOB),
    SHA256=VALUES(SHA256),
    BYTE_SIZE=VALUES(BYTE_SIZE),
    UPDATE_TIME=CURRENT_TIMESTAMP(6)
""".strip()

_GET_SQL = """
SELECT TRANSACTION_ID, EPISODE_ID, PHASE, ITEM_ID, FRAME_NO,
       DOCUMENT_BLOB, SHA256, BYTE_SIZE, CREATE_TIME, UPDATE_TIME
FROM TB_PRODUCTION_RECOVERY_JOURNAL
WHERE TRANSACTION_ID=%s
LIMIT 1
""".strip()


def canonical_bytes(document: dict) -> bytes:
    if not isinstance(document, dict):
        raise ValueError("production recovery journal document must be an object")
    return json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


class MySqlProductionRecoveryJournalRepository:
    """MySQL authority for mutable Production recovery transaction state."""

    def __init__(self, connection):
        self.connection = connection

    def upsert(self, episode_id: str, transaction_id: str, document: dict) -> dict:
        row = deepcopy(document)
        phase = str(row.get("phase") or "").strip()
        if not phase:
            raise ValueError("production recovery journal phase is required")
        payload = canonical_bytes(row)
        digest = hashlib.sha256(payload).hexdigest()
        frame = row.get("frame")
        frame_no = int(frame) if frame not in (None, "") else None
        self.connection.execute(
            _UPSERT_SQL,
            (
                str(transaction_id),
                str(episode_id),
                phase,
                str(row.get("item_id") or "") or None,
                frame_no,
                payload,
                digest,
                len(payload),
            ),
        )
        return {
            "transaction_id": str(transaction_id),
            "episode_id": str(episode_id),
            "sha256": digest,
            "byte_size": len(payload),
        }

    def get(self, transaction_id: str) -> dict | None:
        row = self.connection.query_one(_GET_SQL, (str(transaction_id),))
        if not row:
            return None
        raw = row.get("DOCUMENT_BLOB") if "DOCUMENT_BLOB" in row else row.get("document_blob")
        if isinstance(raw, memoryview):
            raw = raw.tobytes()
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        if not isinstance(raw, (bytes, bytearray)):
            raise ValueError("production recovery journal blob is invalid")
        payload = bytes(raw)
        expected_size = int(row.get("BYTE_SIZE") or row.get("byte_size") or 0)
        expected_sha = str(row.get("SHA256") or row.get("sha256") or "").lower()
        if expected_size and expected_size != len(payload):
            raise ValueError("production recovery journal byte-size mismatch")
        actual_sha = hashlib.sha256(payload).hexdigest()
        if expected_sha and expected_sha != actual_sha:
            raise ValueError("production recovery journal sha256 mismatch")
        document = json.loads(payload.decode("utf-8"))
        if not isinstance(document, dict):
            raise ValueError("production recovery journal document must decode to object")
        return {
            "transaction_id": row.get("TRANSACTION_ID") or row.get("transaction_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "phase": row.get("PHASE") or row.get("phase"),
            "sha256": actual_sha,
            "byte_size": len(payload),
            "document": document,
        }
