#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, uuid
from pathlib import Path
import batch_runtime_config
import frame_contract

def _sha(data:dict)->str:
    raw=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def _directive(ep:Path,frame:int)->dict:
    return frame_contract.compile_frame(ep,frame,write_cache=True)["hash_material"].get("frame_directive") or {}

def _continuity_key(ep:Path,item:dict)->tuple:
    d=_directive(ep,int(item["frame"]))
    # Unknown/missing fields deliberately collapse to empty strings. Contiguous frame ordering
    # remains the primary grouping rule; these fields only prevent obvious cross-state grouping.
    return (
        str(d.get("location_id") or d.get("location") or ""),
        str(d.get("time_segment") or d.get("time_of_day") or ""),
        str(d.get("environment_segment") or ""),
        str(d.get("world_state") or ""),
    )

def _compatible(ep:Path,left:dict,right:dict)->bool:
    a=_continuity_key(ep,left); b=_continuity_key(ep,right)
    for x,y in zip(a,b):
        if x and y and x!=y: return False
    # Preserve explicit hard pixel prerequisites.
    right_deps={int(x) for x in right.get("depends_on") or []}
    if int(left["frame"]) in right_deps: return False
    return True

def build(ep:Path,items:list[dict],*,size:int|None=None)->dict:
    if not items: raise ValueError("batch cannot be empty")
    limit=int(size or batch_runtime_config.images_per_batch())
    ordered=sorted(items,key=lambda x:int(x["frame"]))
    selected=[ordered[0]]
    for item in ordered[1:]:
        if len(selected)>=limit: break
        if int(item["frame"])!=int(selected[-1]["frame"])+1: break
        if not _compatible(ep,selected[-1],item): break
        selected.append(item)
    rows=[]
    for idx,item in enumerate(selected,1):
        prov=frame_contract.provenance(ep,int(item["frame"]))
        if not prov: raise ValueError(f"frame {int(item['frame']):02d} missing frame contract provenance")
        rows.append({
            "output_index":idx,
            "frame":f"{int(item['frame']):02d}",
            "queue_item_id":item["id"],
            "frame_contract_sha256":prov["contract_sha256"],
        })
    material={
        "schema_version":1,
        "derived_execution_envelope":True,
        "authority":False,
        "planned_count":len(rows),
        "frames":rows,
    }
    material["batch_contract_sha256"]=_sha(material)
    material["batch_id"]="BATCH_"+uuid.uuid4().hex[:12]
    return material

def plan(ep:Path,ready:list[dict])->list[dict]:
    remaining=sorted([x for x in ready if str(x.get("scope") or "")=="batch"],key=lambda x:int(x["frame"]))
    out=[]
    while remaining:
        contract=build(ep,remaining)
        ids={x["queue_item_id"] for x in contract["frames"]}
        out.append(contract)
        remaining=[x for x in remaining if x["id"] not in ids]
    return out

def self_test():
    assert batch_runtime_config.images_per_batch()==5
    print("BATCH CONTRACT SELF-TEST PASS")
if __name__=="__main__": self_test()
