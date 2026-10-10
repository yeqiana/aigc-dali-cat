"""Migration planning is SELECT-only, tightly scoped and never grants DDL."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
import storyos_revision_migration_plan as m

class Db:
    def __init__(self,missing=(),db=m.schema_v2.DATABASE_NAME,case=0,states=None):
        self.missing=set(missing);self.db=db;self.case=case
        self.states=states if states is not None else ("PREPARING","CREATED","PREPARED","VISUAL_LOCK_PENDING","READY","ACTIVE","RETIRED","FAILED")
        self.calls=[]
    def query_one(self,sql,*args):
        self.calls.append(sql);assert sql.strip().upper().startswith("SELECT")
        return {"db":self.db,"case_mode":self.case,"version":"8.0.test"}
    def query_all(self,sql,params):
        self.calls.append(sql);assert sql.strip().upper().startswith("SELECT")
        if "information_schema.TABLES" in sql:
            return [{"TABLE_NAME":n} for n in m.REVISION_TABLES+("TB_GENERATION_ATTEMPT","TB_REVIEW_RECORD") if n not in self.missing]
        if "CHECK_CONSTRAINTS" in sql:
            return [{"CHECK_CLAUSE":"STATUS IN ("+",".join("'"+s+"'" for s in self.states)+")"}]
        raise AssertionError("unexpected SQL")

def test_ddl_is_exactly_four_canonical_revision_tables():
    d=m.ddl()
    assert tuple(n for n,_ in d)==m.STEPS
    assert len(d)==4
    assert not any("CREATE TABLE IF NOT EXISTS TB_GENERATION_ATTEMPT" in sql for _,sql in d)

def test_missing_four_tables_yields_plan_but_not_approval():
    c=Db(missing=m.REVISION_TABLES)
    r=m.plan(c)
    assert r["status"]=="PLAN_READY_NOT_AUTHORIZED"
    assert len(r["ddl_steps"])==4
    assert all(len(s["sha256"])==64 for s in r["ddl_steps"])
    assert not r["ddl_authorized"] and not r["migration_performed"]
    assert all(s.strip().upper().startswith("SELECT") for s in c.calls)

def test_partial_schema_blocks_without_creating_missing_tables():
    for missing in (("TB_PRODUCTION_REVISION",),m.REVISION_TABLES[:3]):
        assert m.plan(Db(missing=missing))["reason"]=="PARTIAL_REVISION_SCHEMA_MANUAL_RECONCILIATION"

def test_installed_schema_noop_and_not_approval():
    r=m.plan(Db())
    assert r["status"]=="ALREADY_INSTALLED"
    assert not r["ddl_authorized"]

def test_old_constraint_requires_separate_review():
    r=m.plan(Db(states=("PREPARING","ACTIVE","RETIRED")))
    assert r["reason"]=="OLD_REVISION_CHECK_NEEDS_SEPARATE_REVIEW"

def test_missing_preexisting_review_table_blocks():
    r=m.plan(Db(missing=m.REVISION_TABLES+("TB_REVIEW_RECORD",)))
    assert r["reason"]=="MISSING_REQUIRED_EXISTING_TABLE"

def test_wrong_database_or_case_mode_blocks():
    for c in (Db(db="story_os_runtime"),Db(case=1)):
        assert m.plan(c)["status"]=="BLOCKED"
        assert len(c.calls)==1
