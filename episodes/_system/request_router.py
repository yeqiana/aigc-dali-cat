#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, uuid
from pathlib import Path
import request_intent, storyos_config

ROOT=Path(__file__).resolve().parents[2]
_CONFIG=storyos_config.load_config()
def now():return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def _cfg():
    rel=storyos_config.get_path(_CONFIG,"agent_runtime.router.config")
    d=json.loads((ROOT/str(rel)).read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict):raise ValueError("router config root must be object")
    return d
def _state(ep):
    p=ep/"meta/episode-state.json"
    if not p.is_file():return None
    d=json.loads(p.read_text(encoding="utf-8-sig"));return d.get("current_state") if isinstance(d,dict) else None
def _sha(req):return hashlib.sha256(json.dumps(req,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def decide(ep,request):
    cfg=_cfg();mode=str(request.get("mode") or "");routes=cfg.get("routes") or {}
    if mode not in routes:raise ValueError(f"ROUTE_UNSUPPORTED_MODE: {mode}")
    spec=dict(routes[mode]);intent=(request.get("intent") or {}).get("intent");expected=request_intent.expected_intent_for_mode(mode)
    if intent and intent!=expected:raise ValueError(f"INTENT_ROUTE_MISMATCH: intent={intent} mode={mode} expected={expected}")
    rewrite=bool(((request.get("user_intent") or {}).get("allow_story_rewrite")))
    preserve=[];invalidate=[]
    if mode=="image_continue":preserve=["story","storyboard","character_contract","preproduction_handoff_authority"]
    elif mode=="repair_only":preserve=["all_clean_frames","story","storyboard","locked_assets"];invalidate=["explicit_dirty_set_only"]
    elif mode=="release_only":preserve=["production_passed_assets","frame_reviews","approved_media"]
    elif mode=="resume":preserve=["all_sha_valid_evidence"]
    return {"schema_version":1,"route_id":"RT_"+uuid.uuid4().hex[:16],"created_at":now(),
        "source":cfg.get("source") or "deterministic_rules","route_is_stage_authority":False,
        "request_id":request.get("request_id"),"request_sha256":_sha(request),"episode_state_at_decision":_state(ep),
        "intent":expected,"workflow_mode":mode,"entry_step":spec.get("entry_step"),"target":spec.get("target"),
        "allow_image_generation":bool(spec.get("allow_image_generation")),"allow_story_rewrite":rewrite,
        "preserve":preserve,"invalidate":invalidate,
        "reason_codes":[f"MODE_{mode.upper()}",f"INTENT_{expected}","DETERMINISTIC_ROUTE"]}
def write_decision(ep,decision):
    p=ep/str(_cfg().get("decision_path") or "meta/runtime-route.json");p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(decision,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return p
def route_episode(ep,request,*,write=True):
    d=decide(ep,request)
    if write:write_decision(ep,d)
    return d
def self_test():
    c=_cfg();assert c["route_is_stage_authority"] is False
    assert c["routes"]["image_continue"]["entry_step"]=="VISUAL_LOCK"
    assert c["routes"]["preproduction_only"]["allow_image_generation"] is False
    print("REQUEST ROUTER SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("preview");p.add_argument("episode_dir",type=Path);p.add_argument("--request",type=Path,required=True)
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    req=json.loads(a.request.read_text(encoding="utf-8-sig"));print(json.dumps(decide(a.episode_dir.resolve(),req),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
