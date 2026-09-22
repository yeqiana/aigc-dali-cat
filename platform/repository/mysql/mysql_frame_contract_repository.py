from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from platform.repository.frame_contract_projection import make_projection
from platform.repository.mysql.payload_policy import bounded_json


_LATEST_SQL = """
SELECT FRAME_CONTRACT_ID, VERSION_NO, SHA256
FROM TB_FRAME_CONTRACT
WHERE EPISODE_ID=%s AND FRAME_NO=%s
ORDER BY VERSION_NO DESC
LIMIT 1
""".strip()

_LOAD_LATEST_SQL = """
SELECT FRAME_CONTRACT_ID, EPISODE_ID, FRAME_NO, VERSION_NO,
       STATUS, SHA256, SOURCE_SHA256, PAYLOAD
FROM TB_FRAME_CONTRACT
WHERE EPISODE_ID=%s AND FRAME_NO=%s
ORDER BY VERSION_NO DESC
LIMIT 1
""".strip()

_LIST_SQL = """
SELECT FRAME_CONTRACT_ID, EPISODE_ID, FRAME_NO, VERSION_NO,
       STATUS, SHA256, SOURCE_SHA256, PAYLOAD
FROM TB_FRAME_CONTRACT
ORDER BY EPISODE_ID, FRAME_NO, VERSION_NO
""".strip()

_BY_ID_SQL = """
SELECT FRAME_CONTRACT_ID, EPISODE_ID, FRAME_NO, VERSION_NO,
       STATUS, SHA256, SOURCE_SHA256, PAYLOAD
FROM TB_FRAME_CONTRACT
WHERE FRAME_CONTRACT_ID=%s
LIMIT 1
""".strip()

_COMPACT_PAYLOAD_SQL = """
UPDATE TB_FRAME_CONTRACT
SET PAYLOAD=%s
WHERE FRAME_CONTRACT_ID=%s
""".strip()

_UPSERT_SQL = """
INSERT INTO TB_FRAME_CONTRACT (
    FRAME_CONTRACT_ID, EPISODE_ID, FRAME_NO, VERSION_NO,
    STATUS, SHA256, SOURCE_SHA256, PAYLOAD
) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    STATUS=VALUES(STATUS),
    SOURCE_SHA256=VALUES(SOURCE_SHA256),
    PAYLOAD=VALUES(PAYLOAD)
""".strip()


def _contract_id(episode_id: str, frame_no: int, sha256: str) -> str:
    raw = f"{episode_id}|{int(frame_no)}|{sha256}".encode("utf-8")
    return "FC_" + hashlib.sha256(raw).hexdigest()[:48]


class MySqlFrameContractRepository:
    """Versioned durable store for resolved Frame Contracts.

    A repeated compile with the same SHA updates the current version in-place.
    A semantic/source change that produces a new SHA appends a new VERSION_NO.
    MySQL is the preferred read surface in dual mode; JSON remains fallback.
    """

    def __init__(self, connection):
        self.connection = connection

    def save_version(self, record: dict) -> dict:
        row = deepcopy(record)
        required = ("episode_id", "frame_no", "status", "sha256", "payload")
        missing = [key for key in required if row.get(key) in (None, "")]
        if missing:
            raise ValueError("frame contract missing required fields: " + ", ".join(missing))

        episode_id = str(row["episode_id"])
        frame_no = int(row["frame_no"])
        sha = str(row["sha256"]).lower()
        latest = self.connection.query_one(_LATEST_SQL, (episode_id, frame_no)) or {}
        latest_sha = str(latest.get("SHA256") or latest.get("sha256") or "").lower()
        if latest_sha == sha:
            version_no = int(latest.get("VERSION_NO") or latest.get("version_no") or 1)
            contract_id = str(
                latest.get("FRAME_CONTRACT_ID")
                or latest.get("frame_contract_id")
                or _contract_id(episode_id, frame_no, sha)
            )
        else:
            version_no = int(latest.get("VERSION_NO") or latest.get("version_no") or 0) + 1
            contract_id = _contract_id(episode_id, frame_no, sha)

        payload_value = row["payload"]
        if row.get("payload_ref") is not None:
            payload_value = make_projection(payload_value, row["payload_ref"])
        payload = bounded_json(payload_value, entity="frame contract")
        self.connection.execute(
            _UPSERT_SQL,
            (
                contract_id,
                episode_id,
                frame_no,
                version_no,
                row["status"],
                sha,
                row.get("source_sha256"),
                payload,
            ),
        )
        return {
            "frame_contract_id": contract_id,
            "episode_id": episode_id,
            "frame_no": frame_no,
            "version_no": version_no,
            "sha256": sha,
        }

    def get_latest(self, episode_id: str, frame_no: int) -> dict | None:
        row = self.connection.query_one(_LOAD_LATEST_SQL, (str(episode_id), int(frame_no)))
        return self._decode_row(row)

    def list_versions(self) -> list[dict]:
        return [self._decode_row(row) for row in self.connection.query_all(_LIST_SQL) if row]

    def get_by_id(self, contract_id: str) -> dict | None:
        return self._decode_row(self.connection.query_one(_BY_ID_SQL, (str(contract_id),)))

    def compact_payload(self, contract_id: str, payload: dict, document_ref: dict) -> dict:
        projection = make_projection(payload, document_ref)
        encoded = bounded_json(projection, entity="frame contract projection")
        affected = self.connection.execute(_COMPACT_PAYLOAD_SQL, (encoded, str(contract_id)))
        return {
            "frame_contract_id": str(contract_id),
            "payload_bytes": len(encoded.encode("utf-8")),
            "affected": affected,
        }

    @staticmethod
    def _decode_row(row: dict | None) -> dict | None:
        if not row:
            return None
        payload = row.get("PAYLOAD") if "PAYLOAD" in row else row.get("payload")
        if isinstance(payload, str):
            payload = json.loads(payload)
        if not isinstance(payload, dict):
            return None
        return {
            "frame_contract_id": row.get("FRAME_CONTRACT_ID") or row.get("frame_contract_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "frame_no": row.get("FRAME_NO") or row.get("frame_no"),
            "version_no": row.get("VERSION_NO") or row.get("version_no"),
            "status": row.get("STATUS") or row.get("status"),
            "sha256": row.get("SHA256") or row.get("sha256"),
            "source_sha256": row.get("SOURCE_SHA256") or row.get("source_sha256"),
            "payload": payload,
        }
