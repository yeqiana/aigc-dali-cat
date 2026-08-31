#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, datetime as dt, json
from pathlib import Path

REL=Path("meta/quota-observability.json")
TOKEN_KEYS={"input_tokens","output_tokens","total_tokens","cached_input_tokens","prompt_tokens","completion_tokens"}

def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def read(ep):
    p=ep/REL
    if not p.is_file(): return {"schema_version":1,"note":"Diagnostic only; quota percentages are never guessed.","snapshots":[]}
    d=json.loads(p.read_text(encoding="utf-8-sig")); d.setdefault("snapshots",[]); return d
def write(ep,d):
    p=ep/REL; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def walk_tokens(obj,out):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k in TOKEN_KEYS and isinstance(v,(int,float)): out[k]=out.get(k,0)+int(v)
            else: walk_tokens(v,out)
    elif isinstance(obj,list):
        for x in obj: walk_tokens(x,out)
def scan_logs(ep):
    totals={}; files=[]; paths=[]
    p=ep/"meta/codex-auto-run.jsonl"
    if p.is_file(): paths.append(p)
    for folder in ("scoped-workers","image-workers"):
        d=ep/"meta"/folder
        if d.is_dir(): paths.extend(sorted(d.glob("*.jsonl")))
    for p in paths:
        files.append(p.relative_to(ep).as_posix())
        for line in p.read_text(encoding="utf-8",errors="replace").splitlines():
            try: obj=json.loads(line)
            except Exception: continue
            walk_tokens(obj,totals)
    return {"source":"local_jsonl_best_effort","token_counters":totals,"files_scanned":files,"warning":"Local counters may not equal product quota accounting."}
def snapshot(ep,five=None,weekly=None,source="codex_status_manual",note=""):
    for name,value in (("five_hour_remaining_pct",five),("weekly_remaining_pct",weekly)):
        if value is not None and not 0<=value<=100: raise ValueError(f"{name} must be 0..100")
    d=read(ep)
    row={"at":now(),"quota":{"five_hour_remaining_pct":five,"weekly_remaining_pct":weekly,"source":source if five is not None or weekly is not None else "UNAVAILABLE"},"observed_usage":scan_logs(ep),"note":note}
    d["snapshots"].append(row); d["snapshots"]=d["snapshots"][-100:]; d["updated_at"]=now(); write(ep,d); return row
def report(ep):
    d=read(ep); snaps=d.get("snapshots") or []; result={"snapshot_count":len(snaps),"latest":snaps[-1] if snaps else None,"quota_deltas":None}
    explicit=[x for x in snaps if (x.get("quota") or {}).get("five_hour_remaining_pct") is not None or (x.get("quota") or {}).get("weekly_remaining_pct") is not None]
    if len(explicit)>=2:
        a,b=explicit[-2],explicit[-1]; qa,qb=a["quota"],b["quota"]
        result["quota_deltas"]={
          "five_hour_consumed_pct_points":None if qa.get("five_hour_remaining_pct") is None or qb.get("five_hour_remaining_pct") is None else round(qa["five_hour_remaining_pct"]-qb["five_hour_remaining_pct"],3),
          "weekly_consumed_pct_points":None if qa.get("weekly_remaining_pct") is None or qb.get("weekly_remaining_pct") is None else round(qa["weekly_remaining_pct"]-qb["weekly_remaining_pct"],3),
          "from":a["at"],"to":b["at"]}
    return result
def self_test():
    assert REL.as_posix()=="meta/quota-observability.json"; print("QUOTA OBSERVABILITY SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("auto"); p.add_argument("episode_dir"); p.add_argument("--note",default="")
    p=sub.add_parser("snapshot"); p.add_argument("episode_dir"); p.add_argument("--five-hour-remaining",type=float); p.add_argument("--weekly-remaining",type=float); p.add_argument("--source",default="codex_status_manual"); p.add_argument("--note",default="")
    p=sub.add_parser("report"); p.add_argument("episode_dir")
    sub.add_parser("self-test"); a=ap.parse_args()
    if a.cmd=="self-test": self_test(); return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="auto": print(json.dumps(snapshot(ep,note=a.note),ensure_ascii=False,indent=2)); return 0
    if a.cmd=="snapshot": print(json.dumps(snapshot(ep,a.five_hour_remaining,a.weekly_remaining,a.source,a.note),ensure_ascii=False,indent=2)); return 0
    print(json.dumps(report(ep),ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
