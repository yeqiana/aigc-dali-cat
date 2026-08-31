#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Machine bridge between Visual Lock baseline generation and the parallel three."""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, subprocess, sys
from pathlib import Path
import character_visual_contract
import frame_contract
import episode_performance

ROOT=Path(__file__).resolve().parents[2]
SYSTEM=Path(__file__).resolve().parent
REL=Path("meta/visual-lock-baseline-review.json")
CHECKS=("visual_profile_match","reality_first","ordinary_life_density","unposed_capture","not_cinematic","capture_credibility","identity_usable","group_members_distinct")

def now():return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read_json(p):
    d=json.loads(Path(p).read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict):raise ValueError(f"JSON root must be object: {p}")
    return d
def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def sha_file(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def repo_file(raw):
    p=Path(str(raw));p=p.resolve() if p.is_absolute() else (ROOT/p).resolve();p.relative_to(ROOT.resolve())
    if not p.is_file():raise ValueError(f"file missing: {raw}")
    return p
def repo_rel(p):return Path(p).resolve().relative_to(ROOT.resolve()).as_posix()

def baseline_plan(ep):
    p=Path(ep)/"meta/visual-lock-plan.json"
    if not p.is_file():raise ValueError("visual-lock-plan missing")
    row=next((x for x in (read_json(p).get("items") or []) if x.get("role")=="ordinary_baseline"),None)
    if not row:raise ValueError("ordinary_baseline missing from visual-lock-plan")
    return row
def baseline_frame(ep):return int(baseline_plan(ep)["frame"])

def generated_baseline(ep):
    ep=Path(ep).resolve();frame=baseline_frame(ep);q=read_json(ep/"meta/production-queue.json")
    rows=[x for x in (q.get("items") or []) if int(x.get("frame") or -1)==frame and x.get("scope") in {"visual_lock","repair"} and x.get("status")=="generated" and x.get("output_path")]
    if not rows:raise ValueError(f"ordinary_baseline frame {frame:02d} is not generated")
    row=rows[-1];asset=repo_file(row["output_path"])
    return {"frame":frame,"asset_path":repo_rel(asset),"sha256":sha_file(asset),"frame_contract_sha256":frame_contract.compile_frame(ep,frame,write_cache=True)["contract_sha256"],"queue_item_id":row.get("id")}

def prepare_review(ep,force=False):
    ep=Path(ep).resolve();p=ep/REL
    if p.is_file() and not force:return read_json(p)
    src=generated_baseline(ep);cv=read_json(ep/character_visual_contract.REL);primary=[str(x) for x in (cv.get("primary_cast_ids") or [])]
    d={"schema_version":1,"status":"DRAFT","decision":"PENDING","created_at":now(),"role":"ordinary_baseline",**src,
       "reviewer_scope":"delegated_pixel_review","checks":{k:"PENDING" for k in CHECKS},
       "face_boxes":[{"character_id":cid,"x":None,"y":None,"w":None,"h":None} for cid in primary],
       "note":"Inspect actual pixels. Face boxes are normalized 0..1 and derive crops only."}
    write_json(p,d)
    episode_performance.safe_begin_named_span(ep,"VISUAL_LOCK_BASELINE_REVIEW",source="visual_lock_baseline_gate",
                                              metadata={"frame":src.get("frame"),"asset_path":src.get("asset_path")})
    return d

def _box_errors(ep,review):
    if not character_visual_contract.pixel_master_required(ep):return []
    primary=set(str(x) for x in (read_json(Path(ep)/character_visual_contract.REL).get("primary_cast_ids") or []));boxes=review.get("face_boxes") or [];seen=set();e=[]
    for row in boxes:
        cid=str((row or {}).get("character_id") or "")
        if cid not in primary:continue
        try:x,y,w,h=[float(row[k]) for k in ("x","y","w","h")]
        except Exception:e.append(f"face box {cid} incomplete");continue
        if not (0<=x<1 and 0<=y<1 and 0.04<=w<=1 and 0.04<=h<=1 and x+w<=1.001 and y+h<=1.001):e.append(f"face box {cid} invalid")
        seen.add(cid)
    for cid in primary-seen:e.append(f"primary face box missing: {cid}")
    return e

def validate_review(ep):
    ep=Path(ep).resolve();p=ep/REL
    if not p.is_file():return ["visual-lock-baseline-review.json missing"]
    d=read_json(p);e=[]
    if d.get("schema_version")!=1:e.append("baseline review schema_version must be 1")
    if d.get("decision")!="PASS":e.append("baseline review decision must be PASS")
    try:src=generated_baseline(ep)
    except Exception as exc:return [str(exc)]
    for k in ("frame","asset_path","sha256","frame_contract_sha256"):
        if str(d.get(k) or "").lower()!=str(src.get(k) or "").lower():e.append(f"baseline review {k} stale")
    for k in CHECKS:
        if str((d.get("checks") or {}).get(k) or "").upper()!="PASS":e.append(f"baseline review check {k} must PASS")
    e.extend(_box_errors(ep,d));return e

def _mark_baseline_pass(ep,review):
    ep=Path(ep).resolve();gpath=ep/"meta/story-gates.json";g=read_json(gpath);items=(((g.get("visual") or {}).get("calibration") or {}).get("items") or []);hit=False
    for row in items:
        if isinstance(row,dict) and row.get("role")=="ordinary_baseline":
            row["asset_path"]=review["asset_path"];row["sha256"]=review["sha256"];row["frame_contract_sha256"]=review["frame_contract_sha256"];row["decision"]="passed";row["note"]="baseline separately PASS; parallel-three may start";hit=True
    if not hit:raise ValueError("ordinary_baseline calibration item missing")
    write_json(gpath,g)

def _ledger_pass(ep,frame):
    lp=Path(ep)/"meta/production-ledger.json"
    if not lp.is_file():return
    d=read_json(lp);status=str(((d.get("frames") or {}).get(f"{int(frame):02d}") or {}).get("status") or "")
    if status not in {"ORIGINAL_READY","REPAIR_READY"}:return
    cp=subprocess.run([sys.executable,str(SYSTEM/"production_ledger.py"),"review",str(ep),"--frame",f"{int(frame):02d}","--decision","pass","--notes","Visual Lock ordinary baseline separate PASS"],cwd=ROOT,check=False,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace")
    if cp.returncode!=0:raise ValueError("baseline ledger PASS failed: "+cp.stdout[-1200:])

def approve(ep):
    ep=Path(ep).resolve();errors=validate_review(ep)
    if errors:raise ValueError("; ".join(errors[:12]))
    review=read_json(ep/REL);_mark_baseline_pass(ep,review);_ledger_pass(ep,review["frame"])
    needs_master=character_visual_contract.pixel_master_required(ep)
    review["status"]="LOCKED";review["approved_at"]=now();review["provisional_master_created"]=needs_master;write_json(ep/REL,review)
    review_sha=sha_file(ep/REL);master=None
    if needs_master:
        master=character_visual_contract.lock_provisional_pixel_master(ep,frame=review["frame"],asset_path=review["asset_path"],asset_sha256=review["sha256"],frame_contract_sha256=review["frame_contract_sha256"],baseline_review_sha256=review_sha,face_boxes=review.get("face_boxes") or [])
        if Path(review["asset_path"]).suffix.lower()==".png":
            primary=set(str(x) for x in (read_json(ep/character_visual_contract.REL).get("primary_cast_ids") or []));made=set(((read_json(ep/character_visual_contract.CROPS_REL).get("items") or {}).keys())) if (ep/character_visual_contract.CROPS_REL).is_file() else set();missing=primary-made
            if missing:raise ValueError("primary derived crops missing: "+",".join(sorted(missing)))
    episode_performance.safe_end_named_span(ep,"VISUAL_LOCK_BASELINE_REVIEW",status="PASS",
                                            metadata={"frame":review["frame"],"pixel_master_status":(master or {}).get("status")})
    return {"baseline_review":"PASS","frame":review["frame"],"baseline_review_sha256":review_sha,"pixel_master_status":(master or {}).get("status"),"crop_result":(master or {}).get("crop_result")}

def approved(ep):
    ep=Path(ep).resolve()
    if validate_review(ep):return False
    if character_visual_contract.pixel_master_required(ep):return not character_visual_contract.validate_pixel_master(ep,allow_provisional=True)
    return True

def validate_final_requirement(ep):
    """Final verify accepts real baseline review or an explicitly marked legacy backfill."""
    ep=Path(ep).resolve();errors=validate_review(ep)
    if not errors:return []
    mp=ep/character_visual_contract.PIXEL_MASTER_REL
    if mp.is_file():
        try:
            d=read_json(mp)
            if d.get("migration_source")=="legacy_four_admission_review_backfill" and d.get("status")=="LOCKED":
                master_errors=character_visual_contract.validate_pixel_master(ep)
                if not master_errors:return []
        except Exception:pass
    return errors

def is_baseline_dependency(ep,dep):
    try:return int(dep)==baseline_frame(ep)
    except Exception:return False

def awaiting_review(ep,q):
    try:
        frame=baseline_frame(ep)
        if approved(ep):return False
        generated=any(int(x.get("frame") or -1)==frame and x.get("status")=="generated" for x in (q.get("items") or []))
        dependents=any(x.get("status")=="queued" and x.get("scope")=="visual_lock" and frame in [int(v) for v in (x.get("depends_on") or [])] for x in (q.get("items") or []))
        return generated and dependents
    except Exception:return False

def self_test():assert len(CHECKS)>=8;print("VISUAL LOCK BASELINE GATE SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("prepare-review");p.add_argument("episode_dir");p.add_argument("--force",action="store_true")
    p=sub.add_parser("approve");p.add_argument("episode_dir");p=sub.add_parser("verify");p.add_argument("episode_dir");p=sub.add_parser("status");p.add_argument("episode_dir");sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve()
    try:
        if a.cmd=="prepare-review":print(json.dumps(prepare_review(ep,a.force),ensure_ascii=False,indent=2));return 0
        if a.cmd=="approve":print(json.dumps(approve(ep),ensure_ascii=False,indent=2));return 0
        if a.cmd=="verify":
            e=validate_review(ep)
            if e:[print("FAIL:",x) for x in e];return 2
            print("VISUAL LOCK BASELINE REVIEW VERIFIED");return 0
        print(json.dumps({"approved":approved(ep),"awaiting_review":awaiting_review(ep,read_json(ep/"meta/production-queue.json")) if (ep/"meta/production-queue.json").is_file() else False},ensure_ascii=False,indent=2));return 0
    except Exception as exc:print("BASELINE GATE ERROR:",exc);return 3
if __name__=="__main__":raise SystemExit(main())
