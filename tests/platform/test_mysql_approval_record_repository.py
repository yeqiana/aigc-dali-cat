from __future__ import annotations
import json
from platform.repository.mysql.mysql_approval_record_repository import MySqlApprovalRecordRepository

class FakeConnection:
    def __init__(self,row=None): self.row=row; self.executed=[]
    def execute(self,sql,params=None): self.executed.append((sql,params)); return 1
    def query_one(self,sql,params=None): return self.row
    def query_all(self,sql,params=None): return [self.row] if self.row else []

def test_upsert_uses_stable_id():
    c=FakeConnection(); saved=MySqlApprovalRecordRepository(c).upsert({'episode_id':'EPU_1','approval_type':'FINAL_ACCEPTANCE','decision':'APPROVED','approver_type':'USER','payload':{'x':1}})
    assert saved['approval_id'].startswith('AR_'); assert json.loads(c.executed[0][1][-1])=={'x':1}

def test_get_current_decodes_payload():
    c=FakeConnection({'APPROVAL_ID':'AR_1','EPISODE_ID':'EPU_1','APPROVAL_TYPE':'FINAL_ACCEPTANCE','DECISION':'APPROVED','APPROVER_TYPE':'USER','EVIDENCE_SHA256':'a'*64,'PAYLOAD':'{"x":1}'})
    row=MySqlApprovalRecordRepository(c).get_by_id('AR_1'); assert row['payload']=={'x':1}
