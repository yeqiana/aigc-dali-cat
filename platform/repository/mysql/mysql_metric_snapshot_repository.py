from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from platform.repository.mysql.payload_policy import (
    bounded_json,
    metric_snapshot_projection,
)


_UPSERT_SQL = """
INSERT INTO TB_METRIC_SNAPSHOT (
    METRIC_ID, EPISODE_ID, METRIC_TYPE, SOURCE_FINGERPRINT, PAYLOAD, OBSERVED_TIME
) VALUES (%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    SOURCE_FINGERPRINT=VALUES(SOURCE_FINGERPRINT),
    PAYLOAD=VALUES(PAYLOAD),
    OBSERVED_TIME=VALUES(OBSERVED_TIME)
""".strip()

_LATEST_SQL = """
SELECT METRIC_ID, EPISODE_ID, METRIC_TYPE, SOURCE_FINGERPRINT, PAYLOAD, OBSERVED_TIME
FROM TB_METRIC_SNAPSHOT
WHERE EPISODE_ID=%s AND METRIC_TYPE=%s
ORDER BY OBSERVED_TIME DESC, CREATE_TIME DESC, METRIC_ID DESC
LIMIT 1
""".strip()

_BY_ID_SQL = """
SELECT METRIC_ID, EPISODE_ID, METRIC_TYPE, SOURCE_FINGERPRINT, PAYLOAD, OBSERVED_TIME
FROM TB_METRIC_SNAPSHOT
WHERE METRIC_ID=%s
LIMIT 1
""".strip()


def metric_id(episode_id: str, metric_type: str, source_fingerprint: str | None) -> str:
    raw = f"{episode_id}|{metric_type}|{source_fingerprint or ''}".encode("utf-8")
    return "MS_" + hashlib.sha256(raw).hexdigest()[:48]


class MySqlMetricSnapshotRepository:
    def __init__(self, connection):
        self.connection = connection

    def upsert(self, record: dict) -> dict:
        row = deepcopy(record)
        required = ("episode_id", "metric_type", "payload", "observed_time")
        missing = [key for key in required if row.get(key) in (None, "")]
        if missing:
            raise ValueError("metric snapshot missing required fields: " + ", ".join(missing))
        episode_id = str(row["episode_id"])
        metric_type = str(row["metric_type"])
        source_fingerprint = str(row.get("source_fingerprint") or "") or None
        mid = str(row.get("metric_id") or metric_id(episode_id, metric_type, source_fingerprint))
        payload_value = row["payload"]
        if row.get("payload_ref") is not None:
            payload_value = metric_snapshot_projection(payload_value, row["payload_ref"])
        payload = bounded_json(payload_value, entity="metric snapshot")
        self.connection.execute(
            _UPSERT_SQL,
            (mid, episode_id, metric_type, source_fingerprint, payload, row["observed_time"]),
        )
        return {"metric_id": mid, "episode_id": episode_id, "metric_type": metric_type}

    def get_latest(self, episode_id: str, metric_type: str) -> dict | None:
        row = self.connection.query_one(_LATEST_SQL, (str(episode_id), str(metric_type)))
        return self._decode(row)

    def get_by_id(self, metric_id_value: str) -> dict | None:
        row = self.connection.query_one(_BY_ID_SQL, (str(metric_id_value),))
        return self._decode(row)

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
            "metric_id": row.get("METRIC_ID") or row.get("metric_id"),
            "episode_id": row.get("EPISODE_ID") or row.get("episode_id"),
            "metric_type": row.get("METRIC_TYPE") or row.get("metric_type"),
            "source_fingerprint": row.get("SOURCE_FINGERPRINT") or row.get("source_fingerprint"),
            "observed_time": row.get("OBSERVED_TIME") or row.get("observed_time"),
            "payload": payload,
        }
