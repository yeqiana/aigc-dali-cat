#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, json, threading, time, uuid
from collections import Counter, defaultdict
from pathlib import Path
import storyos_config

ROOT=Path(__file__).resolve().parents[2]
_CONFIG=storyos_config.load_config()
_LOCK=threading.Lock()

def now():return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="milliseconds")
def _cfg():
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
    p=_path(ep,"event_path");p.parent.mkdir(parents=True,exist_ok=True)
    line=json.dumps({"at":now(),**_clean(event)},ensure_ascii=False,separators=(",",":"))+"\n"
    with _LOCK:
        with p.open("a",encoding="utf-8",newline="\n") as f:f.write(line)
def start_run(ep,run_id,request_data,runtime,route_decision=None):
    trace_id="ST_"+uuid.uuid4().hex[:16]
    cur={"trace_id":trace_id,"run_id":run_id,"request_id":(request_data or {}).get("request_id"),
         "runtime":runtime,"started_at":now(),"route_id":(route_decision or {}).get("route_id")}
    p=_path(ep,"current_path");p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(cur,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    emit(ep,{"event":"TRACE_START",**cur,"status":"RUNNING"});return trace_id
def current(ep):
    p=_path(ep,"current_path")
    if not p.is_file():return {}
    try:
        d=json.loads(p.read_text(encoding="utf-8-sig"));return d if isinstance(d,dict) else {}
    except Exception:return {}
def start_span(ep,name,*,category,trace_id=None,run_id=None,parent_span_id=None,attrs=None):
    cur=current(ep);sid="SP_"+uuid.uuid4().hex[:16]
    emit(ep,{"event":"SPAN_START","trace_id":trace_id or cur.get("trace_id"),"run_id":run_id or cur.get("run_id"),
        "span_id":sid,"parent_span_id":parent_span_id,"name":name,"category":category,"status":"RUNNING","attrs":attrs or {}})
    return sid
def end_span(ep,span_id,*,name,category,status,started_monotonic,trace_id=None,run_id=None,attrs=None):
    cur=current(ep);emit(ep,{"event":"SPAN_END","trace_id":trace_id or cur.get("trace_id"),"run_id":run_id or cur.get("run_id"),
        "span_id":span_id,"name":name,"category":category,"status":status,
        "elapsed_ms":round((time.monotonic()-started_monotonic)*1000,3),"attrs":attrs or {}})
def route_event(ep,decision):
    cur=current(ep);emit(ep,{"event":"ROUTE_DECISION","trace_id":cur.get("trace_id"),"run_id":cur.get("run_id"),
        "route_id":decision.get("route_id"),"intent":decision.get("intent"),"workflow_mode":decision.get("workflow_mode"),
        "entry_step":decision.get("entry_step"),"reason_codes":decision.get("reason_codes"),"status":"DECIDED"})
def _rows(ep):
    p=_path(ep,"event_path")
    if not p.is_file():return []
    out=[]
    for line in p.read_text(encoding="utf-8-sig").splitlines():
        try:
            d=json.loads(line)
            if isinstance(d,dict):out.append(d)
        except Exception:pass
    return out
def summarize(ep,*,write=True):
    rows=_rows(ep);ends=[r for r in rows if r.get("event")=="SPAN_END"];latest=None
    for r in reversed(rows):
        if r.get("trace_id"):latest=r["trace_id"];break
    by=defaultdict(float)
    for r in ends:by[str(r.get("category") or "UNKNOWN")]+=float(r.get("elapsed_ms") or 0)
    slow=sorted(ends,key=lambda r:float(r.get("elapsed_ms") or 0),reverse=True)[:12]
    s={"schema_version":1,"generated_at":now(),"diagnostic_only":True,"stage_authority":False,
       "latest_trace_id":latest,"event_count":len(rows),"span_end_count":len(ends),
       "status_counts":dict(Counter(str(r.get("status") or "UNKNOWN") for r in ends)),
       "elapsed_ms_by_category":{k:round(v,3) for k,v in by.items()},
       "slowest_spans":[{k:r.get(k) for k in ("name","category","status","elapsed_ms","span_id")} for r in slow]}
    if write:
        p=_path(ep,"summary_path");p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
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
