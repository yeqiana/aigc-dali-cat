#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, heapq, json, math, threading, time, uuid
from functools import lru_cache
from collections import Counter, defaultdict
from pathlib import Path
import storyos_config
import runtime_observability
import hot_state_bridge
import runtime_fact_store
import storage_config

ROOT=Path(__file__).resolve().parents[2]
_CONFIG=storyos_config.load_config()
_LOCK=threading.Lock()

class TraceContextUnavailable(RuntimeError):
    """拒绝写入没有 trace_id 的 Span 事件，避免产生不可关联事实。"""

def now():return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="milliseconds")
@lru_cache(maxsize=1)
def _cfg():
    # This process already snapshots storyos.yaml at module import; avoid
    # re-reading/parsing the trace policy for every nested event attribute.
    rel=storyos_config.get_path(_CONFIG,"agent_runtime.trace.config")
    data=json.loads((ROOT/str(rel)).read_text(encoding="utf-8-sig"))
    if not isinstance(data,dict):raise ValueError("trace config root must be object")
    return data
def _path(ep,key):return ep/str(_cfg()[key])
def _clean(v):
    if v is None or isinstance(v,(bool,int,float)):return v
    if isinstance(v,str):return v[:int(_cfg().get("max_attribute_chars") or 800)]
    if isinstance(v,dict):return {str(k):_clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [_clean(x) for x in v[:50]]
    return str(v)[:200]
def emit(ep:Path,event:dict):
    if storyos_config.get_path(_CONFIG,"agent_runtime.trace.enabled") is not True:return
    row={"at":now(),**_clean(event)}
    mode=storage_config.runtime_store_config()["mode"]
    if mode in {"dual","mysql"}:
        runtime_fact_store.record_trace_event(ep,row)
    if mode != "mysql":
        p=_path(ep,"event_path");p.parent.mkdir(parents=True,exist_ok=True)
        line=json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n"
        with _LOCK:
            with p.open("a",encoding="utf-8",newline="\n") as f:f.write(line)
def start_run(ep,run_id,request_data,runtime,route_decision=None):
    trace_id="ST_"+uuid.uuid4().hex[:16]
    cur={"trace_id":trace_id,"run_id":run_id,"request_id":(request_data or {}).get("request_id"),
         "runtime":runtime,"started_at":now(),"route_id":(route_decision or {}).get("route_id")}
    if storage_config.hot_state_config()["mode"] != "redis":
        p=_path(ep,"current_path");p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(cur,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    hot_state_bridge.mirror(ep, "TRACE_CURRENT", cur)
    emit(ep,{"event":"TRACE_START",**cur,"status":"RUNNING"});return trace_id
def current(ep):
    hot = hot_state_bridge.read(ep, "TRACE_CURRENT")
    if hot.get("redis_read") and isinstance(hot.get("value"), dict):
        return hot["value"]
    if not hot_state_bridge.file_fallback_allowed(hot):
        return {}
    p=_path(ep,"current_path")
    if not p.is_file():return {}
    try:
        d=json.loads(p.read_text(encoding="utf-8-sig"));return d if isinstance(d,dict) else {}
    except Exception:return {}
def _context(ep,trace_id,run_id):
    cur=current(ep)
    resolved_trace=trace_id or cur.get("trace_id")
    resolved_run=run_id or cur.get("run_id")
    if not resolved_trace:
        raise TraceContextUnavailable("trace context unavailable: trace_id is required")
    return resolved_trace,resolved_run
def start_span(ep,name,*,category,trace_id=None,run_id=None,parent_span_id=None,attrs=None):
    resolved_trace,resolved_run=_context(ep,trace_id,run_id);sid="SP_"+uuid.uuid4().hex[:16]
    emit(ep,{"event":"SPAN_START","trace_id":resolved_trace,"run_id":resolved_run,
        "span_id":sid,"parent_span_id":parent_span_id,"name":name,"category":category,"status":"RUNNING","attrs":attrs or {}})
    return sid
def end_span(ep,span_id,*,name,category,status,started_monotonic,trace_id=None,run_id=None,attrs=None):
    resolved_trace,resolved_run=_context(ep,trace_id,run_id);emit(ep,{"event":"SPAN_END","trace_id":resolved_trace,"run_id":resolved_run,
        "span_id":span_id,"name":name,"category":category,"status":status,
        "elapsed_ms":round((time.monotonic()-started_monotonic)*1000,3),"attrs":attrs or {}})
def route_event(ep,decision):
    cur=current(ep);emit(ep,{"event":"ROUTE_DECISION","trace_id":cur.get("trace_id"),"run_id":cur.get("run_id"),
        "route_id":decision.get("route_id"),"intent":decision.get("intent"),"workflow_mode":decision.get("workflow_mode"),
        "entry_step":decision.get("entry_step"),"reason_codes":decision.get("reason_codes"),"status":"DECIDED"})
def _iter_rows(ep):
    if storage_config.runtime_store_config()["mode"] == "mysql":
        # Keep the MySQL authority path unchanged; no local JSON fallback.
        yield from runtime_fact_store.load_trace_events(ep)
        return
    p=_path(ep,"event_path")
    if not p.is_file():return
    with p.open("r",encoding="utf-8-sig") as handle:
        for line in handle:
            try:
                d=json.loads(line)
                if isinstance(d,dict):yield d
            except (ValueError,TypeError):
                continue

def _rows(ep):
    # Compatibility helper for existing read-only diagnostics.
    return list(_iter_rows(ep))

def _elapsed_ms_for_summary(raw):
    """Untrusted diagnostic events must not poison aggregate output with NaN."""
    try:
        amount=float(raw or 0)
    except (TypeError,ValueError,OverflowError):
        return 0.0
    return amount if math.isfinite(amount) and amount >= 0 else 0.0


def summarize(ep,*,write=True):
    by=defaultdict(float)
    counts=Counter()
    slowest=[]
    latest=None
    total=0
    finished=0
    for row in _iter_rows(ep):
        total+=1
        if row.get("trace_id"):
            latest=row["trace_id"]
        if row.get("event")!="SPAN_END":
            continue
        finished+=1
        category=str(row.get("category") or "UNKNOWN")
        elapsed=_elapsed_ms_for_summary(row.get("elapsed_ms"))
        by[category]+=elapsed
        counts[str(row.get("status") or "UNKNOWN")]+=1
        # Earlier spans win on equal duration, preserving stable-sort output.
        entry=(elapsed,-finished,row)
        if len(slowest)<12:
            heapq.heappush(slowest,entry)
        elif entry[:2]>slowest[0][:2]:
            heapq.heapreplace(slowest,entry)
    slow=[entry[2] for entry in sorted(slowest,reverse=True)]
    s={"schema_version":1,"generated_at":now(),"diagnostic_only":True,"stage_authority":False,
       "latest_trace_id":latest,"event_count":total,"span_end_count":finished,
       "status_counts":dict(counts),
       "elapsed_ms_by_category":{k:round(v,3) for k,v in by.items()},
       "slowest_spans":[{**{k:r.get(k) for k in ("name","category","status","span_id")},
                         "elapsed_ms":_elapsed_ms_for_summary(r.get("elapsed_ms"))} for r in slow]}
    if write:
        runtime_observability.write_summary(ep,runtime_observability.TRACE_SUMMARY_REL,kind="trace_summary",payload=s)
    return s
def finish_run(ep,trace_id,run_id,status,*,note=""):
    emit(ep,{"event":"TRACE_END","trace_id":trace_id,"run_id":run_id,"status":status,"note":note});return summarize(ep,write=True)
def self_test():
    c=_cfg();assert c["trace_is_stage_authority"] is False;assert c["store_raw_user_request"] is False
    print("RUNTIME TRACE SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("summary");p.add_argument("episode_dir",type=Path);sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    print(json.dumps(summarize(a.episode_dir.resolve(),write=True),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
