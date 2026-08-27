#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
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


def load(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def get_nested(obj, *keys, default=None):
    cur = obj
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def mark(value):
    return "✅" if value else "⬜"


def run_cmd(cmd):
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        tail = (p.stdout + "\n" + p.stderr).strip()
        if len(tail) > 3000:
            tail = tail[-3000:]
        return p.returncode == 0, tail
    except Exception as e:
        return False, str(e)


def build(ep: Path, target: str | None, run_validators: bool):
    meta = ep / "meta"
    state = load(meta / "episode-state.json") or {}
    gates = load(meta / "story-gates.json") or {}
    release = load(meta / "release-manifest.json") or {}
    ledger = load(meta / "production-ledger.json") or {}
    current = state.get("current_state", "UNKNOWN")
    strict = bool(get_nested(gates, "machine_contract", "strict", default=False))

    reviews = gates.get("reviews", {}) if isinstance(gates.get("reviews"), dict) else {}
    continuity = gates.get("continuity", {}) if isinstance(gates.get("continuity"), dict) else {}
    cal = gates.get("calibration", {}) if isinstance(gates.get("calibration"), dict) else {}

    lines = [
        "# FINAL CHECKLIST — generated evidence view",
        "",
        "> 自动生成，只汇总现有状态/证据；**不是新的规范源，也不得保存 stage。**",
        "",
        f"- Episode: `{ep.relative_to(ROOT).as_posix() if ep.is_relative_to(ROOT) else ep}`",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Current state: `{current}`",
        f"- Machine strict: `{strict}`",
        "",
        "## A. 机器事实",
        "",
        f"- {mark((meta/'episode-state.json').exists())} `episode-state.json` 存在",
        f"- {mark((meta/'story-gates.json').exists())} `story-gates.json` 存在",
        f"- {mark((meta/'release-manifest.json').exists())} `release-manifest.json` 存在",
        f"- {mark((meta/'production-ledger.json').exists() or not strict)} strict 模式 production ledger 就绪",
        f"- {mark(bool(reviews.get('story') == 'passed'))} story review passed",
        f"- {mark(bool(reviews.get('visual_admission') == 'passed'))} visual admission passed",
        f"- {mark(bool(reviews.get('authenticity') == 'passed'))} authenticity passed",
        f"- {mark(bool(reviews.get('production') == 'passed'))} production passed",
        f"- {mark(bool(reviews.get('continuity') == 'passed'))} continuity passed",
        f"- {mark(bool(reviews.get('publish') == 'passed'))} publish review passed",
        "",
        "## B. Golden Path 锁点",
        "",
        f"- {mark(current in STATES[1:])} Story Lock：故事/专业分镜已锁",
        f"- {mark(current in STATES[2:])} Visual Lock：三张校准 + 四张视觉准入已锁",
        f"- {mark(current in STATES[3:])} Production Lock：批量生产与逐帧审核完成",
        f"- {mark(current in STATES[4:])} Release Lock：发布版本已锁",
        "",
        "## C. 人工终审（必须人工回答）",
        "",
        "- [ ] 第一眼像真实手机相册 / 合理采集设备，而不是电影剧照、概念图或商业摄影",
        "- [ ] 拍摄者、设备、机位在物理上成立；第一视角设备没有无解释完整入镜",
        "- [ ] 人物身份、服装、地点、关键道具、天气/时间线连续",
        "- [ ] 前 5 张有继续滑动欲望，且每 3–5 张有新证据/因果/认知升级",
        "- [ ] 高潮强于中段，并且不是最近作品的机制换皮",
        "- [ ] 结尾回收前文线索，产生回看价值；没有多余尾图稀释高潮",
        "- [ ] 字幕是人话，位置不压主体，不靠过上/过下/过右等违背本集锁定版式",
        "- [ ] 封面、标题、简介、话题与最终成片一致，没有承诺画面里不存在的内容",
        "- [ ] 若执行 subtitle_only / crop_only，锁定底图 hash 未变化",
        "",
        "## D. 发布后闭环",
        "",
        "- [ ] 已准备 6h / 24h / 48h / 7d 数据回填位置",
        "- [ ] 下一篇选题会读取最近作品，检查题材、异常机制、场景语法、高潮与反转重复",
    ]

    if run_validators:
        tgt = target or (current if current in STATES else None)
        lines += ["", "## E. Validator 快照", ""]
        if tgt:
            ok, out = run_cmd([sys.executable, str(SYSTEM_DIR / "validate_episode.py"), str(ep), "--target", tgt])
            lines.append(f"- {'✅' if ok else '❌'} validate_episode.py --target {tgt}")
            if out:
                lines += ["", "```text", out, "```"]
            if strict and (SYSTEM_DIR / "machine_gate.py").exists():
                ok2, out2 = run_cmd([sys.executable, str(SYSTEM_DIR / "machine_gate.py"), str(ep), "--target", tgt])
                lines.append(f"- {'✅' if ok2 else '❌'} machine_gate.py --target {tgt}")
                if out2:
                    lines += ["", "```text", out2, "```"]
        else:
            lines.append("- ⚠️ 未识别 current_state，跳过 validator。")

    out_path = meta / "FINAL_CHECKLIST.md"
    meta.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_dir")
    ap.add_argument("--target", choices=STATES)
    ap.add_argument("--no-validators", action="store_true")
    args = ap.parse_args()
    ep = Path(args.episode_dir).resolve()
    if not ep.exists():
        print(f"Episode not found: {ep}", file=sys.stderr)
        return 2
    out = build(ep, args.target, not args.no_validators)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
