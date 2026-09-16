#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import datetime as dt, hashlib, json
from dataclasses import asdict, dataclass
from pathlib import Path
import story_json
import runtime_workspace

DAG_REL = Path("meta/runtime-dag-state.json")

def now():
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def read_json(path):
    return story_json.read_json(path)

def write_json(path,data):
    story_json.write_json(path, data)

def evidence_hash(ep,paths):
    h=hashlib.sha256()
    for rel in paths:
        p=ep/rel; h.update(rel.encode("utf-8"))
        if p.is_file():
            h.update(b"F"); h.update(p.read_bytes())
        elif p.is_dir():
            h.update(b"D")
            for child in sorted(x for x in p.rglob("*") if x.is_file()):
                h.update(child.relative_to(ep).as_posix().encode("utf-8")); h.update(child.read_bytes())
        else:
            h.update(b"MISSING")
    return h.hexdigest()

@dataclass(frozen=True)
class StepSpec:
    step_id:str
    executor:str
    depends_on:tuple[str,...]
    covers:tuple[str,...]
    target_state:str|None
    evidence_paths:tuple[str,...]
    expensive:bool=False

@dataclass
class StepResult:
    step_id:str
    status:str
    attempt:int
    started_at:str
    finished_at:str
    elapsed_seconds:float
    input_hash:str|None=None
    output_hash:str|None=None
    note:str=""
    returncode:int=0

def load_state(ep):
    data=runtime_workspace.read_json(ep,DAG_REL,default=None)
    if not isinstance(data,dict):
        return {"schema_version":1,"note":"Runtime DAG recovery evidence only; NOT a stage source.","steps":{},"history":[]}
    data.setdefault("steps",{}); data.setdefault("history",[]); return data

def save_result(ep,result):
    data=load_state(ep); row=asdict(result)
    data["steps"][result.step_id]=row; data["history"].append(row); data["history"]=data["history"][-200:]; data["updated_at"]=now()
    runtime_workspace.write_json(ep,DAG_REL,data)

def self_test():
    x=StepSpec("A","machine",(),("RESTORE",),None,())
    assert x.step_id=="A"
    assert DAG_REL.as_posix()=="meta/runtime-dag-state.json"
    print("WORKFLOW STEP PROTOCOL SELF-TEST PASS")

if __name__=="__main__": self_test()
