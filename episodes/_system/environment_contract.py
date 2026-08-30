#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 Phase 3 Environment Contract + Anomaly Impact validator.

Authoritative data stays embedded in meta/story-gates.json:
  visual.environment_contract
  visual.frame_directives
This tool creates/validates/resolves derived per-frame physical context.
It does NOT create a second episode stage or a second visual authority.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

from story_os_contract import story_os_version

ROOT = Path(__file__).resolve().parents[2]
MIN_VERSION = (2, 1, 0)
ROLES = {"setup","evidence","transition","escalation","reveal","climax","payoff","residue"}
MODES = {"normal_record","anomaly_reveal","anomaly_amplified","climax_impact","payoff"}

def read_json(path: Path) -> dict:
    data=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data,dict): raise ValueError(f"JSON root must be object: {path}")
    return data

def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")

def sha256_json(data: object) -> str:
    raw=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def version_tuple(raw: object) -> tuple[int,...]:
    try:return tuple(int(x) for x in str(raw or "").split("."))
    except Exception:return (0,)

def episode_version(ep: Path) -> str:
    versions=[]
    for rel in ("meta/episode-state.json","meta/release-manifest.json","meta/story-gates.json"):
        p=ep/rel
        if not p.is_file():continue
        try:
            raw=str(read_json(p).get("tool_version") or "")
            vt=version_tuple(raw)
            if vt!=(0,):versions.append((vt,raw))
        except Exception:pass
    return max(versions,key=lambda x:x[0])[1] if versions else story_os_version()

def required(ep: Path) -> bool:
    return version_tuple(episode_version(ep)) >= MIN_VERSION

def resolve_ep(raw: str) -> Path:
    ep=Path(raw).resolve()
    if not ep.is_dir():raise SystemExit(f"episode directory not found: {ep}")
    try:ep.relative_to(ROOT.resolve())
    except ValueError:raise SystemExit("episode must be inside repository")
    return ep

def frame_count(ep: Path) -> int:
    manifest=read_json(ep/"meta/release-manifest.json")
    n=((manifest.get("release") or {}).get("body_frame_count"))
    if isinstance(n,bool) or not isinstance(n,int) or n<=0:raise ValueError("release.body_frame_count must be >0")
    return n

def _s(v: object) -> str:return str(v or "").strip()

def _frame_key(raw: object, total: int) -> str:
    if isinstance(raw,bool):raise ValueError("invalid frame key")
    try:n=int(str(raw))
    except Exception as exc:raise ValueError(f"invalid frame key: {raw}") from exc
    if not 1<=n<=total:raise ValueError(f"frame out of range: {n}/{total}")
    return f"{n:02d}"

def current_contract(ep: Path) -> tuple[dict,dict]:
    gates=read_json(ep/"meta/story-gates.json")
    visual=gates.get("visual") or {}
    return visual.get("environment_contract") or {}, visual.get("frame_directives") or {}

def validate_environment(env: dict, total: int) -> list[str]:
    errors=[]
    if not isinstance(env,dict):return ["visual.environment_contract must be object"]
    if env.get("schema_version") != 1:errors.append("environment_contract.schema_version must be 1")
    baseline=env.get("baseline")
    if not isinstance(baseline,dict):
        errors.append("environment_contract.baseline must be object")
    else:
        for key in ("condition","time_of_day","ground_state","visibility"):
            if not _s(baseline.get(key)):errors.append(f"environment_contract.baseline.{key} missing")
        cues=baseline.get("physical_cues")
        if not isinstance(cues,list) or not all(_s(x) for x in cues):
            errors.append("environment_contract.baseline.physical_cues must be non-empty string array")
    segments=env.get("segments")
    if not isinstance(segments,list):errors.append("environment_contract.segments must be array");segments=[]
    occupied=set()
    ids=set()
    for i,row in enumerate(segments):
        w=f"environment_contract.segments[{i}]"
        if not isinstance(row,dict):errors.append(f"{w} must be object");continue
        sid=_s(row.get("id"))
        if not sid:errors.append(f"{w}.id missing")
        elif sid in ids:errors.append(f"duplicate environment segment id: {sid}")
        ids.add(sid)
        a,b=row.get("start_frame"),row.get("end_frame")
        if isinstance(a,bool) or isinstance(b,bool) or not isinstance(a,int) or not isinstance(b,int) or not(1<=a<=b<=total):
            errors.append(f"{w} invalid frame range");continue
        rng=set(range(a,b+1))
        if occupied & rng:errors.append(f"{w} overlaps another segment")
        occupied |= rng
        if not _s(row.get("condition")):errors.append(f"{w}.condition missing")
        cues=row.get("physical_cues")
        if not isinstance(cues,list) or not all(_s(x) for x in cues):
            errors.append(f"{w}.physical_cues must be non-empty string array")
        cond=row.get("conditional_effects",[])
        if not isinstance(cond,list):errors.append(f"{w}.conditional_effects must be array")
        else:
            for j,effect in enumerate(cond):
                ew=f"{w}.conditional_effects[{j}]"
                if not isinstance(effect,dict):errors.append(f"{ew} must be object");continue
                if not _s(effect.get("effect")):errors.append(f"{ew}.effect missing")
                when=effect.get("when")
                if not isinstance(when,list) or not when or not all(_s(x) for x in when):
                    errors.append(f"{ew}.when must be non-empty string array")
    overrides=env.get("frame_overrides",{})
    if not isinstance(overrides,dict):errors.append("environment_contract.frame_overrides must be object")
    else:
        for raw,row in overrides.items():
            try:_frame_key(raw,total)
            except ValueError as exc:errors.append(str(exc))
            if not isinstance(row,dict) or not row:errors.append(f"frame_overrides.{raw} must be non-empty object")
    return errors

def validate_directives(ep: Path, directives: dict, total: int) -> list[str]:
    errors=[]
    if not isinstance(directives,dict):return ["visual.frame_directives must be object"]
    expected={f"{i:02d}" for i in range(1,total+1)}
    actual=set()
    norm={}
    for raw,row in directives.items():
        try:key=_frame_key(raw,total)
        except ValueError as exc:errors.append(str(exc));continue
        actual.add(key);norm[key]=row
    if actual != expected:
        missing=sorted(expected-actual);extra=sorted(actual-expected)
        if missing:errors.append(f"frame_directives missing frames: {missing}")
        if extra:errors.append(f"frame_directives unexpected frames: {extra}")
    for key,row in norm.items():
        w=f"frame_directives.{key}"
        if not isinstance(row,dict):errors.append(f"{w} must be object");continue
        role=_s(row.get("narrative_role"));mode=_s(row.get("frame_mode"));impact=row.get("impact_level")
        if role not in ROLES:errors.append(f"{w}.narrative_role invalid")
        if mode not in MODES:errors.append(f"{w}.frame_mode invalid")
        if isinstance(impact,bool) or not isinstance(impact,int) or not 0<=impact<=4:
            errors.append(f"{w}.impact_level must be integer 0..4");continue
        cues=row.get("required_visual_cues")
        if not isinstance(cues,list) or not all(_s(x) for x in cues):
            errors.append(f"{w}.required_visual_cues must be string array")
        if impact>=2 and not cues:errors.append(f"{w} impact>=2 requires required_visual_cues")
        scale=_s(row.get("scale_reference"))
        esc=row.get("escalation_from")
        if mode=="normal_record" and impact>1:errors.append(f"{w} normal_record impact must be <=1")
        if mode=="anomaly_reveal" and not 1<=impact<=2:errors.append(f"{w} anomaly_reveal impact must be 1..2")
        if mode in {"anomaly_amplified","climax_impact"}:
            if impact<3:errors.append(f"{w} {mode} impact must be >=3")
            if not scale:errors.append(f"{w} {mode} requires scale_reference")
            if esc is None:errors.append(f"{w} {mode} requires escalation_from")
            else:
                try:
                    e=int(esc)
                    if not 1<=e<int(key):errors.append(f"{w}.escalation_from must reference an earlier frame")
                except Exception:errors.append(f"{w}.escalation_from invalid")
    try:
        gates=read_json(ep/"meta/story-gates.json")
        climax=((gates.get("story") or {}).get("climax_frame"))
        if isinstance(climax,int) and 1<=climax<=total:
            row=norm.get(f"{climax:02d}") or {}
            if row.get("frame_mode")!="climax_impact":errors.append("story.climax_frame must use frame_mode=climax_impact")
            if not isinstance(row.get("impact_level"),int) or row.get("impact_level")<3:errors.append("story.climax_frame impact_level must be >=3")
    except Exception as exc:errors.append(f"cannot validate climax directive: {exc}")
    return errors

def verify(ep: Path) -> list[str]:
    if not required(ep):return []
    try:
        total=frame_count(ep);env,directives=current_contract(ep)
    except Exception as exc:return [str(exc)]
    return validate_environment(env,total)+validate_directives(ep,directives,total)

def init_contract(ep: Path, force: bool=False) -> int:
    gates_path=ep/"meta/story-gates.json";g=read_json(gates_path);visual=g.setdefault("visual",{})
    total=frame_count(ep)
    if force or not isinstance(visual.get("environment_contract"),dict):
        visual["environment_contract"]={
            "schema_version":1,
            "season":"",
            "baseline":{"condition":"","time_of_day":"","temperature_feel":"","ground_state":"","visibility":"","wind":"","precipitation":"","physical_cues":[]},
            "segments":[],
            "frame_overrides":{}
        }
    if force or not isinstance(visual.get("frame_directives"),dict):
        climax=((g.get("story") or {}).get("climax_frame"))
        rows={}
        for i in range(1,total+1):
            mode="climax_impact" if i==climax else "normal_record"
            rows[f"{i:02d}"]={
                "narrative_role":"climax" if i==climax else "setup",
                "frame_mode":mode,
                "impact_level":3 if i==climax else 0,
                "required_visual_cues":[],
                "scale_reference":"",
                "escalation_from":None
            }
        visual["frame_directives"]=rows
    write_json(gates_path,g);print(gates_path);return 0

def resolve_frame(ep: Path, frame: int) -> dict:
    total=frame_count(ep)
    if not 1<=frame<=total:raise ValueError(f"frame out of range: {frame}/{total}")
    env,directives=current_contract(ep)
    errors=validate_environment(env,total)+validate_directives(ep,directives,total)
    if errors:raise ValueError("environment contract invalid: "+"; ".join(errors[:8]))
    merged=dict(env.get("baseline") or {})
    active=[]
    for seg in env.get("segments") or []:
        if seg["start_frame"]<=frame<=seg["end_frame"]:
            for k,v in seg.items():
                if k not in {"id","start_frame","end_frame"}:merged[k]=v
            active.append(seg["id"])
    override=(env.get("frame_overrides") or {}).get(f"{frame:02d}") or (env.get("frame_overrides") or {}).get(str(frame)) or {}
    merged.update(override)
    directive=(directives.get(f"{frame:02d}") or directives.get(str(frame)) or {})
    return {
        "frame":f"{frame:02d}",
        "environment":merged,
        "active_segments":active,
        "directive":directive,
        "environment_frame_sha256":sha256_json({"environment":merged,"active_segments":active}),
        "frame_directive_sha256":sha256_json(directive)
    }

def frame_hashes(ep: Path, frame: str|int) -> dict:
    row=resolve_frame(ep,int(frame))
    return {"environment_frame_sha256":row["environment_frame_sha256"],"frame_directive_sha256":row["frame_directive_sha256"]}

def self_test():
    env={"schema_version":1,"baseline":{"condition":"hot","time_of_day":"day","ground_state":"dry","visibility":"clear","physical_cues":["hard sunlight"]},"segments":[{"id":"S1","start_frame":2,"end_frame":3,"condition":"storm","physical_cues":["wet ground"],"conditional_effects":[{"effect":"lens moisture","when":["outdoor","exposed lens"]}]}],"frame_overrides":{}}
    assert validate_environment(env,4)==[]
    bad=json.loads(json.dumps(env));bad["segments"][0]["conditional_effects"][0]["when"]=[]
    assert validate_environment(bad,4)
    print("ENVIRONMENT CONTRACT V2.1 PHASE3 SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("init");p.add_argument("episode_dir");p.add_argument("--force",action="store_true")
    p=sub.add_parser("verify");p.add_argument("episode_dir")
    p=sub.add_parser("resolve-frame");p.add_argument("episode_dir");p.add_argument("--frame",type=int,required=True);p.add_argument("--json",action="store_true")
    p=sub.add_parser("show");p.add_argument("episode_dir")
    sub.add_parser("self-test")
    a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=resolve_ep(a.episode_dir)
    if a.cmd=="init":return init_contract(ep,a.force)
    if a.cmd=="verify":
        errs=verify(ep)
        if errs:
            [print("FAIL:",e) for e in errs];return 2
        print("ENVIRONMENT CONTRACT VERIFIED");return 0
    if a.cmd=="show":
        env,d=current_contract(ep);print(json.dumps({"environment_contract":env,"frame_directives":d},ensure_ascii=False,indent=2));return 0
    row=resolve_frame(ep,a.frame)
    print(json.dumps(row,ensure_ascii=False,indent=2) if a.json else f"{row['frame']} {row['directive'].get('frame_mode')} impact={row['directive'].get('impact_level')} env={row['environment'].get('condition')}")
    return 0

if __name__=="__main__":raise SystemExit(main())
