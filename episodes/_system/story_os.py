#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SYSTEM_DIR = Path(__file__).resolve().parent
ROOT = SYSTEM_DIR.parents[1]
STATES = [
    "IDEA_LOCKED",
    "STORYBOARD_LOCKED",
    "VISUAL_CALIBRATED",
    "PRODUCTION_PASSED",
    "PUBLISH_READY",
    "PUBLISHED",
    "DATA_REVIEWED",
]
GATE_HINTS = {
    "IDEA_LOCKED": "锁选题：完成最近作品去同质化检查、四把锁、竞争解释与故事入口。",
    "STORYBOARD_LOCKED": "Story Lock：锁完整故事 + 专业分镜 + hook/climax/payoff。",
    "VISUAL_CALIBRATED": "Visual Lock：真实性卡 + 连续性锚点 + 三张校准 + 四张视觉准入。",
    "PRODUCTION_PASSED": "Batch：剩余图生产完成；逐帧真实性/连续性审核；必要帧最多一次内容返修。",
    "PUBLISH_READY": "Release Lock：FINAL_CHECKLIST + 标题/封面/字幕/简介/话题/manifest 全部一致。",
    "PUBLISHED": "记录实际发布时间、平台和最终发布版本事实。",
    "DATA_REVIEWED": "回填 6h/24h/48h/7d 数据，形成下一篇选题输入。",
}


def load_state(ep: Path):
    p = ep / "meta/episode-state.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def cmd_status(ep: Path):
    s = load_state(ep)
    if not s:
        print("NO_STATE: 该剧集尚未接入 episode-state.json")
        return 1
    cur = s.get("current_state", "UNKNOWN")
    print(cur)
    return 0


def cmd_next(ep: Path):
    s = load_state(ep)
    if not s:
        print("当前剧集没有 meta/episode-state.json。")
        print(f"先初始化：python episodes/_system/episode_state.py init \"{ep}\" --id <id> --series <series> --title <title> --frame-count <N>")
        return 1
    cur = s.get("current_state")
    print(f"Current: {cur}")
    if cur not in STATES:
        print("状态不在 Story OS 七阶段中，请先修复 episode-state.json。")
        return 2
    idx = STATES.index(cur)
    print(f"Now: {GATE_HINTS[cur]}")
    if idx == len(STATES) - 1:
        print("Next: 已完成数据复盘；下一步进入新选题，不再推进本集状态。")
        return 0
    nxt = STATES[idx + 1]
    print(f"Next target: {nxt}")
    print(f"Need: {GATE_HINTS[nxt]}")
    print("Precheck:")
    print(f"  python episodes/_system/validate_episode.py \"{ep}\" --target {nxt}")
    print(f"  python episodes/_system/machine_gate.py \"{ep}\" --target {nxt}")
    print(f"  python episodes/_system/v18_gate.py \"{ep}\" --target {nxt}")
    print("Transition after PASS:")
    print(f"  python episodes/_system/episode_state.py transition \"{ep}\" {nxt} --note \"...\"")
    return 0


def forward(script, args):
    return subprocess.call([sys.executable, str(SYSTEM_DIR / script), *args], cwd=ROOT)


def main():
    ap = argparse.ArgumentParser(description="Story OS V1.8 Golden Path CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    p = sub.add_parser("status"); p.add_argument("episode_dir")
    p = sub.add_parser("next"); p.add_argument("episode_dir")
    p = sub.add_parser("checklist"); p.add_argument("episode_dir"); p.add_argument("--no-validators", action="store_true")
    # Story OS V1.7 reliability adapters (evidence/transaction only; no new episode stage)
    p = sub.add_parser("audit-text"); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("transport"); p.add_argument("episode_dir"); p.add_argument("transport_cmd", choices=["preflight", "failure", "success", "status"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("text-revision"); p.add_argument("episode_dir"); p.add_argument("revision_cmd", choices=["start", "diff", "submit", "approve", "revert", "status"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    # Story OS V1.8: default visual IP + approval provenance + release hash
    p = sub.add_parser("visual-profile"); p.add_argument("episode_dir"); p.add_argument("profile_cmd", choices=["show", "set-default", "set-override"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("approval"); p.add_argument("episode_dir"); p.add_argument("approval_cmd", choices=["story", "visual", "verify", "status"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("release-package"); p.add_argument("episode_dir"); p.add_argument("release_cmd", choices=["build", "verify", "show"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    if args.cmd == "doctor":
        return forward("story_os_doctor.py", [])
    ep = Path(args.episode_dir).resolve()
    if args.cmd == "audit-text":
        return forward("text_audit.py", [str(ep), *args.extra])
    if args.cmd == "transport":
        return forward("transport_guard.py", [args.transport_cmd, str(ep), *args.extra])
    if args.cmd == "text-revision":
        return forward("text_revision.py", [args.revision_cmd, str(ep), *args.extra])
    if args.cmd == "visual-profile":
        return forward("visual_profile.py", [args.profile_cmd, str(ep), *args.extra])
    if args.cmd == "approval":
        return forward("approval_lock.py", [args.approval_cmd, str(ep), *args.extra])
    if args.cmd == "release-package":
        return forward("release_package.py", [args.release_cmd, str(ep), *args.extra])
    if args.cmd == "status":
        return cmd_status(ep)
    if args.cmd == "next":
        return cmd_next(ep)
    if args.cmd == "checklist":
        extra = [str(ep)] + (["--no-validators"] if args.no_validators else [])
        return forward("final_checklist.py", extra)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
