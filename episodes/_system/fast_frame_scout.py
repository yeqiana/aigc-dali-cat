#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 Phase 7 Fast Frame Scout.

Scout is an early triage layer, NEVER the final Production PASS authority.
Decisions:
- PASS_FAST: no obvious early defect; still requires Final Frame Semantic Critic.
- REPAIR_NOW: obvious high-confidence defect; may move ready candidate to CONTENT_FAILED.
- DEFER_TO_FINAL: low-risk or uncertain; final critic decides.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import frame_contract
import runtime_router

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ("visual", "fast_frame_scout")
RESULT_DIR = Path("meta/frame-scouts")
SUMMARY_REL = Path("meta/frame-scout-summary.json")
ISSUE_CODES = {
    "IDENTITY_OBVIOUS_DRIFT",
    "KEY_PROP_OBVIOUS_DRIFT",
    "WEATHER_OBVIOUS_MISMATCH",
    "ANOMALY_SCALE_OBVIOUSLY_WEAK",
    "POV_RECORDER_OBVIOUSLY_ILLEGAL",
    "CONTINUITY_OBVIOUS_BREAK",
    "FRAME_CONTRACT_OBVIOUS_MISMATCH",
}
DECISIONS = {"PASS_FAST", "REPAIR_NOW", "DEFER_TO_FINAL"}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    data=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data,dict): raise ValueError(f"JSON root must be object: {path}")
    return data


def write_json(path: Path,data:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()


def resolve_ep(raw:str)->Path:
    ep=Path(raw).resolve()
    if not ep.is_dir(): raise SystemExit(f"episode directory not found: {ep}")
    try: ep.relative_to(ROOT.resolve())
    except ValueError: raise SystemExit("episode must be inside repository")
    return ep


def repo_file(raw:object)->Path:
    if not isinstance(raw,str) or not raw.strip(): raise ValueError("image path missing")
    p=Path(raw.strip())
    p=p.resolve() if p.is_absolute() else (ROOT/p).resolve()
    try:p.relative_to(ROOT.resolve())
    except ValueError as exc: raise ValueError("path escapes repository") from exc
    if not p.is_file(): raise ValueError(f"image missing: {raw}")
    return p


def policy(ep:Path)->dict:
    p=ep/"meta/story-gates.json"
    if not p.is_file(): return {}
    g=read_json(p)
    return (((g.get("visual") or {}).get("fast_frame_scout")) or {})


def required(ep:Path)->bool:
    return policy(ep).get("enabled") is True


def enable(ep:Path)->dict:
    p=ep/"meta/story-gates.json";g=read_json(p)
    visual=g.setdefault("visual",{})
    scout=visual.setdefault("fast_frame_scout",{})
    scout.update({
        "schema_version":1,
        "enabled":True,
        "policy":"risk_based_v21",
        "final_critic_still_required":True,
        "decisions":["PASS_FAST","REPAIR_NOW","DEFER_TO_FINAL"],
        "high_risk_required":True,
    })
    write_json(p,g)
    return scout


def _contains(text:str,tokens:tuple[str,...])->bool:
    low=text.lower()
    return any(x.lower() in low for x in tokens)


def classify_frame(ep:Path,frame:int)->dict:
    c=frame_contract.compile_frame(ep,frame,write_cache=True)
    hm=c["hash_material"];d=hm.get("frame_directive") or {}
    tags=[];score=0
    mode=str(d.get("frame_mode") or "")
    role=str(d.get("narrative_role") or "")
    impact=int(d.get("impact_level") or 0)
    if mode=="climax_impact":tags.append("climax");score+=50
    if mode=="anomaly_amplified":tags.append("anomaly_amplified");score+=42
    if mode=="anomaly_reveal":tags.append("first_anomaly");score+=35
    if role in {"climax","payoff","reveal","residue"}:tags.append(role);score+=25
    if impact>=3:tags.append("impact_3_4");score+=30
    elif impact==2:tags.append("impact_2");score+=18
    refs=hm.get("references") or []
    if any(isinstance(x,dict) and x.get("kind")=="identity" for x in refs):tags.append("identity");score+=30
    if any(isinstance(x,dict) and x.get("kind")=="prop" for x in refs):tags.append("key_prop");score+=24
    blob=json.dumps({
        "authenticity":hm.get("authenticity_card") or {},
        "continuity":hm.get("continuity") or {},
        "directive":d,
    },ensure_ascii=False)
    if _contains(blob,("pov","first_person","first-person","第一视角","拍摄者","自拍","recorder","摄影者")):
        tags.append("pov_recorder");score+=28
    total=frame_contract.frame_count(ep)
    if frame>=max(1,total-1):tags.append("ending");score+=18
    env=hm.get("environment") or {}
    if _contains(json.dumps(env,ensure_ascii=False),("storm","heavy rain","fog","snow","dust","sand","暴雨","大雾","暴雪","沙尘")):
        tags.append("difficult_environment");score+=15
    level="HIGH" if score>=45 else "MEDIUM" if score>=25 else "LOW"
    return {"frame":f"{frame:02d}","risk_level":level,"risk_score":score,"risk_tags":sorted(set(tags)),"frame_contract_sha256":c["contract_sha256"]}


def resolve_codex(raw:str|None)->Path:
    value=raw or shutil.which("codex") or shutil.which("codex.exe") or shutil.which("codex.cmd")
    if not value: raise RuntimeError("Codex CLI not found")
    p=Path(value).expanduser().resolve()
    if not p.exists(): raise RuntimeError(f"Codex CLI not found: {p}")
    return p


def prefix(codex:Path)->list[str]:
    if codex.suffix.lower()==".py":return [sys.executable,str(codex)]
    if os.name=="nt" and codex.suffix.lower() in {".cmd",".bat"}:return ["cmd.exe","/d","/c",str(codex)]
    return [str(codex)]


def _result_path(ep:Path,frame:int)->Path:
    return ep/RESULT_DIR/f"{frame:02d}.json"


def _candidate_path(ep:Path,frame:int,asset_sha:str)->Path:
    return ep/"meta"/f".frame-scout-{frame:02d}-{asset_sha[:10]}.candidate.json"


def _validate_model(data:dict)->list[str]:
    errors=[]
    decision=str(data.get("decision") or "")
    if decision not in DECISIONS:errors.append("invalid scout decision")
    codes=data.get("issue_codes")
    if not isinstance(codes,list):errors.append("issue_codes must be list");codes=[]
    unknown=[x for x in codes if x not in ISSUE_CODES]
    if unknown:errors.append(f"unknown issue_codes: {unknown}")
    if decision=="REPAIR_NOW" and not codes:errors.append("REPAIR_NOW requires issue_codes")
    if decision=="PASS_FAST" and codes:errors.append("PASS_FAST issue_codes must be empty")
    return errors


def evaluate_candidate(ep:Path,frame:int,image:Path|str,*,codex_raw:str|None=None,timeout:int=240)->dict:
    image=repo_file(str(image))
    risk=classify_frame(ep,frame)
    contract=frame_contract.compile_frame(ep,frame,write_cache=True)
    asset_sha=sha256_file(image)
    base={
        "schema_version":1,
        "story_os_version":contract["story_os_version"],
        **risk,
        "asset_path":image.relative_to(ROOT).as_posix(),
        "asset_sha256":asset_sha,
        "scouted_at":now(),
        "final_critic_still_required":True,
    }
    if not required(ep):
        result={**base,"decision":"DEFER_TO_FINAL","issue_codes":[],"notes":"Scout policy disabled for this episode.","model_called":False,"scout_status":"disabled"}
        write_json(_result_path(ep,frame),result);return result
    if risk["risk_level"]=="LOW":
        result={**base,"decision":"DEFER_TO_FINAL","issue_codes":[],"notes":"Low-risk frame: skip extra critic call; final critic remains authoritative.","model_called":False,"scout_status":"low_risk_defer"}
        write_json(_result_path(ep,frame),result);return result

    candidate=_candidate_path(ep,frame,asset_sha);candidate.unlink(missing_ok=True)
    rel_out=candidate.relative_to(ROOT).as_posix()
    prompt=f"""You are Story OS V2.1 Fast Frame Scout. Triage ONE actual generated image, not the whole story.
This is NOT the final critic. Use REPAIR_NOW only for obvious, high-confidence defects worth fixing immediately.
Use PASS_FAST only when there is no obvious early defect. PASS_FAST never authorizes Production PASS.
Use DEFER_TO_FINAL when uncertain or when the issue needs neighboring/full-story context.

Risk: {json.dumps(risk,ensure_ascii=False)}
Resolved Frame Contract:
<frame_contract>
{contract['prompt_contract']}
</frame_contract>

Look only for obvious:
- identity drift
- key prop drift
- weather/environment physical mismatch
- promised anomaly scale clearly underdelivered
- illegal POV / impossible visible recorder
- obvious continuity break visible from this frame and locked references
- clear contradiction with current Frame Contract

Do NOT fail because the anomaly is huge/impossible. Judge capture credibility, not existence plausibility.
Write ONLY JSON to {rel_out}:
{{"decision":"PASS_FAST|REPAIR_NOW|DEFER_TO_FINAL","issue_codes":[],"notes":"brief actual-pixel evidence","confidence":0.0}}
Allowed issue codes: {sorted(ISSUE_CODES)}
"""
    active_runtime,_=runtime_router.detect()
    if active_runtime in {"WORK","WEB"} and not codex_raw:
        result={
            **base,
            "decision":"DEFER_TO_FINAL",
            "issue_codes":[],
            "notes":f"{active_runtime} product runtime: Fast Scout is non-blocking and does not launch local Codex; defer actual-pixel authority to product/final review.",
            "model_called":False,
            "scout_status":"product_runtime_defer",
        }
        write_json(_result_path(ep,frame),result)
        return result
    try:
        codex=resolve_codex(codex_raw)
        cmd=prefix(codex)+["exec","--skip-git-repo-check","--ephemeral","-c",'model_reasoning_effort="low"',"-s","workspace-write","-C",str(ROOT),"--json","-i",str(image),"-"]
        log=ep/"meta/frame-scouts"/f"{frame:02d}.jsonl";log.parent.mkdir(parents=True,exist_ok=True)
        with log.open("w",encoding="utf-8",newline="\n") as h:
            done=subprocess.run(cmd,input=prompt,text=True,encoding="utf-8",stdout=h,stderr=subprocess.STDOUT,timeout=timeout,check=False)
        if done.returncode!=0 or not candidate.is_file():
            raise RuntimeError(f"scout critic failed rc={done.returncode}")
        model=read_json(candidate);candidate.unlink(missing_ok=True)
        errors=_validate_model(model)
        if errors:raise RuntimeError("; ".join(errors))
        result={**base,**model,"model_called":True,"scout_status":"model_complete","critic_log":log.relative_to(ROOT).as_posix()}
    except Exception as exc:
        result={**base,"decision":"DEFER_TO_FINAL","issue_codes":[],"notes":f"Scout technical defer: {exc}","model_called":True,"scout_status":"technical_defer"}
    write_json(_result_path(ep,frame),result)
    return result


def latest_candidate_rows(ep:Path)->list[dict]:
    p=ep/"meta/production-ledger.json"
    if not p.is_file():return []
    d=read_json(p);rows=[]
    for key,row in sorted((d.get("frames") or {}).items()):
        if not isinstance(row,dict):continue
        asset=row.get("approved_asset") or row.get("current_candidate")
        if not isinstance(asset,dict):continue
        raw=asset.get("path") or asset.get("asset_path")
        sha=str(asset.get("sha256") or "")
        if raw and sha:rows.append({"frame":int(key),"status":row.get("status"),"path":raw,"sha256":sha})
    return rows


def audit(ep:Path,*,write_summary:bool=True)->list[str]:
    if not required(ep):return []
    errors=[];rows=[]
    for item in latest_candidate_rows(ep):
        risk=classify_frame(ep,item["frame"])
        scout_path=_result_path(ep,item["frame"])
        required_now=risk["risk_level"]=="HIGH"
        scout=read_json(scout_path) if scout_path.is_file() else None
        if required_now and not isinstance(scout,dict):
            errors.append(f"high-risk frame {item['frame']:02d} missing Fast Scout")
            continue
        if isinstance(scout,dict):
            if str(scout.get("asset_sha256") or "").lower()!=item["sha256"].lower():
                if required_now:errors.append(f"high-risk frame {item['frame']:02d} scout stale for current asset")
            if scout.get("frame_contract_sha256")!=risk["frame_contract_sha256"] and required_now:
                errors.append(f"high-risk frame {item['frame']:02d} scout frame contract stale")
            if scout.get("decision")=="REPAIR_NOW":
                errors.append(f"frame {item['frame']:02d} unresolved REPAIR_NOW")
            rows.append({"frame":f"{item['frame']:02d}","risk":risk["risk_level"],"decision":scout.get("decision"),"asset_sha256":item["sha256"]})
        else:
            rows.append({"frame":f"{item['frame']:02d}","risk":risk["risk_level"],"decision":"NOT_SCOUTED","asset_sha256":item["sha256"]})
    if write_summary:
        # Keep the summary deterministic: snapshot verification may call audit repeatedly.
        # A wall-clock timestamp here would change the evidence SHA on every verification.
        evidence_times=[]
        for row in rows:
            sp=_result_path(ep,int(row["frame"]))
            if sp.is_file():
                try:evidence_times.append(str(read_json(sp).get("scouted_at") or ""))
                except Exception:pass
        write_json(ep/SUMMARY_REL,{"schema_version":1,"evidence_updated_at":max(evidence_times) if evidence_times else None,"policy":"risk_based_v21","rows":rows,"errors":errors,"summary":{"passed":not errors,"final_critic_still_required":True}})
    return errors


def self_test()->None:
    assert DECISIONS=={"PASS_FAST","REPAIR_NOW","DEFER_TO_FINAL"}
    assert "ANOMALY_SCALE_OBVIOUSLY_WEAK" in ISSUE_CODES
    print("FAST FRAME SCOUT V2.1 PHASE7 SELF-TEST PASS")


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("enable");p.add_argument("episode_dir")
    p=sub.add_parser("classify");p.add_argument("episode_dir");p.add_argument("--frame",type=int,required=True)
    p=sub.add_parser("run");p.add_argument("episode_dir");p.add_argument("--frame",type=int,required=True);p.add_argument("--image",required=True);p.add_argument("--codex");p.add_argument("--timeout",type=int,default=240)
    p=sub.add_parser("audit");p.add_argument("episode_dir")
    p=sub.add_parser("show");p.add_argument("episode_dir");p.add_argument("--frame",type=int)
    sub.add_parser("self-test")
    a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=resolve_ep(a.episode_dir)
    try:
        if a.cmd=="enable":print(json.dumps(enable(ep),ensure_ascii=False,indent=2));return 0
        if a.cmd=="classify":print(json.dumps(classify_frame(ep,a.frame),ensure_ascii=False,indent=2));return 0
        if a.cmd=="run":
            result=evaluate_candidate(ep,a.frame,a.image,codex_raw=a.codex,timeout=a.timeout)
            print(json.dumps(result,ensure_ascii=False,indent=2));return 5 if result["decision"]=="REPAIR_NOW" else 0
        if a.cmd=="audit":
            errors=audit(ep)
            if errors:
                [print("FAIL:",x) for x in errors];return 2
            print("FAST FRAME SCOUT AUDIT PASS");return 0
        if a.frame:
            p=_result_path(ep,a.frame);print(p.read_text(encoding="utf-8") if p.is_file() else "{}")
        else:
            p=ep/SUMMARY_REL;print(p.read_text(encoding="utf-8") if p.is_file() else "{}")
        return 0
    except (OSError,RuntimeError,ValueError,subprocess.TimeoutExpired) as exc:
        print("FAST FRAME SCOUT ERROR:",exc);return 3


if __name__=="__main__":raise SystemExit(main())
