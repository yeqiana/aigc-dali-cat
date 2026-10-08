from __future__ import annotations
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
SYSTEM=ROOT/"episodes"/"_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0,str(SYSTEM))
import scoped_codex_worker as sw


def test_preimage_runner_request_id_is_forwarded_end_to_end(monkeypatch,tmp_path):
    record={}
    monkeypatch.setattr(sw,"prompt",lambda ep,step:"real bounded preimage prompt")
    monkeypatch.setattr(sw,"resolved_model",lambda step,ep:{"model":"gpt-6-luna","reasoning_effort":"high","model_policy_sha256":"a"*64,"role":"preimage.world_prepare"})
    monkeypatch.setattr(sw,"_attach",lambda *args,**kwargs:(None,False))
    monkeypatch.setattr(sw,"resolve_codex",lambda _raw:"codex")
    monkeypatch.setattr(sw.codex_user_runner,"bridge_required",lambda:True)
    monkeypatch.setattr(sw,"attach_source_sha256",lambda ep,step:"b"*64)
    monkeypatch.setattr(sw,"scoped_fingerprint",lambda *args:"c"*64)
    monkeypatch.setattr(sw.episode_performance,"safe_begin_stage",lambda *args,**kwargs:"test")
    monkeypatch.setattr(sw.episode_performance,"safe_end_stage",lambda *args,**kwargs:None)
    monkeypatch.setattr(sw.inflight_codex_task,"begin",lambda *args,**kwargs:record.update(request_id=kwargs["request_id"],stdin_sha256=kwargs["stdin_sha256"]))
    monkeypatch.setattr(sw.inflight_codex_task,"clear",lambda *args,**kwargs:record.update(cleared=True))
    def fake_model(*args,**kwargs):
        record["forwarded_request_id"]=kwargs.get("runner_request_id")
        return 0,{"status":"SUCCESS"}
    monkeypatch.setattr(sw,"execute_model_call",fake_model)
    rc,_=sw.run_step(tmp_path,"PREIMAGE_WORLD",codex_raw="codex",timeout=900)
    assert rc==0
    assert len(record["request_id"])==32
    assert record["forwarded_request_id"]==record["request_id"]
    assert record["cleared"] is True


def test_execute_model_call_uses_runner_exact_request_id(monkeypatch,tmp_path):
    import logical_asset_identity
    record={}
    monkeypatch.setattr(sw,"resolve_codex",lambda _raw:"codex")
    monkeypatch.setattr(sw,"codex_exec_command",lambda *args,**kwargs:["codex","exec","-"])
    monkeypatch.setattr(sw,"_model_event",lambda *args,**kwargs:None)
    monkeypatch.setattr(sw.runtime_observability,"now",lambda :"2026-10-08T16:20:00+08:00")
    monkeypatch.setattr(sw.runtime_observability,"write_model_execution_receipt",lambda ep,receipt:tmp_path/"receipt.json")
    monkeypatch.setattr(logical_asset_identity,"episode_id",lambda ep:"00-05")
    def fake_run_codex(*args,**kwargs):
        record["request_id"]=kwargs.get("request_id")
        return SimpleNamespace(returncode=0,remote={"request_id":kwargs.get("request_id")})
    monkeypatch.setattr(sw.codex_user_runner,"run_codex",fake_run_codex)
    rid="a"*32
    rc,receipt=sw.execute_model_call(tmp_path,"PREIMAGE_WORLD",{
        "model":"gpt-6-luna","reasoning_effort":"high","role":"preimage.world_prepare",
    },"bounded candidate",runner_request_id=rid)
    assert rc==0
    assert record["request_id"]==rid
    assert receipt["runner_request_id"]==rid
