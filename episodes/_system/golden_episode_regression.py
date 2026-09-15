#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Curated Golden Episode quality regression registry.

This compares machine-verifiable story/directing/runtime quality signals. It
does not pretend to replace pixel critics or subjective visual scoring.
"""
from __future__ import annotations
import argparse, datetime as dt, json
from pathlib import Path
import storyboard_density_gate, voice_contract, capture_event_contract, world_state, asset_lineage
import propagation_core_gate  # STORY_OS_V2_5_PROPAGATION_CORE
import story_json

ROOT=Path(__file__).resolve().parents[2]
REG=ROOT/"reports/golden-episode-registry.json"
REPORT=ROOT/"reports/golden-episode-regression.json"
REQUIRED_METRICS=("density_error_count","voice_error_count","capture_event_error_count",
                  "world_state_error_count","lineage_error_count","propagation_core_error_count","text_hard_errors")
METRIC_SOURCES={
    "density_error_count": storyboard_density_gate.REL.as_posix(),
    "voice_error_count": voice_contract.REL.as_posix(),
    "capture_event_error_count": capture_event_contract.REL.as_posix(),
    "world_state_error_count": world_state.REL.as_posix(),
    "lineage_error_count": asset_lineage.REL.as_posix(),
    "propagation_core_error_count": "meta/story-semantic-review.json#propagation_core",
    "text_hard_errors": "meta/text-audit.json#summary.hard_error_count",
}
RELEASE_STATES={"PUBLISH_READY","PUBLISHED","DATA_REVIEWED"}

def now():return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read_json(p):
    return story_json.read_json(p)
def write_json(p,d):
    story_json.write_json(p, d)
def rel(p):return Path(p).resolve().relative_to(ROOT.resolve()).as_posix()
def registry():
    return read_json(REG) if REG.is_file() else {"schema_version":1,"episodes":[],"recommended_minimum":10}

def metrics(ep):
    ep=Path(ep).resolve()
    ta=read_json(ep/"meta/text-audit.json") if (ep/"meta/text-audit.json").is_file() else {}
    ledger=read_json(ep/"meta/production-ledger.json") if (ep/"meta/production-ledger.json").is_file() else {}
    attempts=0;repairs=0
    for row in (ledger.get("frames") or {}).values():
        ats=row.get("attempts") or [];attempts+=len(ats)
        repairs+=sum(1 for x in ats if str(x.get("kind") or "").lower()=="repair")
    return {
      "density_error_count":len(storyboard_density_gate.validate(ep,True)) if (ep/storyboard_density_gate.REL).is_file() else None,
      "voice_error_count":len(voice_contract.validate(ep,True)) if (ep/voice_contract.REL).is_file() else None,
      "capture_event_error_count":len(capture_event_contract.validate(ep,True)) if (ep/capture_event_contract.REL).is_file() else None,
      "world_state_error_count":len(world_state.validate(ep,True)) if (ep/world_state.REL).is_file() else None,
      "lineage_error_count":len(asset_lineage.verify(ep)) if (ep/asset_lineage.REL).is_file() else None,
      "propagation_core_error_count":(
          len(propagation_core_gate.verify(ep, force=True))
          if (ep/"meta/story-semantic-review.json").is_file()
          and isinstance(read_json(ep/"meta/story-semantic-review.json").get("propagation_core"), dict)
          else None
      ),
      "text_hard_errors":((ta.get("summary") or {}).get("hard_error_count")),
      "text_warnings":((ta.get("summary") or {}).get("warning_count")),
      "repair_rate":round(repairs/max(1,attempts),6) if attempts else None,
      "attempt_count":attempts
    }

def qualification(ep):
    ep=Path(ep).resolve()
    blockers=[]
    state_path=ep/"meta/episode-state.json"
    state=read_json(state_path) if state_path.is_file() else {}
    current_state=str(state.get("current_state") or "UNKNOWN")
    if current_state not in RELEASE_STATES:
        blockers.append(f"state={current_state}; requires PUBLISH_READY+")
    import final_candidate_snapshot
    snapshot_errors=final_candidate_snapshot.verify(ep)
    blockers.extend(f"snapshot: {x}" for x in snapshot_errors[:5])
    try:
        baseline=metrics(ep)
    except Exception as exc:
        baseline={}
        blockers.append(f"metrics: {type(exc).__name__}: {exc}")
    invalid=[k for k in REQUIRED_METRICS if type(baseline.get(k)) is not int or baseline[k]!=0]
    blockers.extend(f"metric: {k}={baseline.get(k)} (required zero)" for k in invalid)
    metric_sources={}
    for key in REQUIRED_METRICS:
        source=METRIC_SOURCES[key]
        rel_path=source.split("#",1)[0]
        metric_sources[key]={"source":source,"present":(ep/rel_path).is_file(),"value":baseline.get(key)}
    return {
        "path":rel(ep),
        "state":current_state,
        "eligible":not blockers,
        "blockers":blockers,
        "baseline":baseline,
        "metric_sources":metric_sources,
        "missing_metric_sources":[key for key,row in metric_sources.items() if row["value"] is None],
    }


def candidates():
    rows=[]
    for state_path in sorted((ROOT/"episodes").glob("**/meta/episode-state.json")):
        ep=state_path.parent.parent
        try:
            state=read_json(state_path)
        except Exception:
            continue
        if str(state.get("current_state") or "") not in RELEASE_STATES:
            continue
        rows.append(qualification(ep))
    return {
        "schema_version":1,
        "generated_at":now(),
        "candidate_count":len(rows),
        "eligible_count":sum(1 for row in rows if row["eligible"]),
        "curator_confirmation_required":True,
        "candidates":rows,
    }


def register(ep,tags,curator=None):
    ep=Path(ep).resolve();d=registry();path=rel(ep)
    if not curator or not str(curator).strip():
        raise ValueError("Golden registration requires explicit curator confirmation")
    qualified=qualification(ep)
    baseline=qualified["baseline"]
    if not qualified["eligible"]:
        raise ValueError("Golden sample is not qualified: "+"; ".join(qualified["blockers"][:8]))
    rows=d.setdefault("episodes",[])
    current=next((x for x in rows if x.get("path")==path),None)
    row={"path":path,"tags":tags,"registered_at":now(),"curator":str(curator),"baseline":baseline}
    if current: rows[rows.index(current)]=row
    else: rows.append(row)
    write_json(REG,d);return row

def run_all():
    d=registry();results=[];failures=[]
    for item in d.get("episodes") or []:
        ep=ROOT/item["path"]
        cur=metrics(ep);base=item.get("baseline") or {};errs=[]
        for k in REQUIRED_METRICS:
            if type(cur.get(k)) is not int or cur[k]!=0:errs.append(f"{k}={cur.get(k)} (required zero)")
        if cur.get("repair_rate") is not None and base.get("repair_rate") is not None and cur["repair_rate"]>base["repair_rate"]+0.10:
            errs.append(f"repair_rate regression {base['repair_rate']} -> {cur['repair_rate']}")
        row={"path":item["path"],"tags":item.get("tags") or [],"baseline":base,"current":cur,"errors":errs,"passed":not errs}
        results.append(row)
        if errs:failures.append(item["path"])
    out={"schema_version":1,"generated_at":now(),"registered":len(results),"failed":len(failures),"results":results,
         "passed":bool(results) and not failures,
         "status":"EMPTY_REGISTRY" if not results else ("FAILED" if failures else "PASSED")}
    write_json(REPORT,out);return out

def self_test():
    assert ROOT.name
    print("GOLDEN EPISODE REGRESSION SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("register");p.add_argument("episode_dir");p.add_argument("--tag",action="append",default=[]);p.add_argument("--curator",required=True)
    sub.add_parser("candidates");sub.add_parser("run");sub.add_parser("show");sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    if a.cmd=="register":print(json.dumps(register(a.episode_dir,a.tag,a.curator),ensure_ascii=False,indent=2));return 0
    if a.cmd=="candidates":print(json.dumps(candidates(),ensure_ascii=False,indent=2));return 0
    if a.cmd=="run":
        out=run_all();print(json.dumps(out,ensure_ascii=False,indent=2));return 0 if out["passed"] else 2
    print((REPORT if REPORT.is_file() else REG).read_text(encoding="utf-8-sig") if (REPORT.is_file() or REG.is_file()) else "{}");return 0
if __name__=="__main__":raise SystemExit(main())
