#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, json, subprocess, sys, time
from pathlib import Path

SYSTEM = Path(__file__).resolve().parent
ROOT = SYSTEM.parents[1]
sys.path.insert(0, str(SYSTEM))

import validation_stage_v223
import visual_profile_bridge_v224 as visual_bridge
import codex_subscription_image
from canvas_normalize import normalize

VERSION="2.2.4"
NON_AUTHORITY="NON_AUTHORITY_TEST_ONLY"

def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read_json(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def write_json(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def episode(raw):
    ep=Path(raw).resolve()
    if not ep.is_dir(): raise SystemExit(f"episode directory not found: {ep}")
    try: ep.relative_to(ROOT.resolve())
    except ValueError: raise SystemExit("episode must be inside current repository")
    return ep

def blueprint(ep):
    c=sorted((ep/"meta").glob("*blueprint*.json"))
    return (c[0],read_json(c[0])) if c else (None,None)

def profile_drift(ep):
    bp_p,bp=blueprint(ep)
    meta_p=ep/"meta"/"visual-profile.json"
    if not meta_p.is_file(): meta_p=ep/"meta"/"visual_profile.json"
    meta=read_json(meta_p) if meta_p.is_file() else {}
    bp_v=(bp or {}).get("visual_profile")
    bp_id=bp_v.get("profile_id") if isinstance(bp_v,dict) else bp_v
    meta_id=meta.get("profile_id")
    resolved=visual_bridge.resolve_profile(ep).get("profile_id")
    ids=[x for x in [bp_id,meta_id,resolved] if x]
    return {
        "mismatch": len(set(ids))>1,
        "blueprint_profile_id": bp_id,
        "episode_meta_profile_id": meta_id,
        "resolved_profile_id": resolved
    }

def need_bootstrap(ep):
    r=validation_stage_v223.validate_bootstrap(ep)
    if r["status"]!="BOOTSTRAP_VALIDATE_PASS":
        raise SystemExit("BOOTSTRAP_VALIDATE_REQUIRED: "+r["status"])

def need_preproduction(ep):
    r=validation_stage_v223.validate_preproduction(ep)
    if r["status"]!="PREPRODUCTION_VALIDATE_PASS":
        raise SystemExit("PREPRODUCTION_VALIDATE_REQUIRED: "+r["status"])

def canvas(ep):
    _,bp=blueprint(ep)
    r=str((((bp or {}).get("episode") or {}).get("aspect_ratio") or "4:5")).strip()
    return {"9:16":(1080,1920),"1:1":(1080,1080)}.get(r,(1080,1350))

def check_drift(ep):
    d=profile_drift(ep)
    if d["mismatch"]:
        raise SystemExit(
            "VISUAL_PROFILE_BLUEPRINT_DRIFT: "
            f"blueprint={d['blueprint_profile_id']} meta={d['episode_meta_profile_id']} "
            f"resolved={d['resolved_profile_id']}. "
            "Run scripts/story_visual_authority.py sync-blueprint <episode>."
        )
    return d

def visual(args):
    ep=episode(args.episode_dir); need_bootstrap(ep); check_drift(ep)
    scene=args.scene or Path(args.scene_file).read_text(encoding="utf-8").strip()
    if not scene.strip(): raise SystemExit("visual test scene is empty")
    vc=visual_bridge.compile_prompt_contract(ep); w,h=canvas(ep)
    plan={
        "version":VERSION,"test_type":"VISUAL_TEST","authority":NON_AUTHORITY,
        "promotion_allowed":False,"requires":"BOOTSTRAP_VALIDATE_PASS",
        "requires_preproduction":False,"scene":scene,
        "visual_profile":{"profile_id":vc["profile_id"],"profile_path":vc["profile_path"],
                          "profile_sha256":vc["profile_sha256"],"authority_source":vc.get("authority_source")},
        "target_size":[w,h],"created_at":now()
    }
    plan_p=ep/"meta"/"tests"/"visual-test-plan.json"; write_json(plan_p,plan)
    if args.plan_only:
        print(json.dumps({**plan,"status":"VISUAL_TEST_PLAN_READY"},ensure_ascii=False,indent=2)); return 0

    stamp=dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    prompt=ep/"meta"/"tests"/f"visual-test-{stamp}.txt"
    prompt.parent.mkdir(parents=True,exist_ok=True); prompt.write_text(scene+"\n",encoding="utf-8")
    raw=ep/"media"/"tests"/"visual"/"raw"/f"visual-test-{stamp}.png"
    out=ep/"media"/"tests"/"visual"/f"visual-test-{stamp}.png"
    log=ep/"meta"/"tests"/"logs"/f"visual-test-{stamp}.jsonl"
    started=time.monotonic()
    backend=codex_subscription_image.invoke_codex(
        prompt,[],raw,log,codex_subscription_image.provider_size(w,h),
        args.timeout,args.codex,vc["text"],None,args.image_model,"high",args.strict_model
    )
    normalize(raw,out,w,h)
    report={**plan,"status":"VISUAL_TEST_GENERATED_PENDING_REVIEW",
            "output":str(out.relative_to(ep)),"log":str(log.relative_to(ep)),
            "backend_elapsed_seconds":backend,
            "total_elapsed_seconds":round(time.monotonic()-started,2),
            "review_required":True}
    write_json(ep/"meta"/"tests"/"visual-test-report.json",report)
    print(json.dumps(report,ensure_ascii=False,indent=2)); return 0

def production_smoke(args):
    ep=episode(args.episode_dir); need_preproduction(ep); check_drift(ep)
    prompt=Path(args.prompt_file).resolve()
    if not prompt.is_file(): raise SystemExit(f"prompt missing: {prompt}")
    stamp=dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out=ep/"media"/"tests"/"production-smoke"/f"frame-{int(args.frame):02d}-{stamp}.png"
    log=ep/"meta"/"tests"/"logs"/f"production-smoke-{int(args.frame):02d}-{stamp}.jsonl"
    cmd=[sys.executable,str(SYSTEM/"codex_subscription_image.py"),"generate-for-frame",str(ep),
         "--frame",str(int(args.frame)),"--prompt-file",str(prompt),"--output",str(out),
         "--log",str(log),"--timeout",str(args.timeout),"--image-model",args.image_model]
    if args.codex: cmd += ["--codex",args.codex]
    started=time.monotonic()
    r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,encoding="utf-8",errors="replace")
    status="PRODUCTION_SMOKE_TEST_GENERATED_PENDING_REVIEW" if r.returncode==0 else "PRODUCTION_SMOKE_TEST_FAILED"
    report={"version":VERSION,"test_type":"PRODUCTION_SMOKE_TEST","authority":NON_AUTHORITY,
            "promotion_allowed":False,"requires":"PREPRODUCTION_VALIDATE_PASS","status":status,
            "frame":f"{int(args.frame):02d}","output":str(out.relative_to(ep)),
            "log":str(log.relative_to(ep)),"returncode":r.returncode,
            "stdout_tail":r.stdout[-6000:],"total_elapsed_seconds":round(time.monotonic()-started,2)}
    write_json(ep/"meta"/"tests"/"production-smoke-report.json",report)
    print(json.dumps(report,ensure_ascii=False,indent=2)); return 0 if r.returncode==0 else 2

def check(args):
    ep=episode(args.episode_dir)
    b=validation_stage_v223.validate_bootstrap(ep)
    p=validation_stage_v223.validate_preproduction(ep)
    d=profile_drift(ep)
    result={"bootstrap":b["status"],"preproduction":p["status"],"profile_drift":d,
            "resolved_visual_profile":visual_bridge.resolve_profile(ep),
            "visual_test_ready":b["status"]=="BOOTSTRAP_VALIDATE_PASS" and not d["mismatch"],
            "production_smoke_ready":p["status"]=="PREPRODUCTION_VALIDATE_PASS" and not d["mismatch"]}
    print(json.dumps(result,ensure_ascii=False,indent=2)); return 0 if result["visual_test_ready"] else 1

def self_test(args):
    assert NON_AUTHORITY=="NON_AUTHORITY_TEST_ONLY"
    print("STORY OS V2.2.4 TEST STAGE SELF-TEST PASS"); return 0

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("check"); p.add_argument("episode_dir"); p.set_defaults(func=check)
    p=sub.add_parser("visual"); p.add_argument("episode_dir")
    g=p.add_mutually_exclusive_group(required=True); g.add_argument("--scene"); g.add_argument("--scene-file")
    p.add_argument("--plan-only",action="store_true"); p.add_argument("--image-model",default="gpt-image-2")
    p.add_argument("--strict-model",action="store_true"); p.add_argument("--timeout",type=int,default=600); p.add_argument("--codex")
    p.set_defaults(func=visual)
    p=sub.add_parser("production-smoke"); p.add_argument("episode_dir"); p.add_argument("--frame",required=True)
    p.add_argument("--prompt-file",required=True); p.add_argument("--image-model",default="gpt-image-2")
    p.add_argument("--timeout",type=int,default=600); p.add_argument("--codex"); p.set_defaults(func=production_smoke)
    p=sub.add_parser("self-test"); p.set_defaults(func=self_test)
    args=ap.parse_args()
    if hasattr(args,"timeout") and not 60 <= args.timeout <= 1200: raise SystemExit("timeout must be 60..1200")
    return args.func(args)

if __name__=="__main__": raise SystemExit(main())
