from __future__ import annotations

import hashlib
import json
from copy import deepcopy


_LATEST_SQL = """
SELECT FRAME_CONTRACT_ID, VERSION_NO, SHA256
FROM TB_FRAME_CONTRACT
WHERE EPISODE_ID=%s AND FRAME_NO=%s
ORDER BY VERSION_NO DESC
LIMIT 1
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
    JSON cache files remain the compatibility read surface during dual-write.
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

        payload = json.dumps(
            row["payload"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
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

