#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build/verify ChatGPT -> GitHub -> Codex preproduction handoff."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import character_contract, environment_contract, frame_contract, resource_library, runtime_execution
import directing_quality

ROOT=Path(__file__).resolve().parents[2]
REL=Path("meta/preproduction-handoff.json")

def read_json(p):
    d=json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict):raise ValueError(f"JSON root must be object: {p}")
    return d
def write_json(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def stage(ep):
    p=ep/"meta/episode-state.json";return (read_json(p).get("current_state") if p.is_file() else None)
def authority_files(ep):
    rows=[]
    # Only hash assets that should stay immutable after the handoff.
    for rel in ("meta/runtime-request.json","meta/character-contract.json","meta/resource-selection.json","meta/intro-policy.json","meta/directing-quality.json","meta/voice-contract.json","meta/storyboard-density-review.json","meta/opening-social-anchor.json","meta/capture-event-contract.json","meta/world-state.json"):
        p=ep/rel
        if p.is_file():rows.append(p)
    story=ep/"story"
    if story.is_dir():
        for p in sorted(story.rglob("*")):
            if p.is_file() and p.suffix.lower() in {".md",".json",".txt"}:
                rows.append(p)
    seen=set();out=[]
    for p in rows:
        rp=p.resolve()
        if rp not in seen:seen.add(rp);out.append(p)
    return out
def stable_story_gate_subset(ep):
    p=ep/"meta/story-gates.json"
    if not p.is_file():return {}
    g=read_json(p);v=g.get("visual") or {}
    return {
        "story":g.get("story") or {},
        "visual":{
            "environment_contract":v.get("environment_contract") or {},
            "frame_directives":v.get("frame_directives") or {},
            "calibration":v.get("calibration") or {}
        }
    }
def json_sha(data):
    raw=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
def build(ep,source_runtime="chatgpt"):
    ep=Path(ep).resolve()
    if stage(ep)!="STORYBOARD_LOCKED":raise ValueError("handoff requires current_state=STORYBOARD_LOCKED")
    ce=character_contract.validate(ep,require_locked=True)
    if ce:raise ValueError("character contract invalid: "+"; ".join(ce))
    env=environment_contract.verify(ep)
    if env:raise ValueError("environment contract invalid: "+"; ".join(env[:8]))
    fc=frame_contract.verify_all(ep)
    if fc:raise ValueError("frame contract invalid: "+"; ".join(fc[:8]))
    if directing_quality.enabled(ep):
        qerrors=directing_quality.verify_story(ep)+directing_quality.verify_preimage(ep)
        if qerrors:raise ValueError("directing quality invalid: "+"; ".join(qerrors[:12]))
    resource_library.resolve(ep,True)
    files=authority_files(ep)
    assets=[{"kind":"file","path":p.relative_to(ep).as_posix(),"sha256":sha(p),"bytes":p.stat().st_size} for p in files]
    subsets=[{"kind":"json_subset","path":"meta/story-gates.json","name":"stable_preproduction_subset","sha256":json_sha(stable_story_gate_subset(ep))}]
    q_enabled=directing_quality.enabled(ep)
    data={"schema_version":2 if q_enabled else 1,"handoff_type":"preproduction_to_image","source_runtime":source_runtime,"created_at_stage":"STORYBOARD_LOCKED","authority_assets":assets,"authority_subsets":subsets,"derived_rebuildable":["meta/runtime/execution-capsules","meta/runtime/contracts","meta/runtime/prompt-packages"],"quality_contracts_enabled":q_enabled,"story_rewrite_allowed":False,"next_mode":"image_continue","handoff_ready":True}
    material=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    data["manifest_sha256"]=hashlib.sha256(material).hexdigest()
    write_json(ep/REL,data);return data
def verify(ep):
    ep=Path(ep).resolve();p=ep/REL
    if not p.is_file():return ["HANDOFF_MISSING"]
    d=read_json(p);errors=[]
    if d.get("handoff_ready") is not True:errors.append("HANDOFF_NOT_READY")
    if d.get("story_rewrite_allowed") is not False:errors.append("HANDOFF_STORY_REWRITE_POLICY_INVALID")
    order=("IDEA_LOCKED","STORYBOARD_LOCKED","VISUAL_CALIBRATED","PRODUCTION_PASSED","PUBLISH_READY","PUBLISHED","DATA_REVIEWED")
    cur=stage(ep)
    if cur not in order or order.index(cur)<order.index("STORYBOARD_LOCKED"):errors.append("HANDOFF_STAGE_MISMATCH")
    for row in d.get("authority_assets") or []:
        f=ep/row["path"]
        if not f.is_file():errors.append("HANDOFF_FILE_MISSING:"+row["path"]);continue
        if sha(f)!=row.get("sha256"):errors.append("HANDOFF_SHA_MISMATCH:"+row["path"])
    for row in d.get("authority_subsets") or []:
        if row.get("name")=="stable_preproduction_subset" and json_sha(stable_story_gate_subset(ep))!=row.get("sha256"):
            errors.append("HANDOFF_SHA_MISMATCH:meta/story-gates.json#stable_preproduction_subset")
    ce=character_contract.validate(ep,require_locked=True)
    if ce:errors.extend("HANDOFF_CHARACTER:"+x for x in ce)
    if int(d.get("schema_version") or 1)>=2 and d.get("quality_contracts_enabled") is True:
        errors.extend("HANDOFF_QUALITY:"+x for x in (directing_quality.verify_story(ep)+directing_quality.verify_preimage(ep)))
    return errors

def activate(ep):
    errors=verify(ep)
    if errors:raise ValueError("; ".join(errors))
    return runtime_execution.set_mode(ep,"image_continue","verified_preproduction_handoff")
def self_test():
    assert REL.as_posix()=="meta/preproduction-handoff.json"
    print("PREPRODUCTION HANDOFF SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("build");p.add_argument("episode_dir");p.add_argument("--source-runtime",default="chatgpt")
    p=sub.add_parser("verify");p.add_argument("episode_dir")
    p=sub.add_parser("show");p.add_argument("episode_dir")
    p=sub.add_parser("activate");p.add_argument("episode_dir")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="build":print(json.dumps(build(ep,a.source_runtime),ensure_ascii=False,indent=2));return 0
    if a.cmd=="verify":
        errors=verify(ep)
        if errors:[print(x) for x in errors];return 3
        print("PREPRODUCTION HANDOFF VERIFIED");return 0
    if a.cmd=="activate":
        print(json.dumps(activate(ep),ensure_ascii=False,indent=2));return 0
    p=ep/REL;print(p.read_text(encoding="utf-8-sig") if p.is_file() else "{}");return 0
if __name__=="__main__":raise SystemExit(main())
