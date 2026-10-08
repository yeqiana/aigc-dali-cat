from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SYSTEM=ROOT/"episodes"/"_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0,str(SYSTEM))

import preimage_timeout_candidate_recovery as recovery
import preimage_protocol as protocol


def _prepared(tmp_path,monkeypatch):
    ep=tmp_path
    snap={"snapshot_id":"abcdef123456"}
    rows=[]
    state={"snapshot_id":snap["snapshot_id"],"tasks":{}}
    receipt_dir=ep/recovery.RECEIPTS_REL
    receipt_dir.mkdir(parents=True)
    for index,kind in enumerate(recovery.tasks.TASK_TYPES):
        step=recovery.tasks.canonical_step(kind)
        path=f"meta/runtime/preimage-candidates/{kind.lower()}.json"
        candidate_file=ep/path
        candidate_file.parent.mkdir(parents=True,exist_ok=True)
        candidate_file.write_text(json.dumps({"task_type":kind,"payload":{"real":"data"}}),encoding="utf-8")
        rows.append({"task_type":kind,"task_id":f"real-task-{index}","candidate_output":path})
        status="COMPLETED" if kind=="VISUAL_NARRATIVE_PREPARE" else "FAILED"
        state["tasks"][kind]={"status":status,"task_id":f"real-task-{index}",
                              "reason":"worker rc=124" if status=="FAILED" else ""}
        ident=f"{index+1:032x}"
        receipt={"step":step,"status":"SUCCESS" if status=="COMPLETED" else "TIMEOUT",
                 "call_id":ident,"finished_at":f"2026-10-08T16:33:0{index}+08:00",
                 "requested_model":"gpt-6-luna","reasoning_effort":"high",
                 "model_binding_source":"EPISODE_BOUND_MODEL_POLICY"}
        (receipt_dir/f"{ident}.json").write_text(json.dumps(receipt),encoding="utf-8")
    original_read=recovery.story_json.read_json
    monkeypatch.setattr(recovery.story_json,"read_json",
        lambda p,default=None: state if Path(p).name==recovery.tasks.STATE_REL.name
        else original_read(p,default=default))
    monkeypatch.setattr(recovery.preimage_authority_snapshot,"stale_owned",lambda ep,s:False)
    monkeypatch.setattr(recovery.codex_user_runner,"runner_health",lambda:{"inflight_request_ids":[]})
    monkeypatch.setattr(recovery.tasks,"read_candidate",lambda ep,t:{"task_type":t["task_type"],"payload":{"real":"data"}})
    monkeypatch.setattr(recovery.tasks,"verify_candidate",lambda candidate,t:[])
    return ep,snap,rows,state


def test_timeout_artifacts_can_be_verified_without_faking_model_success(tmp_path,monkeypatch):
    ep,s,rows,state=_prepared(tmp_path,monkeypatch)
    result=recovery.inspect(ep,s,rows)
    assert result["status"]=="ELIGIBLE"
    assert result["model_timeout_count"]==3
    assert result["not_model_success"] is True
    assert [r["model_execution_status"] for r in result["tasks"]].count("TIMEOUT")==3
    assert recovery.recheck_unchanged(ep,result)
    (ep/rows[0]["candidate_output"]).write_text("modified after verification",encoding="utf-8")
    assert not recovery.recheck_unchanged(ep,result)


def test_runner_inflight_or_bad_receipt_refuses_recovery(tmp_path,monkeypatch):
    ep,s,rows,state=_prepared(tmp_path,monkeypatch)
    monkeypatch.setattr(recovery.codex_user_runner,"runner_health",lambda:{"inflight_request_ids":["live"]})
    assert recovery.inspect(ep,s,rows)["status"]=="NOT_ELIGIBLE"
    monkeypatch.setattr(recovery.codex_user_runner,"runner_health",lambda:{"inflight_request_ids":[]})
    for p in (ep/recovery.RECEIPTS_REL).glob("*.json"):
        if json.loads(p.read_text())["status"]=="TIMEOUT":
            p.unlink()
            break
    assert recovery.inspect(ep,s,rows)["status"]=="NOT_ELIGIBLE"


def test_timeout_recovery_commits_candidates_without_new_dispatch(tmp_path,monkeypatch):
    ep,s,rows,state=_prepared(tmp_path,monkeypatch)
    monkeypatch.setattr(protocol.preimage_authority_snapshot,"build",lambda *a,**k:s)
    monkeypatch.setattr(protocol.tasks,"plan_tasks",lambda *a,**k:rows)
    captured=[]
    monkeypatch.setattr(protocol,"commit_candidates",lambda *a,**k:{"status":"PASS","committed":True})
    monkeypatch.setattr(protocol.tasks,"update_task_state",lambda ep,task,status,**kw:captured.append((task["task_type"],status,kw.get("reason"))))
    written=[]
    monkeypatch.setattr(protocol.atomic,"atomic_write_json",lambda p,v:written.append(v))
    def forbidden_model(_task):
        raise AssertionError("recovery must not call model")
    result=protocol.execute_local(ep,forbidden_model)
    assert result["status"]=="PASS"
    assert result["recovery"]=="VERIFIED_TIMEOUT_CANDIDATES"
    assert len(captured)==3
    assert all(x[1]=="REUSED" for x in captured)
    assert written[-1]["status"]=="COMMITTED"
    assert written[-1]["model_timeouts_preserved"] is True
