"""SELECT-only four-table Production Revision schema migration plan."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT,ROOT/"episodes"/"_system",ROOT/"scripts"):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
from platform.repository.mysql import schema_v2
from storyos_revision_schema_readonly import inspect_revision_schema,REVISION_TABLES
STEPS=("create_production_revision","create_production_revision_head","create_production_revision_frame","create_production_revision_visual_admission")

def ddl():
    out=tuple((n,sql) for n,sql in schema_v2.DDL_STEPS if n in STEPS)
    if tuple(n for n,_ in out)!=STEPS: raise RuntimeError("REVISION_CANONICAL_DDL_STEPS_DRIFT")
    if any(not sql.startswith("CREATE TABLE IF NOT EXISTS "+table+" (") for (_,sql),table in zip(out,REVISION_TABLES)):
        raise RuntimeError("REVISION_CANONICAL_DDL_TARGET_DRIFT")
    return out

def plan(connection):
    r=inspect_revision_schema(connection)
    base={"status":"BLOCKED","migration_performed":False,"activation_performed":False,"ddl_authorized":False,"backup_verified":False}
    if not r.get("schema_matches"):return {**base,"reason":"DATABASE_IDENTITY_OR_CASE_MODE_MISMATCH"}
    if not all(r["dependencies"].values()):return {**base,"reason":"MISSING_REQUIRED_EXISTING_TABLE"}
    present=sum(r["revision_tables"].values())
    if 0<present<len(REVISION_TABLES):return {**base,"reason":"PARTIAL_REVISION_SCHEMA_MANUAL_RECONCILIATION"}
    if present==len(REVISION_TABLES):
        return {**base,"status":"ALREADY_INSTALLED" if r["lifecycle_constraint_ready"] else "BLOCKED",
                "reason":"NO_DDL_NEEDED" if r["lifecycle_constraint_ready"] else "OLD_REVISION_CHECK_NEEDS_SEPARATE_REVIEW"}
    return {**base,"status":"PLAN_READY_NOT_AUTHORIZED","reason":"FOUR_TABLES_ABSENT",
        "ddl_steps":[{"name":n,"sha256":hashlib.sha256(sql.encode()).hexdigest()} for n,sql in ddl()],
        "required_before_ddl":["VERIFIED_BACKUP_RESTORE","MAINTENANCE_APPROVAL",
             "SCHEDULERS_QUIESCED","RECHECK_SCHEMA","CONTROLLED_MIGRATION","POSTCHECK"]}

def main():
    from platform.repository.mysql.mysql_connection import MySqlConnection
    import storage_config
    conn=None
    try:
        conn=MySqlConnection(**storage_config.mysql_connection_kwargs({"database":schema_v2.DATABASE_NAME}))
        r=plan(conn)
    except Exception:
        r={"status":"BLOCKED","reason":"SCHEMA_QUERY_FAILED","migration_performed":False,"ddl_authorized":False}
    finally:
        if conn is not None:conn.close()
    print(json.dumps(r,ensure_ascii=False,sort_keys=True))
    return 0 if r["status"] in ("PLAN_READY_NOT_AUTHORIZED","ALREADY_INSTALLED") else 2

if __name__=="__main__":raise SystemExit(main())
