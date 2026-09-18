from __future__ import annotations

import hashlib
import json
from pathlib import Path

import episode_identity
import storage_config
import story_json
import runtime_workspace
from platform.repository.mysql.payload_policy import MAX_INLINE_PAYLOAD_BYTES, document_reference, payload_bytes, payload_sha256

DELEGATED_BUNDLE="DELEGATED_BUNDLE"
FINAL_ACCEPTANCE="FINAL_ACCEPTANCE"
PRODUCTION_APPROVAL="PRODUCTION_APPROVAL"
REL_BY_TYPE={
    DELEGATED_BUNDLE:Path("meta/delegated-approvals.json"),
    FINAL_ACCEPTANCE:Path("meta/final-acceptance.json"),
    PRODUCTION_APPROVAL:Path("meta/production-approval.json"),
}

def _episode_id(ep: Path) -> str:
    return episode_identity.storage_episode_id(Path(ep).resolve())

def payload_sha(payload: dict | None) -> str:
    if not isinstance(payload,dict): return ""
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def _decision(kind: str, payload: dict) -> str:
    if kind==DELEGATED_BUNDLE:
        approvals=payload.get("approvals") or {}
        return "APPROVED" if approvals and all(isinstance(v,dict) and v.get("approved") is True for v in approvals.values()) else "RECORDED"
    if kind==FINAL_ACCEPTANCE:
        return "REVOKED" if payload.get("revokes") is True else str(payload.get("decision") or "RECORDED").upper()[:32]
    if kind==PRODUCTION_APPROVAL:
        return "APPROVED" if payload.get("user_approved") is True else "RECORDED"
    return "RECORDED"

def _approver(kind: str, payload: dict) -> str:
    if kind==DELEGATED_BUNDLE: return "POLICY"
    if kind==FINAL_ACCEPTANCE: return "USER"
    if kind==PRODUCTION_APPROVAL: return "USER" if payload.get("user_approved") is True else "WORK"
    return "WORK"

def _record(ep: Path, kind: str, payload: dict) -> dict:
    if kind not in REL_BY_TYPE: raise ValueError(f"unsupported approval type: {kind}")
    if not isinstance(payload,dict): raise ValueError("approval payload must be object")
    return {
        "episode_id":_episode_id(ep),
        "approval_type":kind,
        "decision":_decision(kind,payload),
        "approver_type":_approver(kind,payload),
        "evidence_sha256":payload_sha(payload),
        "payload":payload,
    }

def persist(ep: Path, kind: str, payload: dict) -> dict:
    mode=storage_config.episode_meta_store_config()["mode"]
    if mode=="json": return {"mode":mode,"mysql_written":False}
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_approval_record_repository import MySqlApprovalRecordRepository
    from platform.repository.mysql.schema_v2 import DATABASE_NAME
    connection=MySqlConnection(**storage_config.mysql_connection_kwargs({"database":DATABASE_NAME}))
    try:
        document_ref = None
        if payload_bytes(payload) > MAX_INLINE_PAYLOAD_BYTES:
            digest = payload_sha256(payload)
            document_ref = document_reference(payload, f"meta/runtime/approvals/{kind}-{digest}.json")
            external = runtime_workspace.write_json(ep, document_ref["rel"], payload)
            document_ref["bytes"] = external.stat().st_size
        record = _record(ep,kind,payload)
        record["payload_ref"] = document_ref
        saved=MySqlApprovalRecordRepository(connection).upsert(record)
        return {"mode":mode,"mysql_written":True,**saved}
    finally: connection.close()

def load(ep: Path, kind: str) -> dict | None:
    ep=Path(ep).resolve(); mode=storage_config.episode_meta_store_config()["mode"]
    if mode in {"dual","mysql"}:
        from platform.repository.mysql.mysql_connection import MySqlConnection
        from platform.repository.mysql.mysql_approval_record_repository import MySqlApprovalRecordRepository
        from platform.repository.mysql.schema_v2 import DATABASE_NAME
        connection=None
        try:
            connection=MySqlConnection(**storage_config.mysql_connection_kwargs({"database":DATABASE_NAME}))
            row=MySqlApprovalRecordRepository(connection).get_current(_episode_id(ep),kind)
            if row and isinstance(row.get("payload"),dict):
                payload = row["payload"]
                document = payload.get("document") if payload.get("projection_type") == "APPROVAL_RECORD_REF" else None
                if isinstance(document, dict):
                    full = runtime_workspace.read_json(ep, document.get("rel"), default=None)
                    if isinstance(full, dict) and payload_sha256(full) == str(document.get("sha256") or "").lower():
                        return full
                else:
                    return payload
        except Exception: pass
        finally:
            if connection is not None: connection.close()
    path=ep/REL_BY_TYPE[kind]
    return story_json.read_json(path,default=None) if path.is_file() else None

def save(ep: Path, kind: str, payload: dict) -> dict:
    ep=Path(ep).resolve(); mode=storage_config.episode_meta_store_config()["mode"]; path=ep/REL_BY_TYPE[kind]
    if mode!="mysql":
        path.parent.mkdir(parents=True,exist_ok=True); story_json.write_json(path,payload)
    db=persist(ep,kind,payload)
    return {"path":path,**db}

def source_sha(ep: Path, kind: str) -> str:
    return payload_sha(load(ep,kind))
