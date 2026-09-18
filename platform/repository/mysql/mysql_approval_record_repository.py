from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from platform.repository.mysql.payload_policy import (
    approval_projection,
    bounded_json,
)

_UPSERT_SQL = """
INSERT INTO TB_APPROVAL_RECORD (
    APPROVAL_ID, EPISODE_ID, APPROVAL_TYPE, DECISION, APPROVER_TYPE, EVIDENCE_SHA256, PAYLOAD
) VALUES (%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
    DECISION=VALUES(DECISION),
    APPROVER_TYPE=VALUES(APPROVER_TYPE),
    EVIDENCE_SHA256=VALUES(EVIDENCE_SHA256),
    PAYLOAD=VALUES(PAYLOAD)
""".strip()

_BY_ID_SQL = """
SELECT APPROVAL_ID, EPISODE_ID, APPROVAL_TYPE, DECISION, APPROVER_TYPE, EVIDENCE_SHA256, PAYLOAD, CREATE_TIME
FROM TB_APPROVAL_RECORD WHERE APPROVAL_ID=%s LIMIT 1
""".strip()

_LIST_SQL = """
SELECT APPROVAL_ID, EPISODE_ID, APPROVAL_TYPE, DECISION, APPROVER_TYPE, EVIDENCE_SHA256, PAYLOAD, CREATE_TIME
FROM TB_APPROVAL_RECORD WHERE EPISODE_ID=%s ORDER BY APPROVAL_TYPE
""".strip()

def approval_record_id(episode_id: str, approval_type: str) -> str:
    raw=f"{episode_id}|{approval_type}".encode("utf-8")
    return "AR_" + hashlib.sha256(raw).hexdigest()[:48]

class MySqlApprovalRecordRepository:
    def __init__(self, connection): self.connection=connection
    def upsert(self, record: dict) -> dict:
        row=deepcopy(record)
        required=("episode_id","approval_type","decision","approver_type","payload")
        missing=[k for k in required if row.get(k) in (None,"")]
        if missing: raise ValueError("approval record missing required fields: "+", ".join(missing))
        episode_id=str(row["episode_id"]); approval_type=str(row["approval_type"])
        rid=str(row.get("approval_id") or approval_record_id(episode_id,approval_type))
        payload_value = row["payload"]
        if row.get("payload_ref") is not None:
            payload_value = approval_projection(payload_value, row["payload_ref"])
        payload=bounded_json(payload_value,entity="approval record")
        self.connection.execute(_UPSERT_SQL,(rid,episode_id,approval_type,str(row["decision"]),str(row["approver_type"]),row.get("evidence_sha256"),payload))
        return {"approval_id":rid,"episode_id":episode_id,"approval_type":approval_type}
    def get_current(self, episode_id: str, approval_type: str) -> dict | None:
        return self.get_by_id(approval_record_id(str(episode_id),str(approval_type)))
    def get_by_id(self, approval_id: str) -> dict | None:
        return self._decode(self.connection.query_one(_BY_ID_SQL,(str(approval_id),)))
    def list_episode(self, episode_id: str) -> list[dict]:
        rows=self.connection.query_all(_LIST_SQL,(str(episode_id),)) or []
        return [x for r in rows if (x:=self._decode(r)) is not None]
    @staticmethod
    def _decode(row: dict | None) -> dict | None:
        if not row: return None
        payload=row.get("PAYLOAD") if "PAYLOAD" in row else row.get("payload")
        if isinstance(payload,str): payload=json.loads(payload)
        if not isinstance(payload,dict): return None
        return {
            "approval_id":row.get("APPROVAL_ID") or row.get("approval_id"),
            "episode_id":row.get("EPISODE_ID") or row.get("episode_id"),
            "approval_type":row.get("APPROVAL_TYPE") or row.get("approval_type"),
            "decision":row.get("DECISION") or row.get("decision"),
            "approver_type":row.get("APPROVER_TYPE") or row.get("approver_type"),
            "evidence_sha256":row.get("EVIDENCE_SHA256") or row.get("evidence_sha256"),
            "payload":payload,
        }
