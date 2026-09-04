#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.5 Propagation Core / SHAREABILITY LOCK."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from story_os_contract import story_os_version

REVIEW_REL=Path("meta/story-semantic-review.json")
FORMAL_MIN_VERSION=(2,5,0)
LATENCIES={"immediate","short","delayed_but_direct"}
VISUAL_CAUSALITY={"strong","medium","weak"}
SEND_IMPULSE={"strong","medium","weak"}

def read_json(path):
    d=json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict): raise ValueError(f"JSON root must be object: {path}")
    return d

def version_tuple(raw):
    try:return tuple(int(x) for x in str(raw or "").split("."))
    except Exception:return (0,)

def episode_version(ep):
    ep=Path(ep);versions=[]
    for rel in ("meta/episode-state.json","meta/release-manifest.json","meta/story-gates.json"):
        p=ep/rel
        if not p.is_file():continue
        try:
            raw=str(read_json(p).get("tool_version") or "");vt=version_tuple(raw)
            if vt!=(0,):versions.append((vt,raw))
        except Exception:pass
    return max(versions,key=lambda x:x[0])[1] if versions else story_os_version()

def required(ep):return version_tuple(episode_version(ep))>=FORMAL_MIN_VERSION

def frame_count(ep):
    p=Path(ep)/"meta/release-manifest.json"
    if not p.is_file():return 0
    try:return int(((read_json(p).get("release") or {}).get("body_frame_count")) or 0)
    except Exception:return 0

def text(v):return str(v or "").strip()

def validate_payload(core,total_frames):
    e=[]
    if not isinstance(core,dict):
        return ["PROPAGATION_CORE_MISSING:story-semantic-review.propagation_core must be object"]
    for key in ("retell_sentence","protagonist_action","abnormal_response","consequence"):
        if not text(core.get(key)):e.append(f"PROPAGATION_CORE_MISSING:{key}")
    sentence=text(core.get("retell_sentence"))
    if len(sentence)>120:e.append("RETELLABILITY_FAILED:retell_sentence exceeds 120 characters")
    if core.get("retellable_in_10s") is not True:e.append("RETELLABILITY_FAILED:retellable_in_10s must be true")
    latency=text(core.get("response_latency"))
    if latency not in LATENCIES:e.append(f"ACTION_RESPONSE_CHAIN_WEAK:invalid response_latency={latency!r}")
    vc=text(core.get("visual_causality"))
    if vc not in VISUAL_CAUSALITY:e.append(f"VISUAL_CAUSALITY_WEAK:invalid visual_causality={vc!r}")
    elif vc=="weak":e.append("VISUAL_CAUSALITY_WEAK:visual_causality cannot be weak")
    impulse=text(core.get("social_send_impulse"))
    if impulse not in SEND_IMPULSE:e.append(f"ACTION_RESPONSE_CHAIN_WEAK:invalid social_send_impulse={impulse!r}")
    elif impulse=="weak":e.append("ACTION_RESPONSE_CHAIN_WEAK:social_send_impulse cannot be weak")
    nums={}
    for key in ("trigger_frame","response_frame","payoff_frame"):
        v=core.get(key)
        if isinstance(v,bool) or not isinstance(v,int):e.append(f"ACTION_RESPONSE_ORDER_BROKEN:{key} must be integer")
        else:nums[key]=v
    if total_frames<=0:e.append("ACTION_RESPONSE_ORDER_BROKEN:total frame count unresolved")
    elif len(nums)==3:
        t,r,p=nums["trigger_frame"],nums["response_frame"],nums["payoff_frame"]
        if not (1<=t<=r<=p<=total_frames):
            e.append(f"ACTION_RESPONSE_ORDER_BROKEN:expected 1 <= trigger({t}) <= response({r}) <= payoff({p}) <= total({total_frames})")
        if t/total_frames>0.5 and not text(core.get("late_trigger_exception_reason")):
            e.append(f"TRIGGER_TOO_LATE_WITHOUT_REASON:trigger={t}/{total_frames} is later than 50% of sequence")
    guard=core.get("surface_copy_guard")
    if not isinstance(guard,dict):e.append("SURFACE_COPY_GUARD_FAILED:surface_copy_guard must be object")
    else:
        if guard.get("structural_reference_only") is not True:e.append("SURFACE_COPY_GUARD_FAILED:structural_reference_only must be true")
        copied=guard.get("copied_surface_elements")
        if not isinstance(copied,list):e.append("SURFACE_COPY_GUARD_FAILED:copied_surface_elements must be list")
        elif [x for x in copied if text(x)]:e.append("SURFACE_COPY_GUARD_FAILED:copied_surface_elements must be empty for PASS")
    return e

def verify(ep,force=False):
    ep=Path(ep).resolve()
    if not force and not required(ep):return []
    p=ep/REVIEW_REL
    if not p.is_file():return ["PROPAGATION_CORE_MISSING:meta/story-semantic-review.json missing"]
    try:d=read_json(p)
    except Exception as exc:return [f"PROPAGATION_CORE_MISSING:{exc}"]
    return validate_payload(d.get("propagation_core"),frame_count(ep))

def self_test():
    good={"retell_sentence":"普通人做了一个动作，对面的异常立刻回应，并留下可见后果。",
          "protagonist_action":"按了一次开关","abnormal_response":"走廊尽头的灯反向逐盏亮起",
          "consequence":"原本关闭的门自己打开","response_latency":"immediate",
          "visual_causality":"strong","retellable_in_10s":True,"social_send_impulse":"strong",
          "trigger_frame":8,"response_frame":9,"payoff_frame":12,"late_trigger_exception_reason":"",
          "surface_copy_guard":{"structural_reference_only":True,"copied_surface_elements":[]}}
    assert validate_payload(good,20)==[]
    late=dict(good);late["trigger_frame"]=13;late["response_frame"]=14;late["payoff_frame"]=15
    assert any(x.startswith("TRIGGER_TOO_LATE") for x in validate_payload(late,20))
    print("PROPAGATION CORE V2.5 SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("verify");p.add_argument("episode_dir");p.add_argument("--force",action="store_true")
    p=sub.add_parser("show");p.add_argument("episode_dir")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="show":
        p=ep/REVIEW_REL
        print(json.dumps((read_json(p).get("propagation_core") or {}) if p.is_file() else {},ensure_ascii=False,indent=2));return 0
    errs=verify(ep,a.force)
    if errs:
        [print("FAIL:",x) for x in errs];return 2
    print("PROPAGATION CORE VERIFIED" if a.force or required(ep) else f"PROPAGATION CORE NOT REQUIRED | episode_version={episode_version(ep)}")
    return 0
if __name__=="__main__":raise SystemExit(main())
