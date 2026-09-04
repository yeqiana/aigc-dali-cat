#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.6.0 Performance Runtime Fast Path entrypoint."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import episode_performance, execution_capsule, raw_candidate_budget, runtime_capability_cache, runtime_resume_capsule
ROOT=Path(__file__).resolve().parents[2]
def slo(ep):
    ep=Path(ep).resolve();p=ep/"meta/episode-performance-ledger.json"
    if not p.is_file():return {"health":"UNKNOWN","active_wall_seconds":None,"gate":False}
    d=json.loads(p.read_text(encoding="utf-8-sig"));active=((d.get("run_wall") or {}).get("active_wall_seconds"));active=active if isinstance(active,(int,float)) else d.get("total_wall_seconds")
    if not isinstance(active,(int,float)):return {"health":"UNKNOWN","active_wall_seconds":None,"gate":False}
    health="GREEN" if active<=5400 else ("YELLOW" if active<=7200 else "RED")
    return {"health":health,"active_wall_seconds":round(float(active),3),"green_max_seconds":5400,"yellow_max_seconds":7200,"gate":False}
def prepare(ep):
    ep=Path(ep).resolve();rid=episode_performance.safe_begin_named_span(ep,"CONTEXT_RECOVERY",source="runtime_fast_path_v251")
    caps=runtime_capability_cache.ensure(ep);resume=runtime_resume_capsule.compile_capsule(ep,True);step=resume.get("runtime_step")
    capsule=None
    if step:
        try:capsule=execution_capsule.compile_capsule(ep,step,write=True)
        except Exception:capsule=None
    state={"schema_version":1,"module_version":"2.6.0","resume_capsule":(ep/runtime_resume_capsule.REL).relative_to(ep).as_posix(),"runtime_step":step,"capability_cache_fresh":runtime_capability_cache.is_fresh(caps),"execution_capsule_compiled":bool(capsule),"performance_slo":slo(ep),"fast_path_policy":"resume capsule first; no broad rescan while source SHA is unchanged"}
    out=ep/"meta/runtime/fast-path-state.json";out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    episode_performance.safe_end_named_span(ep,"CONTEXT_RECOVERY",status="PASS",metadata={"fast_path":"2.6.0"})
    return {"state":state,"resume":resume,"capabilities":caps}
def self_test():
    assert slo(Path("/nonexistent"))["health"]=="UNKNOWN";print("RUNTIME FAST PATH V2.6.0 SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    for name in ("prepare","resume","slo"):
        p=sub.add_parser(name);p.add_argument("episode_dir")
    p=sub.add_parser("capabilities");p.add_argument("episode_dir");p.add_argument("--vision",choices=sorted(runtime_capability_cache.VALID_VISION));p.add_argument("--image-route");p.add_argument("--text-worker");p.add_argument("--sandbox-risk");p.add_argument("--note")
    p=sub.add_parser("candidate");p.add_argument("episode_dir");p.add_argument("--frame",required=True,type=int);p.add_argument("--kind",required=True,choices=sorted(raw_candidate_budget.KINDS));p.add_argument("--reason",default="")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    if a.cmd in {"prepare","resume"}:
        d=prepare(a.episode_dir)
        if a.cmd=="resume":print(json.dumps(d["resume"],ensure_ascii=False,indent=2))
        else:print(json.dumps(d["state"],ensure_ascii=False,indent=2))
        return 0
    if a.cmd=="slo":print(json.dumps(slo(a.episode_dir),ensure_ascii=False,indent=2));return 0
    if a.cmd=="capabilities":
        if any([a.vision,a.image_route,a.text_worker,a.sandbox_risk,a.note]):d=runtime_capability_cache.record(a.episode_dir,vision=a.vision,image_route=a.image_route,text_worker=a.text_worker,sandbox_risk=a.sandbox_risk,note=a.note)
        else:d=runtime_capability_cache.ensure(a.episode_dir)
        print(json.dumps(d,ensure_ascii=False,indent=2));return 0
    ok,row=raw_candidate_budget.claim(a.episode_dir,a.frame,a.kind,a.reason);print(json.dumps(row,ensure_ascii=False,indent=2));return 0 if ok else 2
if __name__=="__main__":raise SystemExit(main())

# STORY_OS_V2_6_0_PERFORMANCE_RUNTIME
