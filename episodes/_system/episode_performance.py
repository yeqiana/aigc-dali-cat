#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-soft Episode performance telemetry for Story OS V2.1.

Telemetry is NOT creative authority and NEVER blocks a stage transition.
All durations are wall-clock observations. Resource-time fields such as
image_backend_seconds may overlap stage wall time and must not be summed
with stage totals as if they were independent.
"""
from __future__ import annotations
import argparse, datetime as dt, json, math, os, statistics, tempfile, uuid
from pathlib import Path
import story_json
import runtime_observability

ROOT=Path(__file__).resolve().parents[2]
REL=runtime_observability.EPISODE_PERFORMANCE_REL
REPORT_REL=Path("reports/story-os-performance-summary.json")
STAGE_NAMES={"CREATIVE_STORY","PREIMAGE_COMPILE","VISUAL_LOCK","PRODUCTION","RELEASE","FULL_AUTO_LEGACY","VISUAL_LOCK_BASELINE_REVIEW"}
EXECUTION_STATES={"ACTIVE","HOST_WAIT","USER_WAIT","IDLE"}

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
    return story_json.read_json(p)
def write_json(p,d):
    story_json.write_json(p, d)

def _new(ep):
    return {
      "schema_version":1,
      "kind":"episode_performance",
      "generated_at":now(),
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
      "execution_sessions":[],
      "summary":{}
    }

def load(ep,create=True):
    ep=Path(ep).resolve();p=ep/REL
    try:
        loaded=runtime_observability.read_summary(ep,REL,default={})
        if loaded:return loaded
    except Exception:
        if not create:raise
    d=_new(ep)
    if create:runtime_observability.write_summary(ep,REL,kind="episode_performance",payload=d)
    return d

def save(ep,d):
    d["updated_at"]=now()
    _refresh_summary(d)
    runtime_observability.write_summary(Path(ep).resolve(),REL,kind="episode_performance",payload=d)
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
    d=load(ep,True);bucket=d.setdefault("stages",{}).setdefault(stage,{"runs":[]})
    # STORY_OS_V211_UNCLOSED_SPAN_REUSE: one row per logical attempt, not per pass.
    # A scoped_model step hands back to the host (HOST_WAIT, rc=20) many times before
    # it finishes. Reusing the still-open run_id keeps runs[-1] stable across those
    # round-trips (critic_runtime_v211 reads it as the visual-lock binding) and stops
    # the ledger filling with rows nothing ever closes. Mirrors begin_named_span().
    running=next((x for x in reversed(bucket["runs"]) if x.get("status")=="RUNNING"),None)
    if running:return running["run_id"]
    rid=uuid.uuid4().hex[:12];at=now()
    row={"run_id":rid,"started_at":at,"ended_at":None,"duration_seconds":None,
         "status":"RUNNING","source":source,"metadata":metadata or {}}
    bucket["runs"].append(row)
    save(ep,d);return rid

def end_stage(ep,stage,run_id=None,status="PASS",metadata=None):
    stage=str(stage).upper();d=load(ep,True);runs=(d.setdefault("stages",{}).setdefault(stage,{"runs":[]})["runs"])
    row=None
    if run_id:
        row=next((x for x in reversed(runs) if x.get("run_id")==run_id),None)
    else:
        row=next((x for x in reversed(runs) if x.get("status")=="RUNNING"),None)
    # STORY_OS_V211_NO_FABRICATED_SPAN: no match means no span was ever opened for
    # this attempt, so there is nothing to close. Never invent a row -- a fabricated
    # row carries started_at=now() and reports a duration belonging to no execution.
    # An explicit run_id must not fall back to an unrelated open row either: that
    # merge closed a span opened hours earlier and inflated stage walls past 100h.
    # fail-soft no-op, same contract as safe_end_stage().
    if row is None:return None
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

def review_span_name(review_type,attempt,lane=None):
    """Build the named-span key for one review lane and attempt.

    ``lane`` separates review entry points that share a kind and attempt number
    (for example an incremental PATCH and a bounded final-patch review) so two
    unrelated reviews cannot merge into one measurement bucket.
    """
    kind=str(review_type or "").strip().upper()
    if kind not in {"FULL","PATCH"}:raise ValueError("review_type must be FULL or PATCH")
    token="".join(ch if ch.isalnum() else "_" for ch in str(lane or "").strip().upper()).strip("_")
    return f"REVIEW_{kind}_{token}_{max(1,int(attempt or 1))}" if token else f"REVIEW_{kind}_{max(1,int(attempt or 1))}"

def safe_begin_review_span(ep,review_type,attempt,metadata=None,lane=None):
    try:
        if not Path(ep).is_dir():return None
        name=review_span_name(review_type,attempt,lane)
        return safe_begin_named_span(ep,name,source="frame_review",metadata={
            "review_type":str(review_type).upper(),"attempt":max(1,int(attempt or 1)),
            "review_lane":str(lane).upper() if lane else None,**(metadata or {})})
    except Exception:return None

def safe_update_named_span(ep,name,metadata=None):
    """Best-effort metadata update on the currently open span."""
    try:
        if not Path(ep).is_dir():return False
        d=load(ep,True);bucket=(d.get("named_spans") or {}).get(str(name),{})
        row=next((x for x in reversed(bucket.get("runs") or []) if x.get("status")=="RUNNING"),None)
        if row is None:return False
        row.setdefault("metadata",{}).update(metadata or {})
        save(ep,d);return True
    except Exception:return False

def safe_end_review_span(ep,review_type,attempt,status="PASS",metadata=None,lane=None):
    try:
        if not Path(ep).is_dir():return False
        name=review_span_name(review_type,attempt,lane)
        bucket=(load(ep,True).get("named_spans") or {}).get(name) or {}
        if not any(x.get("status")=="RUNNING" for x in bucket.get("runs") or []):return False
        return safe_end_named_span(ep,name,status=status,metadata=metadata)
    except Exception:return False

# A span closed at finalize never produced a verdict, so it belongs with the
# deferred/blocked rows instead of being reported as a content failure.
REVIEW_PASS_STATUSES=frozenset({"PASS","REUSED"})
REVIEW_NOT_EXECUTED_STATUSES=frozenset({"DEFERRED","BLOCKED","CLOSED_AT_FINALIZE"})

def review_status_for_code(return_code):
    """Map a review return code to the span status recorded in telemetry."""
    try:code=int(return_code)
    except (TypeError,ValueError):return "FAILED"
    if code==0:return "PASS"
    if code==3:return "DEFERRED"
    return "FAILED"

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
    rows=d.setdefault("image_attempts",[])
    existing=None
    if queue_item_id:
        existing=next((x for x in reversed(rows)
                       if str(x.get("queue_item_id") or "")==str(queue_item_id)
                       and int(x.get("attempt") or 0)==int(row["attempt"])),None)
    if existing is not None:
        event_id=existing.get("event_id")
        existing.update(row)
        if event_id:existing["event_id"]=event_id
        row=existing
    else:
        rows.append(row)
    save(ep,d);return row

def record_queue_image_attempt(ep,item,*,status,error_code=None,ended_at=None):
    """Record one terminal scheduler/import attempt from its queue contract."""
    return record_image_attempt(
        ep,frame=int(item["frame"]),scope=item.get("scope"),kind=item.get("kind"),
        status=status,model=item.get("model"),attempt=max(1,int(item.get("attempts") or 0)),
        started_at=item.get("started_at"),ended_at=ended_at or item.get("completed_at") or now(),
        queue_item_id=item.get("id"),error_code=error_code)

def safe_record_queue_image_attempt(ep,item,**kwargs):
    try:record_queue_image_attempt(ep,item,**kwargs);return True
    except Exception:return False

def safe_record_image_attempt(ep,**kwargs):
    try:record_image_attempt(ep,**kwargs);return True
    except Exception:return False

def _close_execution_state(session, ended):
    states=session.get("states") or []
    row=next((x for x in reversed(states) if not x.get("ended_at")),None)
    if row is None:return None
    row["ended_at"]=ended
    row["duration_seconds"]=seconds_between(row.get("started_at"),ended) or 0.0
    return row

def _close_execution_session(session, ended, status):
    _close_execution_state(session,ended)
    session["ended_at"]=ended
    session["duration_seconds"]=seconds_between(session.get("started_at"),ended) or 0.0
    session["status"]=str(status)
    return session

def begin_execution_session(ep,source="runtime",session_id=None,metadata=None,at=None):
    d=load(ep,True);at=at or now();sessions=d.setdefault("execution_sessions",[])
    sid=str(session_id or uuid.uuid4().hex[:12])
    existing=next((x for x in reversed(sessions) if str(x.get("session_id") or "")==sid),None)
    if existing and not existing.get("ended_at"):return sid
    for old in reversed(sessions):
        if not old.get("ended_at"):
            _close_execution_session(old,at,"HANDOFF_TO_NEXT_SESSION")
            break
    sessions.append({"session_id":sid,"source":str(source),"started_at":at,"ended_at":None,
                     "duration_seconds":None,"status":"RUNNING","metadata":metadata or {},"states":[]})
    save(ep,d);return sid

def transition_execution_state(ep,state,*,session_id=None,source="runtime",metadata=None,at=None):
    state=str(state).upper()
    if state not in EXECUTION_STATES:raise ValueError("invalid execution state: "+state)
    d=load(ep,True);at=at or now();sessions=d.setdefault("execution_sessions",[])
    session=None
    if session_id is not None:
        session=next((x for x in reversed(sessions) if str(x.get("session_id") or "")==str(session_id) and not x.get("ended_at")),None)
    if session is None:session=next((x for x in reversed(sessions) if not x.get("ended_at")),None)
    if session is None:
        sid=begin_execution_session(ep,source=source,session_id=session_id,at=at)
        d=load(ep,True);sessions=d.setdefault("execution_sessions",[])
        session=next(x for x in reversed(sessions) if str(x.get("session_id") or "")==sid and not x.get("ended_at"))
    states=session.setdefault("states",[])
    current=next((x for x in reversed(states) if not x.get("ended_at")),None)
    if current and current.get("state")==state:
        current.setdefault("metadata",{}).update(metadata or {});save(ep,d);return current
    if current:_close_execution_state(session,at)
    row={"state":state,"started_at":at,"ended_at":None,"duration_seconds":None,
         "source":str(source),"metadata":metadata or {}}
    states.append(row);save(ep,d);return row

def finish_execution_session(ep,session_id=None,status="COMPLETE",at=None):
    d=load(ep,True);at=at or now();sessions=d.setdefault("execution_sessions",[])
    session=None
    if session_id is not None:
        session=next((x for x in reversed(sessions) if str(x.get("session_id") or "")==str(session_id) and not x.get("ended_at")),None)
    if session is None:session=next((x for x in reversed(sessions) if not x.get("ended_at")),None)
    if session is None:return None
    _close_execution_session(session,at,status);save(ep,d);return session

def safe_begin_execution_session(ep,**kwargs):
    try:return begin_execution_session(ep,**kwargs)
    except Exception:return None
def safe_transition_execution_state(ep,state,**kwargs):
    try:transition_execution_state(ep,state,**kwargs);return True
    except Exception:return False
def safe_finish_execution_session(ep,**kwargs):
    try:finish_execution_session(ep,**kwargs);return True
    except Exception:return False

def execution_state_for_result(return_code,action=None):
    name=str((action or {}).get("action") or "") if isinstance(action,dict) else ""
    if int(return_code)==22 or name=="USER_DECISION_REQUIRED":return "USER_WAIT"
    if int(return_code)==20:return "HOST_WAIT"
    return "IDLE"

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

def _close_open_telemetry(d,ended):
    """Close dangling telemetry spans without turning them into PASS evidence."""
    for section in ("stages","named_spans"):
        for bucket in (d.get(section) or {}).values():
            for row in (bucket or {}).get("runs") or []:
                if row.get("status")!="RUNNING":continue
                row["ended_at"]=ended
                row["duration_seconds"]=seconds_between(row.get("started_at"),ended) or 0.0
                row["status"]="CLOSED_AT_FINALIZE"
                row.setdefault("metadata",{})["auto_closed_at_finalize"]=True
    for session in d.get("execution_sessions") or []:
        if not session.get("ended_at"):
            _close_execution_session(session,ended,"CLOSED_AT_FINALIZE")

def finalize(ep,status="COMPLETE"):
    ep=Path(ep).resolve();d=load(ep,True);ended=now()
    _close_open_telemetry(d,ended)
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

def _run_wall(bucket):
    intervals=[]
    for row in (bucket or {}).get("runs") or []:
        a=row.get("started_at");b=row.get("ended_at")
        if a and b:intervals.append((a,b))
    return _interval_union_seconds(intervals)

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

def _execution_summary(d):
    sessions=d.get("execution_sessions") or []
    observed_end=d.get("updated_at") or now()
    aggregate={state:[] for state in EXECUTION_STATES}
    def one(session):
        by_state={state:[] for state in EXECUTION_STATES}
        all_intervals=[]
        for row in session.get("states") or []:
            state=str(row.get("state") or "")
            if state not in EXECUTION_STATES:continue
            end=row.get("ended_at") or observed_end
            if row.get("started_at") and end:
                interval=(row["started_at"],end);by_state[state].append(interval);aggregate[state].append(interval);all_intervals.append(interval)
        out={state.lower()+"_seconds":_interval_union_seconds(by_state[state]) for state in sorted(EXECUTION_STATES)}
        out["wall_seconds"]=_interval_union_seconds(all_intervals)
        out.update({"session_id":session.get("session_id"),"source":session.get("source"),"status":session.get("status")})
        return out
    session_summaries=[one(session) for session in sessions]
    latest=session_summaries[-1] if session_summaries else None
    total={state.lower()+"_seconds":_interval_union_seconds(aggregate[state]) for state in sorted(EXECUTION_STATES)}
    return {"session_count":len(sessions),"latest":latest,"aggregate":total,
            "active_wall_seconds":None if latest is None else latest["active_seconds"]}

def _overlap_union_seconds(intervals, state_intervals):
    intersections=[]
    for start,end in intervals:
        a=parse_ts(start);b=parse_ts(end)
        if not a or not b or b<a:continue
        for state_start,state_end in state_intervals:
            c=parse_ts(state_start);e=parse_ts(state_end)
            if not c or not e or e<c:continue
            left=max(a,c);right=min(b,e)
            if right>left:intersections.append((left.isoformat(),right.isoformat()))
    return _interval_union_seconds(intersections)

def _review_summary(d):
    spans=d.get("named_spans") or {}
    if not isinstance(spans,dict):spans={}
    sessions=d.get("execution_sessions") or []
    if not isinstance(sessions,list):sessions=[]
    state_intervals={state:[] for state in EXECUTION_STATES}
    observed_end=d.get("updated_at") or now()
    for session in sessions:
        if not isinstance(session,dict):continue
        for row in session.get("states") or []:
            if not isinstance(row,dict):continue
            state=str(row.get("state") or "")
            if state not in state_intervals or not row.get("started_at"):continue
            state_intervals[state].append((row["started_at"],row.get("ended_at") or observed_end))
    result={}
    for kind in ("FULL","PATCH"):
        attempts=[];intervals=[];frame_counts=[];shard_counts=[]
        prefix=f"REVIEW_{kind}_"
        for name,bucket in spans.items():
            if not str(name).startswith(prefix):continue
            if not isinstance(bucket,dict):continue
            for row in bucket.get("runs") or []:
                if not isinstance(row,dict):continue
                attempts.append(row)
                start=row.get("started_at");end=row.get("ended_at")
                a=parse_ts(start);b=parse_ts(end)
                if a and b and b>=a:intervals.append((start,end))
                metadata=row.get("metadata") or {}
                if not isinstance(metadata,dict):metadata={}
                if isinstance(metadata.get("target_frame_count"),(int,float)):
                    frame_counts.append(float(metadata["target_frame_count"]))
                if isinstance(metadata.get("shard_count"),(int,float)):
                    shard_counts.append(float(metadata["shard_count"]))
        completed=[x for x in attempts if x.get("status")!="RUNNING" and parse_ts(x.get("started_at"))
                   and parse_ts(x.get("ended_at")) and parse_ts(x.get("ended_at"))>=parse_ts(x.get("started_at"))]
        frame_samples=sum(1 for x in attempts if isinstance((x.get("metadata") if isinstance(x.get("metadata"),dict) else {}).get("target_frame_count"),(int,float)))
        shard_samples=sum(1 for x in attempts if isinstance((x.get("metadata") if isinstance(x.get("metadata"),dict) else {}).get("shard_count"),(int,float)))
        intervals_complete=bool(attempts) and len(intervals)==len(attempts)
        state_rows=[interval for rows in state_intervals.values() for interval in rows]
        review_wall=_interval_union_seconds(intervals) if intervals_complete else None
        attributed_wall=_overlap_union_seconds(intervals,state_rows) if intervals_complete and state_rows else None
        state_status=("UNKNOWN" if not state_rows or attributed_wall is None else
                      "OK" if abs(attributed_wall-review_wall)<=0.001 else "INCOMPLETE")
        def _status(row):return str(row.get("status") or "").upper()
        passed=[x for x in completed if _status(x) in REVIEW_PASS_STATUSES]
        deferred=[x for x in completed if _status(x) in REVIEW_NOT_EXECUTED_STATUSES]
        failed=[x for x in completed if _status(x) not in REVIEW_PASS_STATUSES|REVIEW_NOT_EXECUTED_STATUSES]
        fields={"attempt_count":len(attempts) if attempts else None,
                "completed_count":len(completed) if attempts else None,
                "passed_count":len(passed) if attempts else None,
                "failed_count":len(failed) if attempts else None,
                "deferred_count":len(deferred) if attempts else None,
                "unclosed_count":sum(1 for x in attempts if x.get("status")=="RUNNING") if attempts else None,
                "target_frame_sample_count":frame_samples if attempts else None,
                "shard_sample_count":shard_samples if attempts else None,
                "target_frame_count_total":sum(frame_counts) if attempts and frame_samples==len(attempts) else None,
                "shard_count_total":sum(shard_counts) if attempts and shard_samples==len(attempts) else None,
                "wall_seconds":review_wall,
                "active_seconds":_overlap_union_seconds(intervals,state_intervals["ACTIVE"]) if state_status=="OK" else None,
                "host_wait_seconds":_overlap_union_seconds(intervals,state_intervals["HOST_WAIT"]) if state_status=="OK" else None,
                "user_wait_seconds":_overlap_union_seconds(intervals,state_intervals["USER_WAIT"]) if state_status=="OK" else None,
                "idle_seconds":_overlap_union_seconds(intervals,state_intervals["IDLE"]) if state_status=="OK" else None,
                "state_attribution_status":state_status,
                "status":("UNKNOWN" if not attempts else
                          "INCOMPLETE" if len(completed)!=len(attempts) or not intervals_complete or frame_samples!=len(attempts) or shard_samples!=len(attempts) else
                          "OK" if completed else "INCOMPLETE")}
        result[kind.lower()]=fields
    return result

def _refresh_summary(d):
    def bucket_summary(v):
        runs=v.get("runs") or []
        return {"wall_seconds":_run_wall(v),"resource_seconds":_run_total(v),"runs":len(runs),
                "unclosed_runs":sum(1 for x in runs if x.get("status")=="RUNNING"),
                "metric_kind":"elapsed_stage_span","may_include_wait":True,"not_execution_time":True}
    stages={k:bucket_summary(v) for k,v in (d.get("stages") or {}).items()}
    spans={k:bucket_summary(v) for k,v in (d.get("named_spans") or {}).items()}
    imgs=d.get("image_attempts") or []
    completed=[x for x in imgs if str(x.get("status") or "") in {"generated","PASSED","PASS","success"}]
    repair=[x for x in imgs if str(x.get("kind") or "")=="repair"]
    tech=[x for x in imgs if "tech" in str(x.get("status") or "").lower() or x.get("error_code")]
    vals=[float(x["elapsed_seconds"]) for x in imgs if isinstance(x.get("elapsed_seconds"),(int,float))]
    image_backend=sum(vals)
    critical_path=_critical_path_summary(d)  # STORY_OS_V211_RUNTIME_CLOSURE_R3
    # STORY_OS_V2_5_1_RUNTIME_FAST_PATH: advisory active-wall SLO; never a gate.
    execution_wall=_execution_summary(d)
    aggregate_execution=execution_wall.get("aggregate") or {}
    latest_execution=execution_wall.get("latest") or {}
    duration_breakdown={
      "runtime_active_seconds":aggregate_execution.get("active_seconds"),
      "host_wait_seconds":aggregate_execution.get("host_wait_seconds"),
      "user_wait_seconds":aggregate_execution.get("user_wait_seconds"),
      "idle_seconds":aggregate_execution.get("idle_seconds"),
      "latest_session_active_seconds":latest_execution.get("active_seconds"),
      "latest_session_host_wait_seconds":latest_execution.get("host_wait_seconds"),
      "latest_session_user_wait_seconds":latest_execution.get("user_wait_seconds"),
      "latest_session_idle_seconds":latest_execution.get("idle_seconds"),
      "primary_runtime_metric":"latest_session_active_seconds",
      "aggregate_scope":"all_execution_sessions_interval_union",
      "stage_wall_includes_wait":True,
      "external_host_execution_seconds":None,
      "external_host_execution_policy":"measure only explicit host start/complete evidence; never infer execution from HOST_WAIT",
      "note":"episode aggregate covers all execution sessions with interval-union de-duplication; current efficiency/SLO uses the latest session active wall. stage_wall may include HOST_WAIT and is not production execution time.",
    }
    active_wall=execution_wall.get("active_wall_seconds")
    if not isinstance(active_wall,(int,float)): active_wall=((d.get("run_wall") or {}).get("active_wall_seconds"))
    if not isinstance(active_wall,(int,float)): active_wall=d.get("total_wall_seconds")
    if isinstance(active_wall,(int,float)):
        perf_health="GREEN" if active_wall<=5400 else ("YELLOW" if active_wall<=7200 else "RED")
        performance_slo={"health":perf_health,"active_wall_seconds":round(float(active_wall),3),"green_max_seconds":5400,"yellow_max_seconds":7200,"gate":False}
    else: performance_slo={"health":"UNKNOWN","active_wall_seconds":None,"gate":False}
    d["summary"]={
      "stage_wall":stages,
      "named_span_wall":spans,
      "critical_path":critical_path,
      "execution_wall":execution_wall,
      "duration_breakdown":duration_breakdown,
      "performance_slo":performance_slo,
      "review":_review_summary(d),
      "images":{
        "attempts":len(imgs),"successful_attempts":len(completed),"repair_attempts":len(repair),
        "technical_failures_or_retries":len(tech),
        "image_backend_seconds":round(image_backend,3),
        "average_attempt_seconds":round(statistics.mean(vals),3) if vals else None,
        "max_attempt_seconds":round(max(vals),3) if vals else None,
      },
      "note":"stage/named wall_seconds are elapsed interval unions and may include HOST_WAIT; they are not production execution time. resource_seconds sum run durations and may overlap. Use duration_breakdown/execution_wall for wait attribution and do not add resource time to wall time."
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
    import episode_discovery
    root=Path(root).resolve();rows=[]
    for ep in episode_discovery.iter_episode_roots(root/"episodes"):
        p=ep/REL
        if not p.is_file():continue
        try:
            d=read_json(p);_refresh_summary(d)
            rows.append({"episode":ep.relative_to(root).as_posix(),
                             "total_wall_seconds":float(d["total_wall_seconds"]) if isinstance(d.get("total_wall_seconds"),(int,float)) else None,
                             "sample_status":"OK" if isinstance(d.get("total_wall_seconds"),(int,float)) else "INCOMPLETE",
                             "final_status":d.get("final_status"),
                             "images":(d.get("summary") or {}).get("images") or {},
                             "review":(d.get("summary") or {}).get("review") or {},
                             "duration_breakdown":(d.get("summary") or {}).get("duration_breakdown") or {},
                             "critical_path":(d.get("summary") or {}).get("critical_path") or {},
                             "stage_wall":(d.get("summary") or {}).get("stage_wall") or {}})
        except Exception:continue
    totals=[x["total_wall_seconds"] for x in rows if isinstance(x.get("total_wall_seconds"),(int,float))]
    report={"schema_version":2,"generated_at":now(),"episode_count":len(rows),"sample_size":len(totals),
            "sample_status":"NO_DATA" if not totals else ("INSUFFICIENT_SAMPLE" if len(totals)<3 else "READY"),
            "p50_total_seconds":round(percentile(totals,0.50),3) if totals else None,
            "p90_total_seconds":round(percentile(totals,0.90),3) if totals else None,
            "average_total_seconds":round(statistics.mean(totals),3) if totals else None,
            "episodes":rows,
            "telemetry_policy":"fail-soft; never a Story/Release gate"}
    write_json(root/REPORT_REL,report);return report

def self_test():
    assert abs(percentile([10,20,30],0.5)-20)<0.001
    assert REL==runtime_observability.EPISODE_PERFORMANCE_REL
    assert _interval_union_seconds([])==0.0
    # STORY_OS_V211_UNCLOSED_SPAN_REUSE + _NO_FABRICATED_SPAN. Temp episode must live
    # under ROOT: _new() records episode_path relative to it.
    with tempfile.TemporaryDirectory(dir=ROOT/"episodes/_tests") as td:
        ep=Path(td);stage="VISUAL_LOCK"
        def rows():return load(ep,False)["stages"][stage]["runs"]
        first=begin_stage(ep,stage)
        assert begin_stage(ep,stage)==first,"a second begin must adopt the open span"
        assert len(rows())==1
        # An unmatched run_id must not close an unrelated open row, nor invent one.
        assert end_stage(ep,stage,run_id="nosuchrun") is None
        assert len(rows())==1 and rows()[0]["status"]=="RUNNING"
        closed=end_stage(ep,stage,status="REUSED")
        assert closed and closed["run_id"]==first and isinstance(closed["duration_seconds"],float)
        # Nothing open -> no-op, and never a fabricated 'recovered' row.
        assert end_stage(ep,stage) is None
        assert len(rows())==1 and not any(r.get("source")=="recovered" for r in rows())
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
