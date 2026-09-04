#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 Phase 8 Final Candidate Snapshot.

Freezes the exact publish candidate and evidence SHAs before PUBLISH_READY.
The snapshot is evidence, not a new creative authority.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import frame_semantic_review
import fast_frame_scout
import character_visual_contract
import caption_image_audit
import visual_final_freeze
from final_acceptance import valid as acceptance_valid

ROOT=Path(__file__).resolve().parents[2]
SNAPSHOT_REL=Path("meta/final-candidate-snapshot.json")
POLICY_PATH=("release","final_candidate_snapshot")


def now()->str:return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(p:Path)->dict:
    d=json.loads(p.read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict):raise ValueError(f"JSON root must be object: {p}")
    return d


def write_json(p:Path,d:dict)->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")


def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()


def sha256_json(obj:object)->str:
    raw=json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def resolve_ep(raw:str)->Path:
    ep=Path(raw).resolve()
    if not ep.is_dir():raise SystemExit(f"episode directory not found: {ep}")
    try:ep.relative_to(ROOT.resolve())
    except ValueError:raise SystemExit("episode must be inside repository")
    return ep


def repo_file(raw:object,where:str)->Path:
    if not isinstance(raw,str) or not raw.strip():raise ValueError(f"{where} missing")
    p=Path(raw.strip())
    p=p.resolve() if p.is_absolute() else (ROOT/p).resolve()
    try:p.relative_to(ROOT.resolve())
    except ValueError as exc:raise ValueError(f"{where} escapes repository") from exc
    if not p.is_file():raise ValueError(f"{where} missing: {raw}")
    return p


def repo_dir(raw:object,where:str)->Path:
    if not isinstance(raw,str) or not raw.strip():raise ValueError(f"{where} missing")
    p=Path(raw.strip())
    p=p.resolve() if p.is_absolute() else (ROOT/p).resolve()
    try:p.relative_to(ROOT.resolve())
    except ValueError as exc:raise ValueError(f"{where} escapes repository") from exc
    if not p.is_dir():raise ValueError(f"{where} missing: {raw}")
    return p


def rel(p:Path)->str:return p.resolve().relative_to(ROOT.resolve()).as_posix()


def file_row(p:Path,role:str,archive_path:str|None=None)->dict:
    row={"role":role,"path":rel(p),"sha256":sha256_file(p),"bytes":p.stat().st_size}
    if archive_path:row["archive_path"]=archive_path
    return row


def policy(ep:Path)->dict:
    p=ep/"meta/story-gates.json"
    if not p.is_file():return {}
    return (((read_json(p).get("release") or {}).get("final_candidate_snapshot")) or {})


def required(ep:Path)->bool:return policy(ep).get("enabled") is True


def enable(ep:Path)->dict:
    p=ep/"meta/story-gates.json";g=read_json(p)
    release=g.setdefault("release",{})
    cfg=release.setdefault("final_candidate_snapshot",{})
    cfg.update({"schema_version":1,"enabled":True,"delivery_must_consume_snapshot":True,"snapshot_is_authority":False})
    write_json(p,g);return cfg


def gates_lock_subset(ep:Path)->dict:
    g=read_json(ep/"meta/story-gates.json")
    visual=g.get("visual") or {}
    return {
        "tool_version":g.get("tool_version"),
        "story":g.get("story") or {},
        "visual_profile":g.get("visual_profile") or {},
        "visual":{
            "authenticity_card":visual.get("authenticity_card") or {},
            "continuity":visual.get("continuity") or {},
            "references":visual.get("references") or {},
            "environment_contract":visual.get("environment_contract") or {},
            "frame_directives":visual.get("frame_directives") or {},
            "calibration":visual.get("calibration") or {},
        },
        "reviews":g.get("reviews") or {},
        "machine_contract":g.get("machine_contract") or {},
    }


def _optional(ep:Path,relpath:str,role:str,archive:str)->dict|None:
    p=ep/relpath
    return file_row(p,role,archive) if p.is_file() else None


def preflight(ep:Path, *, write_evidence:bool=True)->None:  # STORY_OS_V2_5_R31_HOTFIX
    semantic=frame_semantic_review.verify_episode(ep,metadata_only=False,write_audit=write_evidence)
    if semantic and acceptance_valid(ep) is None:
        raise ValueError("frame semantic preflight failed: "+"; ".join(semantic[:8]))
    elif semantic:
        print("FINAL SNAPSHOT WARN: frame semantic preflight accepted as known defects (meta/final-acceptance.json)")
    freeze_errors=visual_final_freeze.verify(ep)
    if freeze_errors:
        raise ValueError("visual final freeze preflight failed: "+"; ".join(freeze_errors[:8]))
    caption_errors=caption_image_audit.verify(ep)
    if caption_errors:
        raise ValueError("caption image audit preflight failed: "+"; ".join(caption_errors[:8]))
    scout=fast_frame_scout.audit(ep,write_summary=write_evidence)
    if scout and acceptance_valid(ep) is None:
        raise ValueError("Fast Scout unresolved: "+"; ".join(scout[:8]))
    elif scout:
        print("FINAL SNAPSHOT WARN: Fast Scout REPAIR_NOW/stale accepted as known defects (meta/final-acceptance.json)")
    ta=ep/"meta/text-audit.json"
    if not ta.is_file():raise ValueError("meta/text-audit.json missing")
    if ((read_json(ta).get("summary") or {}).get("passed")) is not True:raise ValueError("text audit is not PASS")
    for required_rel in ("meta/release-semantic-review.json","meta/publish-compliance.json"):
        p=ep/required_rel
        if not p.is_file():raise ValueError(f"{required_rel} missing; run release_preflight prepare-auto first")
    master_path=ep/character_visual_contract.PIXEL_MASTER_REL
    if master_path.is_file():
        master_errors=character_visual_contract.validate_pixel_master(ep)
        crop_errors=character_visual_contract.validate_crops(ep)
        if master_errors or crop_errors:raise ValueError("character master snapshot preflight failed: "+"; ".join((master_errors+crop_errors)[:8]))
    elif character_visual_contract.pixel_master_required(ep):
        state_path=ep/"meta/episode-state.json"
        state=str(read_json(state_path).get("current_state") or "") if state_path.is_file() else ""
        if state not in {"PUBLISH_READY","PUBLISHED","DATA_REVIEWED"}:
            raise ValueError("character pixel master required before Final Candidate Snapshot")


def build_lock(ep:Path, *, write_evidence:bool=True)->dict:
    preflight(ep, write_evidence=write_evidence)
    manifest_path=ep/"meta/release-manifest.json";manifest=read_json(manifest_path)
    release=manifest.get("release") or {};art=manifest.get("artifacts") or {};episode=manifest.get("episode") or {};publication=manifest.get("publication") or {}
    story=repo_file(art.get("story"),"manifest.artifacts.story")
    storyboard=repo_file(art.get("storyboard"),"manifest.artifacts.storyboard")
    publish_dir=repo_dir(release.get("publish_dir"),"manifest.release.publish_dir")
    body_glob=str(release.get("body_glob") or "[0-9][0-9].png")
    body=sorted([p for p in publish_dir.glob(body_glob) if p.is_file()],key=lambda p:p.name)
    expected=release.get("body_frame_count")
    if not isinstance(expected,int) or expected<=0 or len(body)!=expected:raise ValueError(f"publish body count mismatch expected={expected} found={len(body)}")
    cover=repo_file(release.get("cover_path"),"manifest.release.cover_path")
    captions=repo_file(art.get("captions"),"manifest.artifacts.captions")
    publish_copy=repo_file(art.get("publish_copy"),"manifest.artifacts.publish_copy")
    propagation=repo_file(art.get("propagation_card"),"manifest.artifacts.propagation_card")

    evidence=[]
    specs=[
        ("meta/production-ledger.json","production_ledger","evidence/production-ledger.json"),
        ("meta/frame-semantic-review.json","frame_semantic_review","qa/frame-semantic-review.json"),
        ("meta/frame-semantic-audit.json","frame_semantic_audit","qa/frame-semantic-audit.json"),
        ("meta/story-semantic-review.json","story_semantic_review","qa/story-semantic-review.json"),
        ("meta/visual-profile-review.json","visual_profile_review","qa/visual-profile-review.json"),
        ("meta/subtitle-layout-audit.json","subtitle_layout_audit","qa/subtitle-layout-audit.json"),
        ("meta/text-audit.json","text_audit","qa/text-audit.json"),
        ("meta/release-semantic-review.json","release_semantic_review","qa/release-semantic-review.json"),
        ("meta/publish-compliance.json","publish_compliance","qa/publish-compliance.json"),
        ("meta/recent5-review.json","recent5_review","qa/recent5-review.json"),
        ("meta/recent5-semantic-review.json","recent5_semantic_review","qa/recent5-semantic-review.json"),
        ("meta/series-lock-binding.json","series_lock_binding","evidence/series-lock-binding.json"),
        ("meta/frame-scout-summary.json","frame_scout_summary","qa/frame-scout-summary.json"),
        ("meta/image-scheduler-performance.json","image_scheduler_performance","evidence/image-scheduler-performance.json"),
        ("meta/runtime/contracts/frame-contract-index.json","frame_contract_index","evidence/frame-contract-index.json"),
        ("meta/visual-lock-baseline-review.json","visual_lock_baseline_review","qa/visual-lock-baseline-review.json"),
        ("meta/visual-final-freeze.json","visual_final_freeze","qa/visual-final-freeze.json"),
        ("meta/caption-image-audit.json","caption_image_audit","qa/caption-image-audit.json"),
        ("meta/character-pixel-master.json","character_pixel_master_metadata","evidence/character-pixel-master.json"),
        ("meta/character-master-crops.json","character_master_crops_metadata","evidence/character-master-crops.json"),
    ]
    for rp,role,arc in specs:
        row=_optional(ep,rp,role,arc)
        if row:evidence.append(row)
    review_dir=ep/"meta/frame-reviews"
    if review_dir.is_dir():
        for p in sorted(review_dir.glob("[0-9][0-9].json")):evidence.append(file_row(p,f"frame_review:{p.stem}",f"qa/frame-reviews/{p.name}"))
    master_meta=ep/character_visual_contract.PIXEL_MASTER_REL
    if master_meta.is_file():
        md=read_json(master_meta);mp=repo_file(md.get("asset_path"),"character_pixel_master.asset_path")
        evidence.append(file_row(mp,"character_pixel_master_asset",f"evidence/character-master/{mp.name}"))
        crops_meta=ep/character_visual_contract.CROPS_REL
        if crops_meta.is_file():
            cd=read_json(crops_meta)
            for cid,row in sorted((cd.get("items") or {}).items()):
                cp=repo_file((row or {}).get("path"),f"character crop {cid}")
                evidence.append(file_row(cp,f"character_crop:{cid}",f"evidence/character-master/crops/{cp.name}"))

    delivery=[
        file_row(manifest_path,"release_manifest","release-manifest.json"),
        *[file_row(p,f"body:{p.stem}",f"publish/{p.name}") for p in body],
        file_row(cover,"cover","cover"+cover.suffix.lower()),
        file_row(captions,"captions",f"text/{captions.name}"),
        file_row(publish_copy,"publish_copy",f"text/{publish_copy.name}"),
        file_row(propagation,"propagation_card",f"text/{propagation.name}"),
        *evidence,
    ]
    lock={
        "schema_version":1,
        "episode":{"id":episode.get("id"),"series":episode.get("series"),"title":episode.get("title"),"aspect_ratio":episode.get("aspect_ratio")},
        "release_version":release.get("version"),
        "publication":publication,
        "publication_sha256":sha256_json(publication),
        "story":file_row(story,"story"),
        "storyboard":file_row(storyboard,"storyboard"),
        "story_gates_contract_sha256":sha256_json(gates_lock_subset(ep)),
        "release_manifest":file_row(manifest_path,"release_manifest","release-manifest.json"),
        "cover":file_row(cover,"cover","cover"+cover.suffix.lower()),
        "body":[file_row(p,f"body:{p.stem}",f"publish/{p.name}") for p in body],
        "text_artifacts":[file_row(captions,"captions",f"text/{captions.name}"),file_row(publish_copy,"publish_copy",f"text/{publish_copy.name}"),file_row(propagation,"propagation_card",f"text/{propagation.name}")],
        "evidence":evidence,
        "delivery_files":delivery,
    }
    return lock


def build(ep:Path)->dict:
    enable(ep)
    lock=build_lock(ep)
    snapshot={
        "schema_version":1,
        "story_os_version":frame_semantic_review.episode_contract_version(ep),
        "built_at":now(),
        "derived_evidence":True,
        "authority":"locked source files listed by SHA",
        "snapshot_is_authority":False,
        "lock":lock,
        "snapshot_sha256":sha256_json(lock),
        "release_review_binding":{
            "release_semantic_review_sha256":next((x["sha256"] for x in lock["evidence"] if x["role"]=="release_semantic_review"),None),
            "reuse_status":"BOUND",
        },
    }
    write_json(ep/SNAPSHOT_REL,snapshot)
    return snapshot


def verify(ep:Path)->list[str]:
    if not required(ep) and not (ep/SNAPSHOT_REL).is_file():return []
    p=ep/SNAPSHOT_REL
    if not p.is_file():return ["final-candidate-snapshot.json missing"]
    try:
        saved=read_json(p);current=build_lock(ep, write_evidence=False);errors=[]
        current_sha=sha256_json(current)
        if str(saved.get("snapshot_sha256") or "").lower()!=current_sha.lower():errors.append("final candidate snapshot drift")
        if saved.get("lock")!=current:errors.append("final candidate lock content drift")
        for row in current.get("delivery_files") or []:
            fp=repo_file(row.get("path"),"snapshot.delivery_file")
            if sha256_file(fp).lower()!=str(row.get("sha256") or "").lower():errors.append(f"snapshot source SHA drift: {row.get('path')}")
        return errors
    except Exception as exc:return [str(exc)]


def reuse_status(ep:Path)->dict:
    errors=verify(ep)
    if errors:return {"status":"STALE","errors":errors}
    snap=read_json(ep/SNAPSHOT_REL)
    return {"status":"REUSED","snapshot_sha256":snap.get("snapshot_sha256"),"release_semantic_review_sha256":((snap.get("release_review_binding") or {}).get("release_semantic_review_sha256"))}


def self_test()->None:
    a={"x":1,"y":[2,3]}
    assert sha256_json(a)==sha256_json({"y":[2,3],"x":1})
    print("FINAL CANDIDATE SNAPSHOT V2.1 PHASE8 SELF-TEST PASS")


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("enable");p.add_argument("episode_dir")
    p=sub.add_parser("build");p.add_argument("episode_dir")
    p=sub.add_parser("verify");p.add_argument("episode_dir")
    p=sub.add_parser("reuse-status");p.add_argument("episode_dir")
    p=sub.add_parser("show");p.add_argument("episode_dir")
    sub.add_parser("self-test")
    a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=resolve_ep(a.episode_dir)
    try:
        if a.cmd=="enable":print(json.dumps(enable(ep),ensure_ascii=False,indent=2));return 0
        if a.cmd=="build":
            s=build(ep);print(f"FINAL CANDIDATE SNAPSHOT LOCKED: {s['snapshot_sha256']}");return 0
        if a.cmd=="verify":
            errors=verify(ep)
            if errors:[print("FAIL:",e) for e in errors];return 2
            print("FINAL CANDIDATE SNAPSHOT VERIFY PASS");return 0
        if a.cmd=="reuse-status":print(json.dumps(reuse_status(ep),ensure_ascii=False,indent=2));return 0
        print((ep/SNAPSHOT_REL).read_text(encoding="utf-8"));return 0
    except (OSError,ValueError,RuntimeError) as exc:
        print("FINAL SNAPSHOT ERROR:",exc);return 3


if __name__=="__main__":raise SystemExit(main())

# STORY_OS_V2_6_0_PERFORMANCE_RUNTIME
