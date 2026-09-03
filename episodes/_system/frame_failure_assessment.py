#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import batch_runtime_config
import frame_contract

ISSUE_WEIGHTS={
    "FRAME_CONTRACT_OBVIOUS_MISMATCH":60,
    "IDENTITY_OBVIOUS_DRIFT":55,
    "CONTINUITY_OBVIOUS_BREAK":45,
    "ANOMALY_SCALE_OBVIOUSLY_WEAK":45,
    "POV_RECORDER_OBVIOUSLY_ILLEGAL":40,
    "KEY_PROP_OBVIOUS_DRIFT":35,
    "WEATHER_OBVIOUS_MISMATCH":30,
}

def deviation_score(scout:dict)->int:
    codes={str(x) for x in (scout.get("issue_codes") or [])}
    total=sum(ISSUE_WEIGHTS.get(code,0) for code in codes)
    if scout.get("decision")=="REPAIR_NOW": total+=15
    try: confidence=float(scout.get("confidence") or 0)
    except Exception: confidence=0
    if confidence>=0.9: total+=10
    elif confidence>=0.75: total+=5
    return min(100,max(0,int(total)))

def risk_priority(ep:Path,frame:int)->int:
    c=frame_contract.compile_frame(ep,frame,write_cache=True)
    d=c["hash_material"]["frame_directive"]
    mode=str(d.get("frame_mode") or "")
    role=str(d.get("narrative_role") or "")
    impact=int(d.get("impact_level") or 0)
    base=impact*20
    mode_bonus={"climax_impact":40,"anomaly_amplified":35,"anomaly_reveal":25,"payoff":20,"normal_record":0}.get(mode,10)
    role_bonus={"climax":30,"payoff":22,"reveal":18,"escalation":15,"evidence":8,"setup":0,"transition":0,"residue":5}.get(role,0)
    return base+mode_bonus+role_bonus

def criticality_score(ep:Path,frame:int)->int:
    # Current scheduler risk_priority practical ceiling is roughly 170 including visual-lock scope bonus.
    # Batch production excludes Visual Lock, so normalize against 150 and clamp.
    return min(100,max(0,round(risk_priority(ep,frame)/150*100)))

def assess(ep:Path,frame:int,scout:dict,*,batch_complete:bool)->dict:
    dev=deviation_score(scout)
    crit=criticality_score(ep,frame)
    dev_hi,crit_hi=batch_runtime_config.repair_thresholds()
    failed=scout.get("decision")=="REPAIR_NOW"
    high_high=failed and dev>=dev_hi and crit>=crit_hi
    if not failed:
        action="KEEP_OR_DEFER_FINAL"
    elif high_high:
        action="EARLY_SINGLE_REPAIR"
    elif not batch_complete:
        action="WAIT_BATCH"
    else:
        action="SINGLE_REPAIR"
    return {
        "schema_version":1,
        "frame":f"{frame:02d}",
        "deviation_score":dev,
        "criticality_score":crit,
        "deviation_high_min":dev_hi,
        "criticality_high_min":crit_hi,
        "high_high":high_high,
        "batch_complete":bool(batch_complete),
        "action":action,
        "issue_codes":list(scout.get("issue_codes") or []),
        "scout_decision":scout.get("decision"),
    }

def self_test():
    assert deviation_score({"decision":"REPAIR_NOW","issue_codes":["IDENTITY_OBVIOUS_DRIFT"],"confidence":0.95})==80
    assert deviation_score({"decision":"REPAIR_NOW","issue_codes":["WEATHER_OBVIOUS_MISMATCH"],"confidence":0.8})==50
    print("FRAME FAILURE ASSESSMENT SELF-TEST PASS")
if __name__=="__main__": self_test()
