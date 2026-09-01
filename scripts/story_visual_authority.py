#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent

def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def save(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def ep(raw):
    p=Path(raw).resolve()
    if not p.is_dir(): raise SystemExit(f"episode directory not found: {p}")
    try: p.relative_to(ROOT.resolve())
    except ValueError: raise SystemExit("episode must be inside current repository")
    return p
def bp(ep):
    c=sorted((ep/"meta").glob("*blueprint*.json"))
    if not c: raise SystemExit("episode blueprint missing")
    return c[0]
def mp(ep):
    for n in ["visual-profile.json","visual_profile.json"]:
        p=ep/"meta"/n
        if p.is_file(): return p
    raise SystemExit("episode meta visual profile missing")
def state(e):
    bpp=bp(e); mpp=mp(e); b=load(bpp); m=load(mpp)
    v=b.get("visual_profile"); bid=v.get("profile_id") if isinstance(v,dict) else v
    mid=m.get("profile_id")
    return {"blueprint_profile_id":bid,"episode_meta_profile_id":mid,"mismatch":bool(bid and mid and bid!=mid),
            "blueprint":str(bpp.relative_to(ROOT)),"episode_meta":str(mpp.relative_to(ROOT))}
def check(args):
    s=state(ep(args.episode_dir)); print(json.dumps(s,ensure_ascii=False,indent=2)); return 1 if s["mismatch"] else 0
def sync(args):
    e=ep(args.episode_dir); bpp=bp(e); mpp=mp(e); b=load(bpp); m=load(mpp)
    pid=str(m.get("profile_id") or "").strip()
    if not pid: raise SystemExit("episode meta profile_id missing")
    canonical=ROOT/"standards"/"visual_profiles"/f"{pid}.json"
    if not canonical.is_file(): raise SystemExit(f"canonical visual profile missing: {canonical.relative_to(ROOT)}")
    stamp=dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup=e/"meta"/"migrations"/f"episode-blueprint-pre-v224-{stamp}.json"
    backup.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(bpp,backup)
    v=b.get("visual_profile")
    if not isinstance(v,dict): v={}; b["visual_profile"]=v
    v["profile_id"]=pid; v["path"]=str(mpp.relative_to(ROOT)).replace("\\","/")
    v["mode"]="episode_meta_locked"; v["override_reason"]=str(m.get("override_reason") or "synced from episode meta authority")
    b["tool_version"]="2.2.4"; save(bpp,b)
    report={"status":"VISUAL_AUTHORITY_SYNC_PASS","profile_id":pid,"blueprint":str(bpp.relative_to(ROOT)),
            "authority":str(mpp.relative_to(ROOT)),"canonical_profile":str(canonical.relative_to(ROOT)),
            "backup":str(backup.relative_to(ROOT))}
    save(e/"meta"/"migrations"/"visual-authority-v224.json",report)
    print(json.dumps(report,ensure_ascii=False,indent=2)); return 0
def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("check"); p.add_argument("episode_dir"); p.set_defaults(func=check)
    p=sub.add_parser("sync-blueprint"); p.add_argument("episode_dir"); p.set_defaults(func=sync)
    a=ap.parse_args(); return a.func(a)
if __name__=="__main__": raise SystemExit(main())
