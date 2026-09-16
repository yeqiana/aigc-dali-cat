from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from platform.repository.mysql.mysql_connection import MySqlConnection
from platform.repository.mysql.schema import DATABASE_NAME

_TABLE = f"{DATABASE_NAME}.platform_latest_record"
_SELECT_SQL = f"SELECT record_key, payload FROM {_TABLE} WHERE namespace=%s ORDER BY record_key"
_UPSERT_SQL = (
    f"INSERT INTO {_TABLE} (namespace, record_key, payload) VALUES (%s,%s,%s) "
    "ON DUPLICATE KEY UPDATE payload=VALUES(payload), updated_at=CURRENT_TIMESTAMP(6)"
)


class MySqlLatestRecordStore:
    """MySQL implementation of the Platform ``LatestRecordStore`` boundary.

    Records are namespaced so Execution and Experience share one small control-plane
    table without mixing keys. This store is non-authoritative for Episode state.
    """

    def __init__(self, connection: MySqlConnection, *, namespace: str, key_field: str) -> None:
        self.connection = connection
        self.namespace = str(namespace).strip()
        self.key_field = str(key_field).strip()
        if not self.namespace:
            raise ValueError("namespace must not be empty")
        if not self.key_field:
            raise ValueError("key_field must not be empty")
        if len(self.namespace) > 64:
            raise ValueError("namespace exceeds 64 characters")

    @staticmethod
    def _decode_payload(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            row = value
        else:
            if isinstance(value, (bytes, bytearray)):
                value = value.decode("utf-8")
            row = json.loads(str(value))
        if not isinstance(row, dict):
            raise ValueError("platform_latest_record payload must decode to an object")
        return row

    def load_all(self) -> dict[str, dict[str, Any]]:
        rows: dict[str, dict[str, Any]] = {}
        for item in self.connection.query_all(_SELECT_SQL, (self.namespace,)):
            key = str(item.get("record_key") or "").strip()
            if not key:
                raise ValueError("platform_latest_record row missing record_key")
            payload = self._decode_payload(item.get("payload"))
            payload_key = str(payload.get(self.key_field) or "").strip()
            if payload_key != key:
                raise ValueError(
                    f"platform_latest_record key mismatch: column={key!r} payload={payload_key!r}"
                )
            rows[key] = payload
        return deepcopy(rows)

    def upsert(self, record: dict[str, Any]) -> None:
        row = deepcopy(record)
        key = str(row.get(self.key_field) or "").strip()
        if not key:
            raise ValueError(f"record missing {self.key_field}")
        payload = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.connection.execute(_UPSERT_SQL, (self.namespace, key, payload))
