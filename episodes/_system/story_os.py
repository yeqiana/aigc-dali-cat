#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from story_os_contract import canonical_stages, story_os_version

SYSTEM_DIR = Path(__file__).resolve().parent
ROOT = SYSTEM_DIR.parents[1]
STATES = canonical_stages()
GATE_HINTS = {
    "IDEA_LOCKED": "锁选题：Recent-5 上下文 + 8–12候选 + Concept Ambition + 三传播图无字测试。",
    "STORYBOARD_LOCKED": "Story Lock：锁完整故事 + 专业分镜 + hook/climax/payoff。",
    "VISUAL_CALIBRATED": "Visual Lock：四层实际像素准入（baseline/worst/first anomaly/high-impact）+ 统一 Critic。",
    "PRODUCTION_PASSED": "Batch：Resolved Frame Contract + max3 有界并发 + Fail-soft/Repair Queue；最终逐帧语义审核。",
    "PUBLISH_READY": "Release Lock：Release/Compliance PASS + Final Candidate Snapshot SHA 冻结 + FINAL_CHECKLIST 一致。",
    "PUBLISHED": "记录实际发布时间、平台和最终发布版本事实。",
    "DATA_REVIEWED": "回填 6h/24h/48h/7d 数据，形成下一篇选题输入。",
}


def load_state(ep: Path):
    p = ep / "meta/episode-state.json"
    if not p.exists(): return None
    return json.loads(p.read_text(encoding="utf-8-sig"))


def cmd_status(ep: Path):
    s = load_state(ep)
    if not s:
        print("NO_STATE: 该剧集尚未接入 episode-state.json"); return 1
    print(s.get("current_state", "UNKNOWN")); return 0


def cmd_next(ep: Path):
    s = load_state(ep)
    if not s:
        print("当前剧集没有 meta/episode-state.json。")
        print(f"先初始化：python episodes/_system/episode_state.py init \"{ep}\" --id <id> --series <series> --title <title> --frame-count <N>")
        return 1
    cur = s.get("current_state")
    print(f"Current: {cur}")
    if cur not in STATES:
        print("状态不在 Story OS 七阶段中，请先修复 episode-state.json。"); return 2
    idx = STATES.index(cur); print(f"Now: {GATE_HINTS[cur]}")
    if idx == len(STATES) - 1:
        print("Next: 已完成数据复盘；下一步进入新选题，不再推进本集状态。"); return 0
    nxt = STATES[idx + 1]
    print(f"Next target: {nxt}"); print(f"Need: {GATE_HINTS[nxt]}")
    print("Precheck:")
    print(f"  python episodes/_system/validate_episode.py \"{ep}\" --target {nxt}")
    print(f"  python episodes/_system/machine_gate.py \"{ep}\" --target {nxt}")
    print(f"  python episodes/_system/evidence_gate.py \"{ep}\" --target {nxt}")
    print("Transition after PASS:")
    print(f"  python episodes/_system/episode_state.py transition \"{ep}\" {nxt} --note \"...\"")
    return 0


def forward(script, args):
    return subprocess.call([sys.executable, str(SYSTEM_DIR / script), *args], cwd=ROOT)


def main():
    ap = argparse.ArgumentParser(description=f"Story OS V{story_os_version()} Multi-Runtime CLI + V2.1 Workflow Foundation")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    p = sub.add_parser("status"); p.add_argument("episode_dir")
    p = sub.add_parser("next"); p.add_argument("episode_dir")
    p = sub.add_parser("plan"); p.add_argument("episode_dir")
    p = sub.add_parser("performance"); p.add_argument("episode_dir")
    p = sub.add_parser("dag"); p.add_argument("dag_cmd", choices=["plan", "run", "resume", "show"]); p.add_argument("episode_dir"); p.add_argument("--codex"); p.add_argument("--timeout", type=int, default=7200)
    p = sub.add_parser("quota"); p.add_argument("quota_cmd", choices=["auto", "snapshot", "report"]); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("checklist"); p.add_argument("episode_dir"); p.add_argument("--no-validators", action="store_true")
    p = sub.add_parser("audit-text"); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("transport"); p.add_argument("episode_dir"); p.add_argument("transport_cmd", choices=["preflight", "failure", "success", "status"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("text-revision"); p.add_argument("episode_dir"); p.add_argument("revision_cmd", choices=["start", "diff", "submit", "approve", "revert", "status"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("visual-profile"); p.add_argument("episode_dir"); p.add_argument("profile_cmd", choices=["show", "set-default", "set-override"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("approval"); p.add_argument("episode_dir"); p.add_argument("approval_cmd", choices=["story", "visual", "verify", "status"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("release-package"); p.add_argument("episode_dir"); p.add_argument("release_cmd", choices=["build", "verify", "show"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("runtime"); p.add_argument("runtime_cmd", choices=["detect", "capabilities", "contract", "show"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("request"); p.add_argument("request_cmd", choices=["compile", "validate", "bind", "show", "show-episode"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("image-model"); p.add_argument("image_model_cmd", choices=["resolve"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("checkpoint"); p.add_argument("episode_dir"); p.add_argument("checkpoint_cmd", choices=["init", "show", "set", "record-step"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("capture-profile"); p.add_argument("profile_cmd", choices=["validate", "list", "show"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("regression"); p.add_argument("regression_cmd", choices=["run", "show"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("concept"); p.add_argument("concept_cmd", choices=["init", "run-critic", "verify", "show"]); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("character"); p.add_argument("character_cmd", choices=["prepare", "lock", "validate", "show"]); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("handoff"); p.add_argument("handoff_cmd", choices=["build", "verify", "show", "activate"]); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("execution-r2"); p.add_argument("execution_cmd", choices=["set", "show", "clear"]); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("resource"); p.add_argument("resource_cmd", choices=["resolve", "show", "register"]); p.add_argument("episode_dir", nargs="?"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("intro"); p.add_argument("intro_cmd", choices=["resolve", "show"]); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("cache-r2"); p.add_argument("cache_cmd", choices=["stats", "clear"])
    p = sub.add_parser("environment"); p.add_argument("environment_cmd", choices=["init", "verify", "resolve-frame", "show"]); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("frame-contract"); p.add_argument("frame_contract_cmd", choices=["compile-all", "compile", "verify", "show"]); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("visual-lock-v21"); p.add_argument("visual_lock_cmd", choices=["prepare", "bind-from-queue", "run-critic", "verify", "show-plan"]); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("image-scheduler"); p.add_argument("scheduler_cmd", choices=["init", "add", "import-visual-lock", "import-batch", "plan", "run", "retry-tech", "show"]); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("frame-scout"); p.add_argument("scout_cmd", choices=["enable", "classify", "run", "audit", "show"]); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("final-snapshot"); p.add_argument("snapshot_cmd", choices=["enable", "build", "verify", "reuse-status", "show"]); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("migrate-v21"); p.add_argument("migration_cmd", choices=["scan", "plan", "activate", "verify", "show"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("regression-v21"); p.add_argument("regression_v21_cmd", choices=["run", "show"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("observability"); p.add_argument("observe_cmd", choices=["collect", "show"]); p.add_argument("episode_dir")
    p = sub.add_parser("post-publish"); p.add_argument("post_publish_cmd", choices=["enable", "mark-published", "record", "review", "complete", "verify", "show"]); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("learning-index"); p.add_argument("learning_cmd", choices=["rebuild", "show"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("fingerprint"); p.add_argument("fingerprint_cmd", choices=["init", "compare", "register"]); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("quality"); p.add_argument("quality_cmd", choices=["enable","verify-story","verify-preimage","verify-release","show"]); p.add_argument("episode_dir")
    p = sub.add_parser("lineage"); p.add_argument("lineage_cmd", choices=["record","verify","show"]); p.add_argument("episode_dir"); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("golden"); p.add_argument("golden_cmd", choices=["register","run","show"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("run"); p.add_argument("episode_dir"); p.add_argument("--full-auto", action="store_true"); p.add_argument("--resume", action="store_true"); p.add_argument("--codex"); p.add_argument("--timeout", type=int, default=7200); p.add_argument("--request-file")
    p = sub.add_parser("image-backend"); p.add_argument("backend_cmd", choices=["generate", "generate-for-frame", "self-test"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("delegated-delivery"); p.add_argument("episode_dir"); p.add_argument("delivery_cmd", choices=["build", "verify", "show"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    p = sub.add_parser("delegated-approval"); p.add_argument("episode_dir"); p.add_argument("approval_cmd", choices=["record", "verify", "show"]); p.add_argument("kind", nargs="?", choices=["story_lock", "visual_lock", "release_lock"]); p.add_argument("extra", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    if args.cmd == "doctor": return forward("story_os_doctor.py", [])
    if args.cmd == "runtime": return forward("runtime_router.py", [args.runtime_cmd, *args.extra])
    if args.cmd == "request": return forward("runtime_request.py", [args.request_cmd, *args.extra])
    if args.cmd == "image-model": return forward("image_model_policy.py", [args.image_model_cmd, *args.extra])
    if args.cmd == "capture-profile": return forward("capture_profile.py", [args.profile_cmd, *args.extra])
    if args.cmd == "regression": return forward("story_regression.py", [args.regression_cmd, *args.extra])
    if args.cmd == "migrate-v21": return forward("migrate_v21.py", [args.migration_cmd, *args.extra])
    if args.cmd == "regression-v21": return forward("regression_matrix_v21.py", [args.regression_v21_cmd, *args.extra])
    if args.cmd == "learning-index": return forward("account_learning_index.py", [args.learning_cmd, *args.extra])
    if args.cmd == "image-backend": return forward("codex_subscription_image.py", [args.backend_cmd, *args.extra])
    if args.cmd == "quota": return forward("quota_observability.py", [args.quota_cmd, str(Path(args.episode_dir).resolve()), *args.extra])
    if args.cmd == "cache-r2": return forward("multi_level_cache.py", [args.cache_cmd])
    if args.cmd == "golden": return forward("golden_episode_regression.py", [args.golden_cmd, *args.extra])
    if args.cmd == "resource" and args.resource_cmd=="register": return forward("resource_library.py", ["register", *args.extra])
    ep = Path(args.episode_dir).resolve()
    if args.cmd == "dag":
        extra=[args.dag_cmd, str(ep)]
        if args.codex: extra += ["--codex", args.codex]
        if args.dag_cmd in {"run","resume"}: extra += ["--timeout", str(args.timeout)]
        return forward("runtime_dag.py", extra)
    if args.cmd == "run":
        mode = "resume" if args.resume else "run"
        extra = [mode, str(ep)]
        if args.full_auto: extra.append("--full-auto")
        if args.codex: extra += ["--codex", args.codex]
        extra += ["--timeout", str(args.timeout)]
        if args.request_file: extra += ["--request-file", args.request_file]
        return forward("workflow_runner.py", extra)
    if args.cmd == "plan": return forward("workflow_runner.py", ["plan", str(ep)])
    if args.cmd == "performance": return forward("workflow_runner.py", ["performance", str(ep)])
    if args.cmd == "delegated-delivery": return forward("delegated_delivery.py", [args.delivery_cmd, str(ep), *args.extra])
    if args.cmd == "delegated-approval":
        extra = [args.approval_cmd, str(ep)]
        if args.kind: extra.append(args.kind)
        extra.extend(args.extra); return forward("delegated_approval.py", extra)
    if args.cmd == "checkpoint": return forward("runtime_checkpoint.py", [args.checkpoint_cmd, str(ep), *args.extra])
    if args.cmd == "concept": return forward("concept_ambition.py", [args.concept_cmd, str(ep), *args.extra])
    if args.cmd == "character": return forward("character_contract.py", [args.character_cmd, str(ep), *args.extra])
    if args.cmd == "handoff": return forward("preproduction_handoff.py", [args.handoff_cmd, str(ep), *args.extra])
    if args.cmd == "execution-r2": return forward("runtime_execution.py", [args.execution_cmd, str(ep), *args.extra])
    if args.cmd == "resource": return forward("resource_library.py", [args.resource_cmd, str(ep), *args.extra])
    if args.cmd == "intro": return forward("intro_policy.py", [args.intro_cmd, str(ep), *args.extra])
    if args.cmd == "environment": return forward("environment_contract.py", [args.environment_cmd, str(ep), *args.extra])
    if args.cmd == "frame-contract": return forward("frame_contract.py", [args.frame_contract_cmd, str(ep), *args.extra])
    if args.cmd == "visual-lock-v21": return forward("visual_lock_v21.py", [args.visual_lock_cmd, str(ep), *args.extra])
    if args.cmd == "image-scheduler": return forward("image_scheduler.py", [args.scheduler_cmd, str(ep), *args.extra])
    if args.cmd == "frame-scout": return forward("fast_frame_scout.py", [args.scout_cmd, str(ep), *args.extra])
    if args.cmd == "final-snapshot": return forward("final_candidate_snapshot.py", [args.snapshot_cmd, str(ep), *args.extra])
    if args.cmd == "observability": return forward("workflow_observability.py", [args.observe_cmd, str(ep)])
    if args.cmd == "post-publish": return forward("post_publish_review.py", [args.post_publish_cmd, str(ep), *args.extra])
    if args.cmd == "fingerprint": return forward("episode_fingerprint.py", [args.fingerprint_cmd, str(ep), *args.extra])
    if args.cmd == "quality": return forward("directing_quality.py", [args.quality_cmd, str(ep)])
    if args.cmd == "lineage": return forward("asset_lineage.py", [args.lineage_cmd, str(ep), *args.extra])
    if args.cmd == "audit-text": return forward("text_audit.py", [str(ep), *args.extra])
    if args.cmd == "transport": return forward("transport_guard.py", [args.transport_cmd, str(ep), *args.extra])
    if args.cmd == "text-revision": return forward("text_revision.py", [args.revision_cmd, str(ep), *args.extra])
    if args.cmd == "visual-profile": return forward("visual_profile.py", [args.profile_cmd, str(ep), *args.extra])
    if args.cmd == "approval": return forward("approval_lock.py", [args.approval_cmd, str(ep), *args.extra])
    if args.cmd == "release-package": return forward("release_package.py", [args.release_cmd, str(ep), *args.extra])
    if args.cmd == "status": return cmd_status(ep)
    if args.cmd == "next": return cmd_next(ep)
    if args.cmd == "checklist": return forward("final_checklist.py", [str(ep)] + (["--no-validators"] if args.no_validators else []))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
