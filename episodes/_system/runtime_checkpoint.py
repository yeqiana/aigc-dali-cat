#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, datetime as dt, json
from pathlib import Path
REL=Path("meta/runtime-checkpoint.json")
def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def rd(p): return json.loads(p.read_text(encoding="utf-8"))
def wr(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("init"); p.add_argument("episode_dir"); p.add_argument("--runtime",required=True,choices=["CODEX","WORK","WEB"]); p.add_argument("--full-auto",action="store_true")
    p=sub.add_parser("show"); p.add_argument("episode_dir")
    p=sub.add_parser("set"); p.add_argument("episode_dir"); p.add_argument("--last-completed"); p.add_argument("--next-action"); p.add_argument("--lock-frame",action="append",default=[]); p.add_argument("--fail-frame",action="append",default=[])
    a=ap.parse_args(); ep=Path(a.episode_dir).resolve(); path=ep/REL
    if a.cmd=="init":
        d=rd(path) if path.exists() else {"schema_version":1,"story_os_version":"2.0","last_completed":"RUNTIME_INITIALIZED","next_action":"READ_EPISODE_STATE","locked_frames":[],"failed_frames":[],"note":"Recovery evidence only; NOT a stage source."}
        d["runtime"]=a.runtime
        if a.full_auto:
            d["continuous_execution_authorized"]=True; d["approval_basis"]="delegated_continuous_execution"
        else:
            d.setdefault("continuous_execution_authorized",False); d.setdefault("approval_basis","interactive")
        d["updated_at"]=now(); wr(path,d); print(path); return 0
    if not path.exists(): raise SystemExit("runtime checkpoint missing")
    d=rd(path)
    if a.cmd=="show": print(path.read_text(encoding="utf-8")); return 0
    if a.last_completed: d["last_completed"]=a.last_completed
    if a.next_action: d["next_action"]=a.next_action
    d["locked_frames"]=sorted(set(d.get("locked_frames",[]))|{str(x).zfill(2) for x in a.lock_frame})
    d["failed_frames"]=sorted(set(d.get("failed_frames",[]))|{str(x).zfill(2) for x in a.fail_frame})
    d["updated_at"]=now(); wr(path,d); print(path); return 0
if __name__=="__main__": raise SystemExit(main())
