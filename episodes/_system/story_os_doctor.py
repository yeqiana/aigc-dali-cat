#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

from contract_sync import collect_errors
import storyos_config
import runtime_log_policy
import episode_discovery

ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def issue(bucket, level: str, code: str, message: str):
    bucket.append({"level": level, "code": code, "message": message})


def scan_episode_meta(issues):
    episodes = ROOT / "episodes"
    if not episodes.exists():
        return
    for ep in episode_discovery.iter_episode_roots(episodes):
        state_path = ep / "meta/episode-state.json"
        try:
            state = load_json(state_path)
        except Exception as e:
            issue(issues, "ERROR", "STATE_JSON", f"{state_path.relative_to(ROOT)}: {e}")
            continue
        current = state.get("current_state")
        if not current:
            issue(issues, "ERROR", "STATE_MISSING", f"{ep.relative_to(ROOT)} 缺 current_state")
        gates_path = ep / "meta/story-gates.json"
        if gates_path.exists():
            try:
                gates = load_json(gates_path)
                for bad in ("current_state", "stage", "workflow_state"):
                    if bad in gates:
                        issue(issues, "ERROR", "SECOND_STATE_SOURCE", f"{gates_path.relative_to(ROOT)} 顶层包含 {bad}")
            except Exception as e:
                issue(issues, "ERROR", "GATES_JSON", f"{gates_path.relative_to(ROOT)}: {e}")


def run_doctor():
    issues = []
    required = [
        "story_os_manifest.json",
        "config/storyos.yaml",
        "config/index.yaml",
        "START_HERE.md",
        "SKILL.md",
        "AGENTS.md",
        "standards/制作规范_正式版.md",
        "standards/AUTHORITY_INDEX.json",
        "runtimes/runtime-contract.json",
        "skills/dali-cat-story/SKILL.md",
        ".agents/skills/dali-cat-story/SKILL.md",
        "episodes/_system/story_os_contract.py",
        "episodes/_system/contract_sync.py",
        "episodes/_system/requirements.txt",
        "episodes/_system/episode_state.py",
        "episodes/_system/validate_episode.py",
        "episodes/_system/machine_gate.py",
        "episodes/_system/evidence_gate.py",
        "episodes/_system/story_os.py",
        "episodes/_system/final_checklist.py",
        "episodes/_system/visual_profile.py",
        "episodes/_system/approval_lock.py",
        "episodes/_system/release_package.py",
        "standards/visual_profiles/M00_MP4_网吧_流水席_旧数码.json",
        "standards/风格锚点_MP4_网吧_流水席_旧数码_V1.2.md",
    ]
    for rel in required:
        if not (ROOT / rel).exists():
            issue(issues, "ERROR", "MISSING_REQUIRED", f"缺少 {rel}")

    if importlib.util.find_spec("PIL") is None:
        issue(
            issues,
            "ERROR",
            "RUNTIME_DEPENDENCY",
            "缺少 Pillow；执行 python -m pip install -r episodes/_system/requirements.txt",
        )
    if importlib.util.find_spec("yaml") is None:
        issue(issues, "ERROR", "RUNTIME_DEPENDENCY", "缺少 PyYAML；执行 python -m pip install -r episodes/_system/requirements.txt")

    try:
        for error in storyos_config.validate():
            issue(issues, "ERROR", "CONFIG_INVALID", error)
        storyos_config.load_index()
    except Exception as e:
        issue(issues, "ERROR", "CONFIG_INVALID", str(e))

    for error in collect_errors(ROOT):
        issue(issues, "ERROR", "CONTRACT_SYNC", error)

    auth_path = ROOT / "standards/AUTHORITY_INDEX.json"
    if auth_path.exists():
        try:
            auth = load_json(auth_path)
            docs = auth.get("documents", [])
            canon = [d for d in docs if d.get("authority") == "canonical" and d.get("active")]
            if len(canon) != 1:
                issue(issues, "ERROR", "CANONICAL_COUNT", f"active canonical 应恰好 1 个，当前 {len(canon)}")
            active_paths = set()
            superseded = set()
            for d in docs:
                path = d.get("path")
                if d.get("active") and path:
                    active_paths.add(path)
                    if not (ROOT / path).exists():
                        issue(issues, "ERROR", "AUTHORITY_MISSING", f"权威索引指向不存在文件：{path}")
                for old in d.get("supersedes", []) or []:
                    superseded.add(old)
            for old in sorted(superseded):
                if old in active_paths:
                    issue(issues, "ERROR", "SUPERSEDED_ACTIVE", f"历史文件同时被标成 active：{old}")

            standards = ROOT / "standards"
            if standards.exists():
                versioned = re.compile(r"_V\d+(?:\.\d+)*\.md$", re.I)
                known = {d.get("path") for d in docs if d.get("path")}
                for f in standards.glob("*.md"):
                    rel = f.relative_to(ROOT).as_posix()
                    if versioned.search(f.name) and rel not in known:
                        issue(issues, "WARN", "UNINDEXED_VERSIONED_STANDARD", f"版本化规范未登记 authority：{rel}")
        except Exception as e:
            issue(issues, "ERROR", "AUTHORITY_JSON", f"AUTHORITY_INDEX.json 无法读取：{e}")

    for rel in ("START_HERE.md", "SKILL.md", "AGENTS.md"):
        p = ROOT / rel
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            if rel != "START_HERE.md" and "START_HERE.md" not in text:
                issue(issues, "WARN", "ENTRYPOINT_NOT_LINKED", f"{rel} 未链接 START_HERE.md")

    log_audit = runtime_log_policy.audit(ROOT)
    if int(log_audit.get("tracked_historical_count") or 0) > 0:
        issue(
            issues,
            "WARN",
            "TRACKED_LOCAL_RUNTIME_LOGS",
            f"历史 raw runtime logs 仍被 Git 跟踪：{log_audit['tracked_historical_count']} 个，现存约 {log_audit['tracked_existing_bytes']} bytes；新日志已 local-only，历史记录可后续 git rm --cached + gc。",
        )

    scan_episode_meta(issues)
    return issues


def main():
    ap = argparse.ArgumentParser(description="Story OS repository health check")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    issues = run_doctor()
    errors = [x for x in issues if x["level"] == "ERROR"]
    warns = [x for x in issues if x["level"] == "WARN"]
    if args.json:
        print(json.dumps({"root": str(ROOT), "errors": len(errors), "warnings": len(warns), "issues": issues}, ensure_ascii=False, indent=2))
    else:
        print(f"Story OS Doctor | errors={len(errors)} warnings={len(warns)}")
        for x in issues:
            print(f"[{x['level']}] {x['code']}: {x['message']}")
        if not issues:
            print("PASS: product contract / Golden Path / authority / state-source baseline looks healthy.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
