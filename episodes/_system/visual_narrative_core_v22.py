#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
import shot_progression_gate
import capture_grammar_v228

ROOT = Path(__file__).resolve().parents[2]
REL = Path("meta/shot-progression-review.json")
CORE_ID = "VISUAL_NARRATIVE_CORE_V2.2"
FORBIDDEN_POV_TOKENS = {"omniscient","god_view","god-view","floating","director","impossible_third_person"}
RECAP_FUNCTIONS = {"recap","repeat","duplicate","same_evidence"}

def _read(path: Path) -> dict:
    data=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data,dict): raise ValueError(f"JSON root must be object: {path}")
    return data

def _sha(data: Any) -> str:
    raw=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def required(ep: Path) -> bool:
    p=Path(ep)/REL
    if not p.is_file(): return False
    try: return int(_read(p).get("schema_version") or 1) >= 2
    except Exception: return False

def _frame_row(ep: Path, frame: int) -> dict:
    data=_read(Path(ep)/REL); key=f"{frame:02d}"
    return next((r for r in data.get("frames") or [] if str(r.get("frame") or "").zfill(2)==key), {})

def _family(row: dict) -> str:
    raw=" ".join(str(row.get(k) or "").strip().lower() for k in ("camera_position","subject_distance","pov_mode","location_zone"))
    rules=[
        ("inside_vehicle",("车内","inside_vehicle","driver","passenger","dashboard")),
        ("through_glass",("隔窗","through_glass","windshield","window")),
        ("over_shoulder",("肩后","over_shoulder","over-shoulder")),
        ("doorway_edge",("门框","车门","doorway","vehicle_edge")),
        ("walking_capture",("步行","走路","walking","moving")),
        ("reaction_frame",("反应","reaction","close","medium")),
        ("object_detail",("细节","detail","hand","手部","prop")),
        ("low_light_distance",("远摄","tele","night","夜")),
        ("reflection_occlusion",("反射","reflection","occlusion","遮挡")),
        ("selfie",("selfie","自拍")),
    ]
    for fam,tokens in rules:
        if any(t in raw for t in tokens): return fam
    return "other:"+str(row.get("camera_position") or "unknown").strip().lower().replace(" ","_")

def _owner_class(row: dict) -> str:
    pov=str(row.get("pov_mode") or "").strip().lower()
    itype=str(((row.get("interaction") or {}).get("type")) or "").strip().lower()
    if "selfie" in pov or itype=="group_selfie": return "selfie_operator"
    if any(x in pov for x in ("companion","secondary","同行","同伴")): return "secondary_or_companion_photographer"
    if any(x in pov for x in ("first","pov","primary","第一","主摄影")): return "primary_photographer"
    if any(x in pov for x in FORBIDDEN_POV_TOKENS): return "FORBIDDEN_CAMERA_LOGIC"
    return "diegetic_operator_must_be_resolved"

def resolve_frame(ep: Path, frame: int|str) -> dict:
    ep=Path(ep).resolve(); n=int(frame); key=f"{n:02d}"
    row=_frame_row(ep,n)
    capture=capture_grammar_v228.compile_capture_contract(ep)
    contract={
        "core_id":CORE_ID,"frame":key,
        "camera_authorship":{
            "owner_class":_owner_class(row),
            "pov_mode":row.get("pov_mode"),
            "camera_position":row.get("camera_position"),
            "ghost_camera_forbidden":True,
            "camera_owner_must_be_physically_explainable":True,
        },
        "moment":{
            "action_in_progress":str(row.get("action") or "").strip(),
            "save_reason":str(row.get("capture_purpose") or "").strip(),
            "must_not_be_result_only_showcase":True,
        },
        "shot_grammar":{
            "family":_family(row),
            "subject_distance":row.get("subject_distance"),
            "location_zone":row.get("location_zone"),
            "first_person_is_logic_not_fixed_composition":True,
            "repeated_hand_phone_distant_anomaly_template_forbidden":True,
        },
        "narrative_evidence":{
            "new_information":row.get("new_information"),
            "new_information_this_frame":str(row.get("visual_function") or "").strip(),
            "anomaly_logic_stage":row.get("anomaly_logic_stage"),
            "human_action_stage":row.get("human_action_stage"),
            "narrative_redundancy_forbidden":True,
            "continuity_exception_reason":str(row.get("continuity_exception_reason") or "").strip(),
        },
        "human_response":{
            "human_present":row.get("human_present"),
            "emotion":row.get("emotion") or {},
            "interaction":row.get("interaction") or {},
        },
        "camera_roster_policy":capture.get("camera_roster") or {},
        "camera_defect_physics":capture.get("camera_defect_physics") or {},
        "visual_memory_continuity":capture.get("visual_memory_continuity") or {},
        "screen_content_physics":capture.get("screen_content_physics") or {},
        "review_questions":[
            "Who took this frame and where is the photographer physically standing?",
            "Why is the camera in that person's hands now?",
            "What action is happening right now?",
            "Why would this exact frame be kept?",
            "What NEW story/evidence information does this add versus the previous frame?",
            "Is it only the same anomaly from another angle?",
            "If blur/noise/reflection/underexposure exists, what physical cause produced it?",
            "If a screen/UI is visible, is it physically and narratively coherent?"
        ],
    }
    return {"frame":key,"visual_narrative":contract,"visual_narrative_sha256":_sha(contract)}

def verify_frame(ep: Path, frame: int|str) -> list[str]:
    ep=Path(ep).resolve()
    if not required(ep): return []
    n=int(frame); row=_frame_row(ep,n); e=[]
    if not row: return [f"VISUAL_NARRATIVE_MISSING:{n:02d}"]
    for k in ("camera_position","pov_mode","action","capture_purpose","visual_function"):
        if not str(row.get(k) or "").strip(): e.append(f"VISUAL_NARRATIVE_FIELD_MISSING:{n:02d}:{k}")
    pov=str(row.get("pov_mode") or "").lower()
    if any(t in pov for t in FORBIDDEN_POV_TOKENS): e.append(f"CAMERA_LOGIC_INVALID:{n:02d}:{pov}")
    exception=str(row.get("continuity_exception_reason") or "").strip()
    if n>1 and row.get("new_information") is not True and not exception:
        e.append(f"NARRATIVE_REDUNDANCY:{n:02d}:new_information must be true or explain deliberate repetition")
    vf=str(row.get("visual_function") or "").strip().lower()
    if n>1 and vf in RECAP_FUNCTIONS and not exception:
        e.append(f"NARRATIVE_EVIDENCE_REPEAT:{n:02d}:{vf}")
    return e

def verify_all(ep: Path) -> list[str]:
    ep=Path(ep).resolve()
    if not required(ep): return []
    e=list(shot_progression_gate.validate(ep,require_locked=True))
    data=_read(ep/REL)
    rows=sorted([r for r in data.get("frames") or [] if isinstance(r,dict)],key=lambda r:int(r.get("frame") or 0))
    fam=[]
    for r in rows:
        n=int(r.get("frame") or 0)
        if n:
            e.extend(verify_frame(ep,n)); fam.append((n,_family(r)))
    if len(fam)>=5:
        w=10 if len(fam)>=10 else len(fam)
        for i in range(len(fam)-w+1):
            win=fam[i:i+w]
            if len({x[1] for x in win})<3:
                e.append(f"SHOT_GRAMMAR_DIVERSITY_FAIL:{win[0][0]:02d}-{win[-1][0]:02d}")
                break
    return e

def self_test():
    s={"camera_position":"inside_vehicle","subject_distance":"medium","pov_mode":"first_person","location_zone":"road","interaction":{"type":"none"}}
    assert _family(s)=="inside_vehicle"
    assert _owner_class(s)=="primary_photographer"
    assert _owner_class({**s,"pov_mode":"omniscient"})=="FORBIDDEN_CAMERA_LOGIC"
    print("VISUAL NARRATIVE CORE V2.2 SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("verify"); p.add_argument("episode_dir"); p.add_argument("--frame",type=int)
    p=sub.add_parser("show"); p.add_argument("episode_dir"); p.add_argument("--frame",type=int,required=True)
    sub.add_parser("self-test")
    a=ap.parse_args()
    if a.cmd=="self-test": self_test(); return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="show":
        print(json.dumps(resolve_frame(ep,a.frame),ensure_ascii=False,indent=2)); return 0
    e=verify_frame(ep,a.frame) if a.frame else verify_all(ep)
    if e:
        [print("FAIL:",x) for x in e]; return 2
    print("VISUAL NARRATIVE CORE VERIFIED"); return 0

if __name__=="__main__":
    raise SystemExit(main())
