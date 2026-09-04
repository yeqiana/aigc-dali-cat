#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-soft Episode performance telemetry for Story OS V2.1.

Telemetry is NOT creative authority and NEVER blocks a stage transition.
All durations are wall-clock observations. Resource-time fields such as
image_backend_seconds may overlap stage wall time and must not be summed
with stage totals as if they were independent.
"""
from __future__ import annotations
import argparse, datetime as dt, json, math, os, statistics, uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REL=Path("meta/episode-performance-ledger.json")
REPORT_REL=Path("reports/story-os-performance-summary.json")
STAGE_NAMES={"CREATIVE_STORY","PREIMAGE_COMPILE","VISUAL_LOCK","PRODUCTION","RELEASE","FULL_AUTO_LEGACY","VISUAL_LOCK_BASELINE_REVIEW"}

def now_dt():
    return dt.datetime.now(dt.timezone.utc).astimezone()
def now():
    return now_dt().isoformat(timespec="milliseconds")
def parse_ts(raw):
    if not raw:return None
    try:return dt.datetime.fromisoformat(str(raw))
    except Exception:return None
def seconds_between(a,b):
    aa=parse_ts(a);bb=parse_ts(b)
    if not aa or not bb:return None
    return max(0.0,(bb-aa).total_seconds())
def read_json(p):
    d=json.loads(Path(p).read_text(encoding="utf-8-sig"))
    if not isinstance(d,dict):raise ValueError(f"JSON root must be object: {p}")
    return d
def write_json(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    os.replace(tmp,p)

def _new(ep):
    return {
      "schema_version":1,
      "telemetry_only":True,
      "not_stage_gate":True,
      "fail_soft":True,
      "episode_path":Path(ep).resolve().relative_to(ROOT.resolve()).as_posix(),
      "started_at":now(),
      "updated_at":now(),
      "finalized_at":None,
      "final_status":None,
      "total_wall_seconds":None,
      "stages":{},
      "named_spans":{},
      "state_transitions":[],
      "image_attempts":[],
      "summary":{}
    }

def load(ep,create=True):
    ep=Path(ep).resolve();p=ep/REL
    if p.is_file():
        try:return read_json(p)
        except Exception:
            if not create:raise
    d=_new(ep)
    if create:write_json(p,d)
    return d

def save(ep,d):
    d["updated_at"]=now()
    _refresh_summary(d)
    write_json(Path(ep).resolve()/REL,d)
    return d

def safe_start_episode(ep,source="runtime"):
    try:
        d=load(ep,True)
        d.setdefault("start_sources",[])
        if source not in d["start_sources"]:d["start_sources"].append(source)
        save(ep,d);return True
    except Exception:return False

def begin_stage(ep,stage,source="scoped_worker",metadata=None):
    stage=str(stage).upper()
    d=load(ep,True);rid=uuid.uuid4().hex[:12];at=now()
    row={"run_id":rid,"started_at":at,"ended_at":None,"duration_seconds":None,
         "status":"RUNNING","source":source,"metadata":metadata or {}}
    d.setdefault("stages",{}).setdefault(stage,{"runs":[]})["runs"].append(row)
    save(ep,d);return rid

def end_stage(ep,stage,run_id=None,status="PASS",metadata=None):
    stage=str(stage).upper();d=load(ep,True);runs=(d.setdefault("stages",{}).setdefault(stage,{"runs":[]})["runs"])
    row=None
    if run_id:row=next((x for x in reversed(runs) if x.get("run_id")==run_id),None)
    if row is None:row=next((x for x in reversed(runs) if x.get("status")=="RUNNING"),None)
    if row is None:
        row={"run_id":run_id or uuid.uuid4().hex[:12],"started_at":now(),"source":"recovered","metadata":{}}
        runs.append(row)
    ended=now();row["ended_at"]=ended;row["duration_seconds"]=seconds_between(row.get("started_at"),ended) or 0.0
    row["status"]=str(status);row.setdefault("metadata",{}).update(metadata or {})
    save(ep,d);return row

def safe_begin_stage(ep,stage,source="scoped_worker",metadata=None):
    try:return begin_stage(ep,stage,source,metadata)
    except Exception:return None
def safe_end_stage(ep,stage,run_id=None,status="PASS",metadata=None):
    try:end_stage(ep,stage,run_id,status,metadata);return True
    except Exception:return False

def begin_named_span(ep,name,source="runtime",metadata=None):
    d=load(ep,True);key=str(name).upper();bucket=d.setdefault("named_spans",{}).setdefault(key,{"runs":[]})
    running=next((x for x in reversed(bucket["runs"]) if x.get("status")=="RUNNING"),None)
    if running:return running["run_id"]
    rid=uuid.uuid4().hex[:12]
    bucket["runs"].append({"run_id":rid,"started_at":now(),"ended_at":None,"duration_seconds":None,
                           "status":"RUNNING","source":source,"metadata":metadata or {}})
    save(ep,d);return rid

def end_named_span(ep,name,status="PASS",metadata=None):
    d=load(ep,True);key=str(name).upper();runs=(d.setdefault("named_spans",{}).setdefault(key,{"runs":[]})["runs"])
    row=next((x for x in reversed(runs) if x.get("status")=="RUNNING"),None)
    if row is None:return None
    ended=now();row["ended_at"]=ended;row["duration_seconds"]=seconds_between(row.get("started_at"),ended) or 0.0
    row["status"]=status;row.setdefault("metadata",{}).update(metadata or {})
    save(ep,d);return row

def safe_begin_named_span(ep,name,source="runtime",metadata=None):
    try:return begin_named_span(ep,name,source,metadata)
    except Exception:return None
def safe_end_named_span(ep,name,status="PASS",metadata=None):
    try:end_named_span(ep,name,status,metadata);return True
    except Exception:return False

def record_state_transition(ep,source_state,target_state,at=None):
    d=load(ep,True)
    row={"from":str(source_state),"to":str(target_state),"at":at or now()}
    existing=d.setdefault("state_transitions",[])
    if not any(x.get("from")==row["from"] and x.get("to")==row["to"] and x.get("at")==row["at"] for x in existing):
        existing.append(row)
    save(ep,d)
    if str(target_state)=="PUBLISH_READY":finalize(ep,"PUBLISH_READY")
    return row

def safe_record_state_transition(ep,source_state,target_state,at=None):
    try:record_state_transition(ep,source_state,target_state,at);return True
    except Exception:return False

def record_image_attempt(ep,*,frame,scope,kind,status,model=None,attempt=1,
                         started_at=None,ended_at=None,elapsed_seconds=None,
                         queue_item_id=None,error_code=None):
    d=load(ep,True);ended_at=ended_at or now()
    if elapsed_seconds is None:elapsed_seconds=seconds_between(started_at,ended_at)
    row={
      "event_id":uuid.uuid4().hex[:12],"frame":f"{int(frame):02d}",
      "scope":str(scope or "unknown"),"kind":str(kind or "original"),"status":str(status or "unknown"),
      "model":model,"attempt":int(attempt or 1),"started_at":started_at,"ended_at":ended_at,
      "elapsed_seconds":float(elapsed_seconds) if isinstance(elapsed_seconds,(int,float)) else None,
      "queue_item_id":queue_item_id,"error_code":error_code
    }
    d.setdefault("image_attempts",[]).append(row);save(ep,d);return row

def safe_record_image_attempt(ep,**kwargs):
    try:record_image_attempt(ep,**kwargs);return True
    except Exception:return False

def observe_checkpoint(ep,state):
    try:
        state=str(state)
        d=load(ep,True)
        d.setdefault("checkpoint_events",[]).append({"state":state,"at":now()})
        save(ep,d)
        if state=="ORCHESTRATOR_STARTED":
            begin_stage(ep,"FULL_AUTO_LEGACY",source="codex_auto_orchestrator")
        elif state in {"FULL_AUTO_COMPLETE","MINIMAL_CLOSURE_COMPLETE"}:
            end_stage(ep,"FULL_AUTO_LEGACY",status="PASS")
            finalize(ep,"PUBLISH_READY")
        elif state in {"FULL_AUTO_BLOCKED","FULL_AUTO_PAUSED","ORCHESTRATOR_BLOCKED"}:
            end_stage(ep,"FULL_AUTO_LEGACY",status=state)
        return True
    except Exception:return False

def finalize(ep,status="COMPLETE"):
    ep=Path(ep).resolve();d=load(ep,True);ended=now()
    d["finalized_at"]=ended;d["final_status"]=status
    d["total_wall_seconds"]=seconds_between(d.get("started_at"),ended)
    save(ep,d)
    try:rebuild_report(ROOT)
    except Exception:pass
    return d

def safe_finalize(ep,status="COMPLETE"):
    try:finalize(ep,status);return True
    except Exception:return False

def _run_total(bucket):
    vals=[]
    for row in (bucket or {}).get("runs") or []:
        v=row.get("duration_seconds")
        if isinstance(v,(int,float)):vals.append(float(v))
    return round(sum(vals),3)

# STORY_OS_V211_RUNTIME_CLOSURE_R3: overlap-aware end-to-end critical-path telemetry.
def _interval_union_seconds(intervals):
    rows=[]
    for a,b in intervals:
        aa=parse_ts(a);bb=parse_ts(b)
        if aa and bb and bb>=aa:rows.append((aa,bb))
    if not rows:return 0.0
    rows.sort(key=lambda x:x[0]);start,end=rows[0];total=0.0
    for a,b in rows[1:]:
        if a<=end:
            if b>end:end=b
        else:
            total+=(end-start).total_seconds();start,end=a,b
    total+=(end-start).total_seconds()
    return round(max(0.0,total),3)

def _critical_path_summary(d):
    started=parse_ts(d.get("started_at"));finalized=parse_ts(d.get("finalized_at"))
    observed=[]
    chain=[]
    for stage,bucket in (d.get("stages") or {}).items():
        for row in (bucket or {}).get("runs") or []:
            a=row.get("started_at");b=row.get("ended_at")
            if a and b:observed.append((a,b))
            chain.append({"stage":stage,"run_id":row.get("run_id"),"status":row.get("status"),
                          "started_at":a,"ended_at":b,"duration_seconds":row.get("duration_seconds")})
    image_intervals=[]
    image_resource=0.0
    for row in d.get("image_attempts") or []:
        a=row.get("started_at");b=row.get("ended_at")
        if a and b:image_intervals.append((a,b));observed.append((a,b))
        if isinstance(row.get("elapsed_seconds"),(int,float)):image_resource+=float(row["elapsed_seconds"])
    if not finalized:
        ends=[parse_ts(b) for _,b in observed if parse_ts(b)]
        finalized=max(ends) if ends else None
    critical=max(0.0,(finalized-started).total_seconds()) if started and finalized else None
    image_union=_interval_union_seconds(image_intervals)
    chain.sort(key=lambda x:str(x.get("started_at") or ""))
    return {
      "kind":"observed_end_to_end_wall",
      "critical_path_seconds":round(critical,3) if critical is not None else None,
      "image_backend_union_wall_seconds":image_union,
      "image_backend_resource_seconds":round(image_resource,3),
      "parallel_saved_seconds":round(max(0.0,image_resource-image_union),3),
      "dependency_chain":chain,
      "note":"End-to-end wall is the user-visible critical path; image resource time is overlap-aware and is not added to stage wall."
    }

def _refresh_summary(d):
    stages={k:{"wall_seconds":_run_total(v),"runs":len(v.get("runs") or [])} for k,v in (d.get("stages") or {}).items()}
    spans={k:{"wall_seconds":_run_total(v),"runs":len(v.get("runs") or [])} for k,v in (d.get("named_spans") or {}).items()}
    imgs=d.get("image_attempts") or []
    completed=[x for x in imgs if str(x.get("status") or "") in {"generated","PASSED","PASS","success"}]
    repair=[x for x in imgs if str(x.get("kind") or "")=="repair"]
    tech=[x for x in imgs if "tech" in str(x.get("status") or "").lower() or x.get("error_code")]
    vals=[float(x["elapsed_seconds"]) for x in imgs if isinstance(x.get("elapsed_seconds"),(int,float))]
    image_backend=sum(vals)
    critical_path=_critical_path_summary(d)  # STORY_OS_V211_RUNTIME_CLOSURE_R3
    d["summary"]={
      "stage_wall":stages,
      "named_span_wall":spans,
      "critical_path":critical_path,
      "images":{
        "attempts":len(imgs),"successful_attempts":len(completed),"repair_attempts":len(repair),
        "technical_failures_or_retries":len(tech),
        "image_backend_seconds":round(image_backend,3),
        "average_attempt_seconds":round(statistics.mean(vals),3) if vals else None,
        "max_attempt_seconds":round(max(vals),3) if vals else None,
      },
      "note":"stage wall time and image backend resource time can overlap; do not add them together."
    }

def episode_summary(ep):
    d=load(ep,False);_refresh_summary(d)
    return {"episode_path":d.get("episode_path"),"started_at":d.get("started_at"),
            "finalized_at":d.get("finalized_at"),"final_status":d.get("final_status"),
            "total_wall_seconds":d.get("total_wall_seconds"),**(d.get("summary") or {})}

def percentile(values,p):
    vals=sorted(float(x) for x in values)
    if not vals:return None
    if len(vals)==1:return vals[0]
    pos=(len(vals)-1)*p;lo=math.floor(pos);hi=math.ceil(pos)
    if lo==hi:return vals[lo]
    return vals[lo]+(vals[hi]-vals[lo])*(pos-lo)

def rebuild_report(root=ROOT):
    root=Path(root).resolve();rows=[]
    for p in root.rglob(REL.as_posix()):
        if "_system" in p.parts:continue
        try:
            d=read_json(p);_refresh_summary(d)
            if isinstance(d.get("total_wall_seconds"),(int,float)):
                rows.append({"episode":p.parent.parent.relative_to(root).as_posix(),
                             "total_wall_seconds":float(d["total_wall_seconds"]),
                             "final_status":d.get("final_status"),
                             "images":(d.get("summary") or {}).get("images") or {},
                             "stage_wall":(d.get("summary") or {}).get("stage_wall") or {}})
        except Exception:continue
    totals=[x["total_wall_seconds"] for x in rows]
    report={"schema_version":1,"generated_at":now(),"sample_size":len(rows),
            "p50_total_seconds":round(percentile(totals,0.50),3) if totals else None,
            "p90_total_seconds":round(percentile(totals,0.90),3) if totals else None,
            "average_total_seconds":round(statistics.mean(totals),3) if totals else None,
            "episodes":rows,
            "telemetry_policy":"fail-soft; never a Story/Release gate"}
    write_json(root/REPORT_REL,report);return report

def self_test():
    assert abs(percentile([10,20,30],0.5)-20)<0.001
    assert REL.as_posix()=="meta/episode-performance-ledger.json"
    assert _interval_union_seconds([])==0.0
    print("EPISODE PERFORMANCE + R3 CRITICAL PATH SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("show");p.add_argument("episode_dir")
    p=sub.add_parser("finalize");p.add_argument("episode_dir");p.add_argument("--status",default="COMPLETE")
    sub.add_parser("rebuild-report")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    if a.cmd=="rebuild-report":print(json.dumps(rebuild_report(ROOT),ensure_ascii=False,indent=2));return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="finalize":print(json.dumps(finalize(ep,a.status),ensure_ascii=False,indent=2));return 0
    print(json.dumps(episode_summary(ep),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())

# STORY_OS_V211_RUNTIME_CLOSURE_R31
