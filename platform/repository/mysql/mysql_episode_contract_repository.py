from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from platform.repository.mysql.payload_policy import (
    bounded_json,
    projection_envelope,
)


_LATEST_SQL = """
SELECT CONTRACT_ID, EPISODE_ID, CONTRACT_TYPE, VERSION_NO,
       STATUS, SHA256, SOURCE_SHA256, PAYLOAD, CREATE_TIME
FROM TB_EPISODE_CONTRACT
WHERE EPISODE_ID=%s AND CONTRACT_TYPE=%s
ORDER BY VERSION_NO DESC
LIMIT 1
""".strip()

_LIST_TYPE_SQL = """
SELECT CONTRACT_ID, EPISODE_ID, CONTRACT_TYPE, VERSION_NO,
       STATUS, SHA256, SOURCE_SHA256, PAYLOAD, CREATE_TIME
FROM TB_EPISODE_CONTRACT
WHERE EPISODE_ID=%s AND CONTRACT_TYPE=%s
ORDER BY VERSION_NO ASC
""".strip()

_UPSERT_SQL = """
INSERT INTO TB_EPISODE_CONTRACT (
    CONTRACT_ID, EPISODE_ID, CONTRACT_TYPE, VERSION_NO,
    STATUS, SHA256, SOURCE_SHA256, PAYLOAD
) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    STATUS=VALUES(STATUS),
    SOURCE_SHA256=VALUES(SOURCE_SHA256),
    PAYLOAD=VALUES(PAYLOAD)
""".strip()


_LATEST_FOR_UPDATE_SQL = _LATEST_SQL + "\nFOR UPDATE"
# The CAS path must never mutate historical rows via ON DUPLICATE KEY UPDATE.
_CAS_INSERT_SQL = """
INSERT INTO TB_EPISODE_CONTRACT (
    CONTRACT_ID, EPISODE_ID, CONTRACT_TYPE, VERSION_NO,
    STATUS, SHA256, SOURCE_SHA256, PAYLOAD
) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
""".strip()

def contract_id(episode_id: str, contract_type: str, sha256: str) -> str:
    raw = f"{episode_id}|{contract_type}|{sha256}".encode("utf-8")
    return "EC_" + hashlib.sha256(raw).hexdigest()[:48]


class MySqlEpisodeContractRepository:
    """Versioned durable Episode-level Contract repository."""

    def __init__(self, connection):
        self.connection = connection

    def save_version(self, record: dict) -> dict:
        row = deepcopy(record)
        required = ("episode_id", "contract_type", "status", "sha256", "payload")
        missing = [key for key in required if row.get(key) in (None, "")]
        if missing:
            raise ValueError("episode contract missing required fields: " + ", ".join(missing))

        episode_id = str(row["episode_id"])
        contract_type = str(row["contract_type"])
        sha = str(row["sha256"]).lower()
        latest = self.connection.query_one(
            _LATEST_SQL, (episode_id, contract_type)
        ) or {}
        latest_sha = str(latest.get("SHA256") or latest.get("sha256") or "").lower()
        if latest_sha == sha:
            version_no = int(latest.get("VERSION_NO") or latest.get("version_no") or 1)
            cid = str(
                latest.get("CONTRACT_ID")
                or latest.get("contract_id")
                or contract_id(episode_id, contract_type, sha)
            )
        else:
            version_no = int(latest.get("VERSION_NO") or latest.get("version_no") or 0) + 1
            cid = contract_id(episode_id, contract_type, sha)

        payload_value = row["payload"]
        if row.get("payload_ref") is not None:
            payload_value = projection_envelope(
                payload_value,
                row["payload_ref"],
                "EPISODE_CONTRACT_REF",
                {
                    "contract_type": contract_type,
                    "status": str(row["status"]),
                },
            )
        encoded = bounded_json(payload_value, entity="episode contract")
        self.connection.execute(
            _UPSERT_SQL,
            (
                cid,
                episode_id,
                contract_type,
                version_no,
                str(row["status"]),
                sha,
                row.get("source_sha256"),
                encoded,
            ),
        )
        return {
            "contract_id": cid,
            "episode_id": episode_id,
            "contract_type": contract_type,
            "version_no": version_no,
            "sha256": sha,
        }

    def save_version_if_latest(self, record: dict, *, expected_sha256: str) -> dict:
        """Append atomically iff MySQL's most recent contract SHA still matches.

        Lock the latest row and insert the next version on a single pinned
        transaction connection. MySQL's unique version key is the backstop.
        """
        row = deepcopy(record)
        for key in ("episode_id", "contract_type", "status", "sha256", "payload"):
            if row.get(key) in (None, ""):
                raise ValueError(f"episode contract missing required field: {key}")
        expected = str(expected_sha256 or "").lower()
        if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
            raise ValueError("EPISODE_CONTRACT_CAS_INVALID_EXPECTED_SHA")
        episode_id = str(row["episode_id"])
        contract_type = str(row["contract_type"])
        new_sha = str(row["sha256"]).lower()
        if len(new_sha) != 64 or any(c not in "0123456789abcdef" for c in new_sha):
            raise ValueError("EPISODE_CONTRACT_CAS_INVALID_NEW_SHA")
        payload_value = row["payload"]
        if row.get("payload_ref") is not None:
            payload_value = projection_envelope(
                payload_value, row["payload_ref"], "EPISODE_CONTRACT_REF",
                {"contract_type": contract_type, "status": str(row["status"])},
            )
        encoded = bounded_json(payload_value, entity="episode contract")
        with self.connection.transaction():
            latest = self.connection.query_one(
                _LATEST_FOR_UPDATE_SQL, (episode_id, contract_type)
            )
            if not latest:
                raise ValueError("EPISODE_CONTRACT_CAS_LATEST_MISSING")
            previous_sha = str(
                latest.get("SHA256") or latest.get("sha256") or ""
            ).lower()
            if previous_sha != expected:
                raise ValueError("EPISODE_CONTRACT_CAS_STALE_AUTHORITY")
            version_no = int(latest.get("VERSION_NO") or latest.get("version_no") or 0)
            if new_sha == expected:
                return {
                    "contract_id": latest.get("CONTRACT_ID") or latest.get("contract_id"),
                    "episode_id": episode_id,
                    "contract_type": contract_type,
                    "version_no": version_no,
                    "sha256": new_sha,
                    "unchanged": True,
                }
            version_no += 1
            cid = contract_id(episode_id, contract_type, new_sha)
            self.connection.execute(
                _CAS_INSERT_SQL,
                (cid, episode_id, contract_type, version_no,
                 str(row["status"]), new_sha, row.get("source_sha256"), encoded),
            )
        return {
            "contract_id": cid, "episode_id": episode_id,
            "contract_type": contract_type, "version_no": version_no,
            "sha256": new_sha, "unchanged": False,
        }

    def get_latest(self, episode_id: str, contract_type: str) -> dict | None:
        return self._decode(
            self.connection.query_one(
                _LATEST_SQL, (str(episode_id), str(contract_type))
            )
        )

    def list_versions(self, episode_id: str, contract_type: str) -> list[dict]:
        rows = self.connection.query_all(
            _LIST_TYPE_SQL, (str(episode_id), str(contract_type))
        ) or []
        return [decoded for row in rows if (decoded := self._decode(row)) is not None]

    @staticmethod
    def _decode(row: dict | None) -> dict | None:
        if not row:
            return None
        payload = row.get("PAYLOAD") if "PAYLOAD" in row else row.get("payload")
        if isinstance(payload, (bytes, bytearray)):
            payload = payload.decode("utf-8")
        if isinstance(payload, str):
            payload = json.loads(payload)
        if not isinstance(payload, dict):
            raise ValueError("episode contract payload must decode to object")
        return {
            "contract_id": row.get("CONTRACT_ID") or row.get("contract_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "contract_type": row.get("CONTRACT_TYPE") or row.get("contract_type"),
            "version_no": row.get("VERSION_NO") or row.get("version_no"),
            "status": row.get("STATUS") or row.get("status"),
            "sha256": row.get("SHA256") or row.get("sha256"),
            "source_sha256": (
                row.get("SOURCE_SHA256")
                if "SOURCE_SHA256" in row
                else row.get("source_sha256")
            ),
            "payload": payload,
        }
