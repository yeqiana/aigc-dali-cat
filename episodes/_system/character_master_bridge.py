#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Safe backfill for episodes that passed Visual Lock before pixel-master closure."""
from __future__ import annotations
import argparse, datetime as dt, json
from pathlib import Path
import character_visual_contract
import visual_lock_v21
ROOT=Path(__file__).resolve().parents[2]
SAFE_STATES={"VISUAL_CALIBRATED","PRODUCTION_PASSED"}
def now():return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read_json(p):
    d=json.loads(Path(p).read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict):raise ValueError(f"JSON root must be object: {p}")
    return d
def state(ep):
    p=Path(ep)/"meta/episode-state.json";return str(read_json(p).get("current_state") or "") if p.is_file() else ""
def base_visual_lock_errors(ep):
    ep=Path(ep).resolve();p=ep/visual_lock_v21.REVIEW_REL
    if not p.is_file():return ["visual-profile-review missing"]
    try:
        contract=visual_lock_v21.compile_prompt_contract(ep);assets=visual_lock_v21.calibration_assets(ep)
        return visual_lock_v21.validate_payload(read_json(p),contract=contract,assets=assets,version=visual_lock_v21.episode_version(ep))
    except Exception as exc:return [str(exc)]
def backfill_episode(ep):
    ep=Path(ep).resolve()
    if state(ep) not in SAFE_STATES:return {"status":"SKIP","reason":"state_not_safe_for_derived_backfill","state":state(ep)}
    if not (ep/character_visual_contract.REL).is_file():return {"status":"SKIP","reason":"character_visual_contract_missing"}
    if not character_visual_contract.pixel_master_required(ep):return {"status":"SKIP","reason":"pixel_master_not_required"}
    if (ep/character_visual_contract.PIXEL_MASTER_REL).is_file():
        existing_errors=character_visual_contract.validate_pixel_master(ep)
        if not existing_errors:return {"status":"REUSED"}
        return {"status":"SKIP","reason":"invalid_existing_master_not_overwritten","errors":existing_errors[:8]}
    errors=base_visual_lock_errors(ep)
    if errors:return {"status":"SKIP","reason":"visual_lock_not_machine_valid","errors":errors[:8]}
    assets=visual_lock_v21.calibration_assets(ep);baseline=next(x for x in assets if x["role"]=="ordinary_baseline")
    master=character_visual_contract.lock_pixel_master(ep,frame=baseline["frame"],asset_path=baseline["asset_path"],asset_sha256=baseline["sha256"],frame_contract_sha256=baseline["frame_contract_sha256"])
    mp=ep/character_visual_contract.PIXEL_MASTER_REL
    master=read_json(mp);master["migration_source"]="legacy_four_admission_review_backfill";master["legacy_backfill_at"]=now();character_visual_contract.write_json(mp,master)
    review=ep/"meta/visual-lock-baseline-review.json"
    if review.is_file():
        try:character_visual_contract.derive_face_crops(ep,read_json(review).get("face_boxes") or [],allow_non_png=True)
        except Exception:pass
    return {"status":"BACKFILLED","frame":baseline["frame"],"sha256":master["sha256"]}
def backfill_all():
    import episode_discovery
    results=[]
    for ep in episode_discovery.iter_episode_roots(ROOT/"episodes"):
        p=ep/"meta/visual-profile-review.json"
        if not p.is_file():continue
        try:r=backfill_episode(ep)
        except Exception as exc:r={"status":"ERROR","error":str(exc)}
        if r.get("status")!="SKIP":results.append({"episode":ep.relative_to(ROOT).as_posix(),**r})
    out={"schema_version":1,"generated_at":now(),"safe_states":sorted(SAFE_STATES),"results":results};rp=ROOT/"reports/character-master-backfill.json";rp.parent.mkdir(parents=True,exist_ok=True);rp.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n");return out
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True);p=sub.add_parser("backfill");p.add_argument("episode_dir");sub.add_parser("backfill-all");a=ap.parse_args()
    print(json.dumps(backfill_all() if a.cmd=="backfill-all" else backfill_episode(Path(a.episode_dir).resolve()),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
