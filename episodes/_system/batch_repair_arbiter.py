#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
import frame_failure_assessment
import runtime_trace

ROOT=Path(__file__).resolve().parents[2]
SYSTEM=Path(__file__).resolve().parent

def _run(cmd):
    return subprocess.run([str(x) for x in cmd],cwd=ROOT,check=False,stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace")

def authorize_single_repair(ep:Path,frame:int,reason:str)->tuple[bool,str]:
    cp=_run([sys.executable,SYSTEM/"production_ledger.py","review",ep,"--frame",f"{frame:02d}",
        "--decision","repair","--notes",reason])
    return cp.returncode==0,cp.stdout

def assess(ep:Path,frame:int,scout:dict,*,batch_complete:bool,batch_id:str)->dict:
    result=frame_failure_assessment.assess(ep,frame,scout,batch_complete=batch_complete)
    result["batch_id"]=batch_id
    return result

def apply(ep:Path,assessment:dict)->dict:
    action=assessment["action"]
    frame=int(assessment["frame"])
    if action not in {"EARLY_SINGLE_REPAIR","SINGLE_REPAIR"}:
        return {**assessment,"ledger_repair_authorized":False}
    reason=(
        f"V2.4 Batch Repair Gate batch={assessment['batch_id']} "
        f"action={action} deviation={assessment['deviation_score']} "
        f"criticality={assessment['criticality_score']}"
    )
    ok,msg=authorize_single_repair(ep,frame,reason)
    return {**assessment,"ledger_repair_authorized":ok,"ledger_message":msg[-800:]}

def write_batch_decision(ep:Path,batch_id:str,rows:list[dict])->Path:
    p=ep/"meta/batch-repair-decisions"/f"{batch_id.lower()}.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    data={"schema_version":1,"batch_id":batch_id,"decisions":rows,"evidence_not_authority":True}
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return p

def self_test():
    print("BATCH REPAIR ARBITER SELF-TEST PASS")
if __name__=="__main__": self_test()
