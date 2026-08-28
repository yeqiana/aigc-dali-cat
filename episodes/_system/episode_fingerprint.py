#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse,json,datetime as dt
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REG=ROOT/"reports"/"account-pattern-registry.json"
TPL=ROOT/"standards"/"templates"/"episode-fingerprint.template.json"
W={"core_anomaly_mechanism":25,"story_engine":15,"entry_mode":10,"anomaly_carrier":10,"primary_visual_space":10,"middle_escalation":10,"climax_form":10,"relationship":5,"reality_residue":5}
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def ensure():
    if not REG.exists():write(REG,{"schema_version":1,"story_os_version":"2.0","episodes":[]})
def sim(a,b):
    da=a["dimensions"];db=b["dimensions"];score=sum(v for k,v in W.items() if da.get(k) and str(da.get(k)).lower()==str(db.get(k)).lower())
    veto=all(da.get(k) and str(da.get(k)).lower()==str(db.get(k)).lower() for k in ("core_anomaly_mechanism","middle_escalation","climax_form"))
    return score,veto
def valid(d):
    return bool(d.get("episode_id") and d.get("title") and all((d.get("dimensions") or {}).get(k) for k in W))
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    for n in ("init","compare","register"):
        p=sub.add_parser(n);p.add_argument("episode")
    sub.add_parser("list"); a=ap.parse_args()
    if a.cmd=="list":ensure();print(REG.read_text(encoding="utf-8"));return 0
    ep=Path(a.episode).resolve();p=ep/"meta"/"episode-fingerprint.json"
    if a.cmd=="init":
        if not p.exists():write(p,read(TPL))
        print(p);return 0
    if not p.exists():print("FAIL: fingerprint missing");return 2
    cur=read(p)
    if not valid(cur):print("FAIL: fingerprint incomplete");return 2
    ensure();r=read(REG)
    if a.cmd=="register":
        row={"episode_id":cur["episode_id"],"title":cur["title"],"dimensions":cur["dimensions"],"registered_at":dt.datetime.now(dt.timezone.utc).isoformat()}
        r["episodes"]=[x for x in r["episodes"] if x.get("episode_id")!=cur["episode_id"]]+[row];write(REG,r);print("REGISTERED");return 0
    blocked=False
    for x in reversed(r["episodes"][-5:]):
        s,v=sim(cur,x);blocked=blocked or v or s>=70;print(s,"VETO" if v else "HIGH" if s>=70 else "MEDIUM_HIGH" if s>=55 else "LIGHT" if s>=40 else "LOW",x.get("title"))
    print("DECISION","BLOCK_OR_REDESIGN" if blocked else "PASS_WITH_REVIEW");return 3 if blocked else 0
if __name__=="__main__":raise SystemExit(main())
