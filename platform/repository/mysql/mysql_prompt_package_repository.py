from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from platform.repository.mysql.payload_policy import (
    bounded_json,
    prompt_package_projection,
)


_UPSERT_SQL = """
INSERT INTO TB_PROMPT_PACKAGE (
    PROMPT_PACKAGE_ID, EPISODE_ID, FRAME_NO, PACKAGE_TYPE, SHA256, PAYLOAD
) VALUES (%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    PACKAGE_TYPE=VALUES(PACKAGE_TYPE),
    SHA256=VALUES(SHA256),
    PAYLOAD=VALUES(PAYLOAD)
""".strip()

_LATEST_SQL = """
SELECT PROMPT_PACKAGE_ID, EPISODE_ID, FRAME_NO, PACKAGE_TYPE, SHA256, PAYLOAD, CREATE_TIME
FROM TB_PROMPT_PACKAGE
WHERE EPISODE_ID=%s AND FRAME_NO=%s AND PACKAGE_TYPE=%s
ORDER BY CREATE_TIME DESC, PROMPT_PACKAGE_ID DESC
LIMIT 1
""".strip()

_BY_ID_SQL = """
SELECT PROMPT_PACKAGE_ID, EPISODE_ID, FRAME_NO, PACKAGE_TYPE, SHA256, PAYLOAD, CREATE_TIME
FROM TB_PROMPT_PACKAGE
WHERE PROMPT_PACKAGE_ID=%s
LIMIT 1
""".strip()


def _package_id(episode_id: str, frame_no: int, package_type: str, sha256: str) -> str:
    raw = f"{episode_id}|{int(frame_no)}|{package_type}|{sha256}".encode("utf-8")
    return "PP_" + hashlib.sha256(raw).hexdigest()[:48]


class MySqlPromptPackageRepository:
    """Durable store for generated per-frame Prompt Packages."""

    def __init__(self, connection):
        self.connection = connection

    def upsert(self, record: dict) -> dict:
        row = deepcopy(record)
        required = ("episode_id", "frame_no", "package_type", "sha256", "payload")
        missing = [key for key in required if row.get(key) in (None, "")]
        if missing:
            raise ValueError("prompt package missing required fields: " + ", ".join(missing))
        episode_id = str(row["episode_id"])
        frame_no = int(row["frame_no"])
        package_type = str(row["package_type"])
        sha = str(row["sha256"]).lower()
        package_id = str(row.get("prompt_package_id") or _package_id(episode_id, frame_no, package_type, sha))
        payload_value = row["payload"]
        if row.get("payload_ref") is not None:
            payload_value = prompt_package_projection(payload_value, row["payload_ref"])
        payload = bounded_json(payload_value, entity="prompt package")
        self.connection.execute(
            _UPSERT_SQL,
            (package_id, episode_id, frame_no, package_type, sha, payload),
        )
        return {
            "prompt_package_id": package_id,
            "episode_id": episode_id,
            "frame_no": frame_no,
            "package_type": package_type,
            "sha256": sha,
        }

    def get_latest(self, episode_id: str, frame_no: int, package_type: str = "IMAGE") -> dict | None:
        row = self.connection.query_one(
            _LATEST_SQL, (str(episode_id), int(frame_no), str(package_type))
        )
        return self._decode(row)

    def get_by_id(self, prompt_package_id: str) -> dict | None:
        return self._decode(self.connection.query_one(_BY_ID_SQL, (str(prompt_package_id),)))

    @staticmethod
    def _decode(row: dict | None) -> dict | None:
        if not row:
            return None
        payload = row.get("PAYLOAD") if "PAYLOAD" in row else row.get("payload")
        if isinstance(payload, str):
            payload = json.loads(payload)
        if not isinstance(payload, dict):
            return None
        return {
            "prompt_package_id": row.get("PROMPT_PACKAGE_ID") or row.get("prompt_package_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "frame_no": row.get("FRAME_NO") or row.get("frame_no"),
            "package_type": row.get("PACKAGE_TYPE") or row.get("package_type"),
            "sha256": row.get("SHA256") or row.get("sha256"),
            "payload": payload,
        }
