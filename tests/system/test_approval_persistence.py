from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; SYSTEM=ROOT/'episodes'/'_system'
if str(SYSTEM) not in sys.path: sys.path.insert(0,str(SYSTEM))
import approval_persistence as p

def test_json_mode_loads_legacy(monkeypatch,tmp_path):
    ep=tmp_path/'ep'; path=ep/p.REL_BY_TYPE[p.FINAL_ACCEPTANCE]; path.parent.mkdir(parents=True); p.story_json.write_json(path,{'decision':'accept_current_as_final'})
    monkeypatch.setattr(p.storage_config,'episode_meta_store_config',lambda:{'mode':'json'})
    assert p.load(ep,p.FINAL_ACCEPTANCE)['decision']=='accept_current_as_final'

def test_mysql_mode_loads_without_file(monkeypatch,tmp_path):
    ep=tmp_path/'ep'; monkeypatch.setattr(p.storage_config,'episode_meta_store_config',lambda:{'mode':'mysql'}); monkeypatch.setattr(p.storage_config,'mysql_connection_kwargs',lambda *_a,**_k:{}); monkeypatch.setattr(p.episode_identity,'storage_episode_id',lambda _ep:'EPU_test')
    import platform.repository.mysql.mysql_connection as mc
    import platform.repository.mysql.mysql_approval_record_repository as ar
    class C:
        def __init__(self,**_k): pass
        def close(self): pass
    monkeypatch.setattr(mc,'MySqlConnection',C); monkeypatch.setattr(ar.MySqlApprovalRecordRepository,'get_current',lambda self,*_a,**_k:{'payload':{'decision':'accept_current_as_final'}})
    assert p.load(ep,p.FINAL_ACCEPTANCE)['decision']=='accept_current_as_final'

def test_final_acceptance_sha_is_deterministic():
    a={'b':2,'a':1}; b={'a':1,'b':2}; assert p.payload_sha(a)==p.payload_sha(b)
