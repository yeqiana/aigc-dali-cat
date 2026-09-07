"""Shared scheduling and repair risk weights."""
from pathlib import Path
import frame_contract

def risk_priority(ep:Path,frame:int,scope:str="batch")->int:
    c=frame_contract.compile_frame(ep,frame,write_cache=True)
    d=c["hash_material"]["frame_directive"]
    mode=str(d.get("frame_mode") or "")
    role=str(d.get("narrative_role") or "")
    impact=int(d.get("impact_level") or 0)
    base=impact*20
    mode_bonus={"climax_impact":40,"anomaly_amplified":35,"anomaly_reveal":25,"payoff":20,"normal_record":0}.get(mode,10)
    role_bonus={"climax":30,"payoff":22,"reveal":18,"escalation":15,"evidence":8,"setup":0,"transition":0,"residue":5}.get(role,0)
    return base+mode_bonus+role_bonus+(50 if scope=="visual_lock" else 0)

def criticality_score(ep:Path,frame:int)->int:
    # Preserve the production scale: 150 points maps to 100; stronger frames clamp.
    return min(100,max(0,round(risk_priority(ep,frame)/150*100)))

