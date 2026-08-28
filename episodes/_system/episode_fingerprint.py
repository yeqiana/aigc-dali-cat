#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TPL=ROOT/"standards"/"templates"/"episode-fingerprint.template.json"; REG=ROOT/"reports"/"account-pattern-registry.json"
W={"core_anomaly_mechanism":25,"story_engine":15,"entry_mode":10,"anomaly_carrier":10,"primary_visual_space":10,"middle_escalation":10,"climax_form":10,"relationship":5,"reality_residue":5}
def rd(p): return json.loads(p.read_text(encoding="utf-8"))
def wr(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def sim(a,b):
    da=a.get("dimensions") or {}; db=b.get("dimensions") or {}; score=0
    for k,w in W.items():
        x=str(da.get(k,"")).strip().lower(); y=str(db.get(k,"")).strip().lower()
        if x and x==y: score+=w
    veto=all(str(da.get(k,"")).strip() and str(da.get(k,"")).strip().lower()==str(db.get(k,"")).strip().lower() for k in ("core_anomaly_mechanism","middle_escalation","climax_form"))
    return score,veto
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    for name in ("init","compare","register"):
        p=sub.add_parser(name); p.add_argument("episode_dir")
        if name=="compare": p.add_argument("--limit",type=int,default=5)
    a=ap.parse_args(); ep=Path(a.episode_dir).resolve(); fp=ep/"meta"/"episode-fingerprint.json"
    if a.cmd=="init":
        if not fp.exists(): wr(fp,rd(TPL))
        print(fp); return 0
    if not fp.exists(): raise SystemExit("fingerprint missing")
    cur=rd(fp)
    if not REG.exists(): wr(REG,{"schema_version":1,"story_os_version":"2.0","episodes":[]})
    reg=rd(REG)
    if a.cmd=="register":
        if not cur.get("episode_id") or not cur.get("title") or any(not str((cur.get("dimensions") or {}).get(k,"")).strip() for k in W): raise SystemExit("fingerprint incomplete")
        row={"episode_id":cur["episode_id"],"title":cur["title"],"dimensions":cur["dimensions"]}
        reg["episodes"]=[x for x in reg.get("episodes",[]) if x.get("episode_id")!=row["episode_id"]]+[row]; wr(REG,reg); print("REGISTERED"); return 0
    blocked=False
    for x in reversed(reg.get("episodes",[])[-a.limit:]):
        score,veto=sim(cur,x); blocked=blocked or veto or score>=70; print(f"{score:03d}", "VETO" if veto else "HIGH" if score>=70 else "PASS", x.get("title",""))
    print("DECISION:", "BLOCK_OR_REDESIGN" if blocked else "PASS_WITH_REVIEW"); return 3 if blocked else 0
if __name__=="__main__": raise SystemExit(main())
