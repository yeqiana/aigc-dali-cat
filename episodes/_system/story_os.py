#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
SYSTEM_DIR=Path(__file__).resolve().parent
ROOT=SYSTEM_DIR.parents[1]
STATES=["IDEA_LOCKED","STORYBOARD_LOCKED","VISUAL_CALIBRATED","PRODUCTION_PASSED","PUBLISH_READY","PUBLISHED","DATA_REVIEWED"]
GATE_HINTS={
"IDEA_LOCKED":"锁选题：完成最近作品去同质化检查、四把锁、竞争解释与故事入口。",
"STORYBOARD_LOCKED":"Story Lock：锁完整故事 + 专业分镜 + hook/climax/payoff。",
"VISUAL_CALIBRATED":"Visual Lock：真实性卡 + 连续性锚点 + 三张校准 + 四张视觉准入。",
"PRODUCTION_PASSED":"Batch：剩余图生产完成；逐帧真实性/连续性审核；必要帧最多一次内容返修。",
"PUBLISH_READY":"Release Lock：FINAL_CHECKLIST + 标题/封面/字幕/简介/话题/manifest 全部一致。",
"PUBLISHED":"记录实际发布时间、平台和最终发布版本事实。",
"DATA_REVIEWED":"回填 6h/24h/48h/7d 数据，形成下一篇选题输入。"}
def load_state(ep):
    p=ep/"meta/episode-state.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
def status(ep):
    s=load_state(ep)
    if not s:print("NO_STATE: 该剧集尚未接入 episode-state.json");return 1
    print(s.get("current_state","UNKNOWN"));return 0
def nxt(ep):
    s=load_state(ep)
    if not s:print("当前剧集没有 meta/episode-state.json。");return 1
    cur=s.get("current_state");print("Current:",cur)
    if cur not in STATES:return 2
    i=STATES.index(cur);print("Now:",GATE_HINTS[cur])
    if i==len(STATES)-1:print("Next: 已完成数据复盘。");return 0
    n=STATES[i+1];print("Next target:",n);print("Need:",GATE_HINTS[n])
    print(f'Precheck:\n  python episodes/_system/validate_episode.py "{ep}" --target {n}\n  python episodes/_system/machine_gate.py "{ep}" --target {n}\n  python episodes/_system/v18_gate.py "{ep}" --target {n}')
    return 0
def forward(script,args):return subprocess.call([sys.executable,str(SYSTEM_DIR/script),*args],cwd=ROOT)
def main():
    ap=argparse.ArgumentParser(description="Story OS V2.0 Golden Path CLI")
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("doctor")
    p=sub.add_parser("status");p.add_argument("episode_dir")
    p=sub.add_parser("next");p.add_argument("episode_dir")
    p=sub.add_parser("checklist");p.add_argument("episode_dir");p.add_argument("--no-validators",action="store_true")
    p=sub.add_parser("audit-text");p.add_argument("episode_dir");p.add_argument("extra",nargs=argparse.REMAINDER)
    p=sub.add_parser("transport");p.add_argument("episode_dir");p.add_argument("transport_cmd",choices=["preflight","failure","success","status"]);p.add_argument("extra",nargs=argparse.REMAINDER)
    p=sub.add_parser("text-revision");p.add_argument("episode_dir");p.add_argument("revision_cmd",choices=["start","diff","submit","approve","revert","status"]);p.add_argument("extra",nargs=argparse.REMAINDER)
    p=sub.add_parser("visual-profile");p.add_argument("episode_dir");p.add_argument("profile_cmd",choices=["show","set-default","set-override"]);p.add_argument("extra",nargs=argparse.REMAINDER)
    p=sub.add_parser("approval");p.add_argument("episode_dir");p.add_argument("approval_cmd",choices=["story","visual","verify","status"]);p.add_argument("extra",nargs=argparse.REMAINDER)
    p=sub.add_parser("release-package");p.add_argument("episode_dir");p.add_argument("release_cmd",choices=["build","verify","show"]);p.add_argument("extra",nargs=argparse.REMAINDER)
    p=sub.add_parser("capture-profile");p.add_argument("profile_cmd",choices=["validate","list","show"]);p.add_argument("extra",nargs=argparse.REMAINDER)
    p=sub.add_parser("regression");p.add_argument("regression_cmd",choices=["run","show"]);p.add_argument("extra",nargs=argparse.REMAINDER)
    p=sub.add_parser("fingerprint");p.add_argument("fingerprint_cmd",choices=["init","compare","register","list"]);p.add_argument("episode_dir",nargs="?");p.add_argument("extra",nargs=argparse.REMAINDER)
    p=sub.add_parser("auto-prod");p.add_argument("auto_cmd",choices=["plan","run","status","package","self-test"]);p.add_argument("episode_dir",nargs="?");p.add_argument("extra",nargs=argparse.REMAINDER)
    a=ap.parse_args()
    if a.cmd=="doctor":return forward("story_os_doctor.py",[])
    if a.cmd=="capture-profile":return forward("capture_profile.py",[a.profile_cmd,*a.extra])
    if a.cmd=="regression":return forward("story_regression.py",[a.regression_cmd,*a.extra])
    if a.cmd=="fingerprint":
        x=[a.fingerprint_cmd]+(([a.episode_dir] if a.episode_dir else []))+a.extra
        return forward("episode_fingerprint.py",x)
    if a.cmd=="auto-prod":
        x=[a.auto_cmd]+(([a.episode_dir] if a.episode_dir else []))+a.extra
        return forward("auto_production.py",x)
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="audit-text":return forward("text_audit.py",[str(ep),*a.extra])
    if a.cmd=="transport":return forward("transport_guard.py",[a.transport_cmd,str(ep),*a.extra])
    if a.cmd=="text-revision":return forward("text_revision.py",[a.revision_cmd,str(ep),*a.extra])
    if a.cmd=="visual-profile":return forward("visual_profile.py",[a.profile_cmd,str(ep),*a.extra])
    if a.cmd=="approval":return forward("approval_lock.py",[a.approval_cmd,str(ep),*a.extra])
    if a.cmd=="release-package":return forward("release_package.py",[a.release_cmd,str(ep),*a.extra])
    if a.cmd=="status":return status(ep)
    if a.cmd=="next":return nxt(ep)
    if a.cmd=="checklist":return forward("final_checklist.py",[str(ep)]+(["--no-validators"] if a.no_validators else []))
    return 2
if __name__=="__main__":raise SystemExit(main())
