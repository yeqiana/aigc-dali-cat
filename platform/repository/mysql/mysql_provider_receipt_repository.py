from __future__ import annotations

import json
from copy import deepcopy
from platform.repository.mysql.payload_policy import bounded_json


_UPSERT_SQL = """
INSERT INTO TB_PROVIDER_RECEIPT (
    RECEIPT_ID, EPISODE_ID, ATTEMPT_ID, PROVIDER, MODEL, STATUS,
    ERROR_CODE, REQUEST_ID, LEGACY_PATH, LEGACY_SHA256, PAYLOAD
) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    ATTEMPT_ID=VALUES(ATTEMPT_ID),
    PROVIDER=VALUES(PROVIDER),
    MODEL=VALUES(MODEL),
    STATUS=VALUES(STATUS),
    ERROR_CODE=VALUES(ERROR_CODE),
    REQUEST_ID=VALUES(REQUEST_ID),
    LEGACY_PATH=VALUES(LEGACY_PATH),
    LEGACY_SHA256=VALUES(LEGACY_SHA256),
    PAYLOAD=VALUES(PAYLOAD)
""".strip()

_BY_LEGACY_PATH_SQL = """
SELECT RECEIPT_ID, EPISODE_ID, STATUS, LEGACY_PATH, LEGACY_SHA256, PAYLOAD
FROM TB_PROVIDER_RECEIPT
WHERE EPISODE_ID=%s AND LEGACY_PATH=%s
LIMIT 1
""".strip()


class MySqlProviderReceiptRepository:
    """V2 durable repository for image-provider receipts."""

    def __init__(self, connection):
        self.connection = connection

    def upsert(self, record: dict) -> None:
        row = deepcopy(record)
        required = ("receipt_id", "episode_id", "provider", "status", "payload")
        missing = [key for key in required if not row.get(key)]
        if missing:
            raise ValueError(
                "provider receipt missing required fields: " + ", ".join(missing)
            )
        payload = bounded_json(row["payload"], entity="provider receipt")
        self.connection.execute(
            _UPSERT_SQL,
            (
                row["receipt_id"], row["episode_id"], row.get("attempt_id"),
                row["provider"], row.get("model"), row["status"],
                row.get("error_code"), row.get("request_id"),
                row.get("legacy_path"), row.get("legacy_sha256"), payload,
            ),
        )

    def get_by_legacy_path(self, episode_id: str, legacy_path: str) -> dict | None:
        row = self.connection.query_one(
            _BY_LEGACY_PATH_SQL, (str(episode_id), str(legacy_path))
        )
        if not row:
            return None
        payload = row.get("PAYLOAD") if "PAYLOAD" in row else row.get("payload")
        if isinstance(payload, (bytes, bytearray)):
            payload = payload.decode("utf-8")
        if isinstance(payload, str):
            payload = json.loads(payload)
        if not isinstance(payload, dict):
            raise ValueError("provider receipt payload must decode to object")
        return {
            "receipt_id": row.get("RECEIPT_ID") or row.get("receipt_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "status": row.get("STATUS") or row.get("status"),
            "legacy_path": row.get("LEGACY_PATH") or row.get("legacy_path"),
            "legacy_sha256": row.get("LEGACY_SHA256") or row.get("legacy_sha256"),
            "payload": payload,
        }
