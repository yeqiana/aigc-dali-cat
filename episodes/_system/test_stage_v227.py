#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import secrets
import time
from pathlib import Path

SYSTEM = Path(__file__).resolve().parent
ROOT = SYSTEM.parents[1]

import test_stage_v224 as v224
import test_stage_v225 as v225
import visual_profile_bridge_v224 as visual_bridge
import codex_subscription_image
from canvas_normalize import normalize

VERSION = "2.2.7"
NON_AUTHORITY = "NON_AUTHORITY_TEST_ONLY"
HISTORY_POLICY = "AUDIT_ONLY_NEVER_EXECUTION_INPUT"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def new_run_id() -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    return f"VT_{stamp}_{secrets.token_hex(2)}"


def resolve_scene(args) -> str:
    scene = (getattr(args, "scene", None) or "").strip()
    scene_file = getattr(args, "scene_file", None)
    if scene_file:
        scene = Path(scene_file).read_text(encoding="utf-8").strip()
    if not scene:
        raise SystemExit("visual test scene is empty")
    return scene


def run_meta_dir(ep: Path, run_id: str) -> Path:
    return ep / "meta" / "tests" / "visual" / run_id


def run_media_dir(ep: Path, run_id: str) -> Path:
    return ep / "media" / "tests" / "visual" / run_id


def latest_pointer_path(ep: Path) -> Path:
    return ep / "meta" / "tests" / "visual" / "latest.json"


def update_latest_pointer(ep: Path, run_id: str, status: str, report: str | None = None):
    # Convenience pointer only. Never read by prepare/finalize execution decisions.
    payload = {
        "version": VERSION,
        "pointer_type": "NON_AUTHORITY_NON_GATE_NON_REUSE",
        "history_policy": HISTORY_POLICY,
        "run_id": run_id,
        "status": status,
        "report": report,
        "updated_at": now(),
    }
    write_json(latest_pointer_path(ep), payload)


def prepare_run_dirs(ep: Path, run_id: str):
    md = run_meta_dir(ep, run_id)
    media = run_media_dir(ep, run_id)
    (md / "logs").mkdir(parents=True, exist_ok=False)
    media.mkdir(parents=True, exist_ok=False)
    return md, media


def visual_prepare(args):
    ep = v224.episode(args.episode_dir)

    # HARD RULE: no history lookup here.
    # Only current production-entry prerequisites are checked.
    v224.need_bootstrap(ep)
    v224.check_drift(ep)

    scene = resolve_scene(args)
    vc = visual_bridge.compile_prompt_contract(ep)
    w, h = v224.canvas(ep)

    run_id = new_run_id()
    md, media = prepare_run_dirs(ep, run_id)

    prompt = md / "prompt.txt"
    raw = media / "raw.png"
    out = media / "output.png"
    plan_path = md / "plan.json"
    report_path = md / "report.json"
    generation_path = md / "generation.json"

    prompt.write_text(scene + "\n", encoding="utf-8")

    plan = {
        "version": VERSION,
        "run_id": run_id,
        "test_type": "VISUAL_TEST",
        "status": "VISUAL_TEST_NATIVE_IMAGE_REQUIRED",
        "authority": NON_AUTHORITY,
        "promotion_allowed": False,
        "history_policy": HISTORY_POLICY,
        "reuse_previous_visual_test": False,
        "reuse_previous_image": False,
        "skip_if_previous_pass": False,
        "cache_hit_allowed": False,
        "route": "MAIN_SESSION_NATIVE_IMAGE",
        "requires": "BOOTSTRAP_VALIDATE_PASS",
        "requires_preproduction": False,
        "scene": scene,
        "prompt_file": str(prompt.relative_to(ep)),
        "raw_target": str(raw.relative_to(ep)),
        "output_target": str(out.relative_to(ep)),
        "report_target": str(report_path.relative_to(ep)),
        "generation_target": str(generation_path.relative_to(ep)),
        "visual_profile": {
            "profile_id": vc["profile_id"],
            "profile_path": vc["profile_path"],
            "profile_sha256": vc["profile_sha256"],
            "authority_source": vc.get("authority_source"),
            "capture_grammar": vc.get("capture_grammar"),
            "prompt_contract": vc["text"],
        },
        "image_model": {
            "requested": args.image_model,
            "strict": bool(args.strict_model),
        },
        "target_size": [w, h],
        "provider_size": codex_subscription_image.provider_size(w, h),
        "created_at": now(),
        "started_epoch": time.time(),
    }
    plan["native_instruction"] = (
        "This is a NEW Visual Test run. Do not inspect, reuse, compare, or skip because of any prior Visual Test. "
        "Use the CURRENT MAIN SESSION image generation tool exactly once. "
        "Do not spawn an isolated image worker. "
        f"Request model={args.image_model}. "
        "Use visual_profile.prompt_contract as mandatory context and scene as the scene request. "
        f"Save/copy the newly generated image to: {raw}. "
        "If generation succeeds, run: "
        f'python -X utf8 scripts/story_test.py visual-finalize "{ep}" --run-id "{run_id}". '
        "If the provider blocks/fails and no real image is produced, run: "
        f'python -X utf8 scripts/story_test.py visual-record-failure "{ep}" --run-id "{run_id}" '
        '--status GENERATION_BLOCKED --reason "<provider reason>".'
    )

    write_json(plan_path, plan)
    write_json(generation_path, {
        "version": VERSION,
        "run_id": run_id,
        "status": "IMAGE_GENERATION_REQUESTED",
        "requested_at": now(),
        "image_model": args.image_model,
        "history_policy": HISTORY_POLICY,
    })
    update_latest_pointer(ep, run_id, "VISUAL_TEST_NATIVE_IMAGE_REQUIRED", None)

    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


def load_run_plan(ep: Path, run_id: str) -> tuple[Path, dict]:
    if not run_id or not run_id.startswith("VT_"):
        raise SystemExit("VISUAL_TEST_RUN_ID_REQUIRED")
    plan_path = run_meta_dir(ep, run_id) / "plan.json"
    if not plan_path.is_file():
        raise SystemExit(f"VISUAL_TEST_RUN_NOT_FOUND: {run_id}")
    plan = read_json(plan_path)
    if plan.get("run_id") != run_id:
        raise SystemExit("VISUAL_TEST_RUN_ID_MISMATCH")
    return plan_path, plan


def visual_finalize(args):
    ep = v224.episode(args.episode_dir)
    v224.need_bootstrap(ep)
    v224.check_drift(ep)

    plan_path, plan = load_run_plan(ep, args.run_id)

    if plan.get("authority") != NON_AUTHORITY or plan.get("promotion_allowed") is not False:
        raise SystemExit("VISUAL_TEST_PLAN_AUTHORITY_INVALID")
    if plan.get("history_policy") != HISTORY_POLICY:
        raise SystemExit("VISUAL_TEST_HISTORY_POLICY_INVALID")
    if plan.get("status") != "VISUAL_TEST_NATIVE_IMAGE_REQUIRED":
        raise SystemExit(f"VISUAL_TEST_PLAN_STATE_INVALID: {plan.get('status')}")

    vc = visual_bridge.compile_prompt_contract(ep)
    expected = (plan.get("visual_profile") or {}).get("profile_sha256")
    if expected != vc["profile_sha256"]:
        raise SystemExit(
            f"VISUAL_TEST_PROFILE_STALE: plan={expected} current={vc['profile_sha256']}"
        )

    raw = ep / plan["raw_target"]
    out = ep / plan["output_target"]
    if not codex_subscription_image.valid_image(raw):
        raise SystemExit(
            f"VISUAL_TEST_IMAGE_MISSING_OR_INVALID: {raw}. "
            "No real image means no successful finalize."
        )

    w, h = [int(x) for x in plan["target_size"]]
    norm = normalize(raw, out, w, h)
    if not codex_subscription_image.valid_image(out):
        raise SystemExit(f"VISUAL_TEST_NORMALIZED_IMAGE_INVALID: {out}")

    elapsed = round(max(0.0, time.time() - float(plan.get("started_epoch") or time.time())), 2)
    report_path = ep / plan["report_target"]
    generation_path = ep / plan["generation_target"]

    report = {
        **plan,
        "version": VERSION,
        "status": "VISUAL_TEST_GENERATED_PENDING_REVIEW",
        "route": "MAIN_SESSION_NATIVE_IMAGE",
        "raw_sha256": sha256_file(raw),
        "output_sha256": sha256_file(out),
        "normalization": norm,
        "total_elapsed_seconds": elapsed,
        "generation_elapsed_seconds": args.generation_seconds,
        "review_required": True,
        "review_rule": (
            "NON_AUTHORITY_TEST_ONLY. History is audit-only and cannot be reused to satisfy future Visual Tests."
        ),
        "finalized_at": now(),
    }
    report.pop("native_instruction", None)
    write_json(report_path, report)

    write_json(generation_path, {
        "version": VERSION,
        "run_id": args.run_id,
        "status": "IMAGE_GENERATED",
        "generation_elapsed_seconds": args.generation_seconds,
        "raw_sha256": report["raw_sha256"],
        "output_sha256": report["output_sha256"],
        "recorded_at": now(),
    })

    plan["status"] = "VISUAL_TEST_NATIVE_IMAGE_CONSUMED"
    plan["finalized_report"] = str(report_path.relative_to(ep))
    write_json(plan_path, plan)
    update_latest_pointer(
        ep,
        args.run_id,
        "VISUAL_TEST_GENERATED_PENDING_REVIEW",
        str(report_path.relative_to(ep)),
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def visual_record_failure(args):
    ep = v224.episode(args.episode_dir)
    plan_path, plan = load_run_plan(ep, args.run_id)

    allowed = {
        "GENERATION_BLOCKED",
        "GENERATION_FAILED",
        "GENERATION_CANCELLED",
    }
    status = args.status.strip().upper()
    if status not in allowed:
        raise SystemExit("invalid failure status; expected GENERATION_BLOCKED|GENERATION_FAILED|GENERATION_CANCELLED")

    report_path = ep / plan["report_target"]
    generation_path = ep / plan["generation_target"]

    report = {
        "version": VERSION,
        "run_id": args.run_id,
        "test_type": "VISUAL_TEST",
        "status": status,
        "authority": NON_AUTHORITY,
        "promotion_allowed": False,
        "history_policy": HISTORY_POLICY,
        "scene": plan.get("scene"),
        "visual_profile": plan.get("visual_profile"),
        "image_model": plan.get("image_model"),
        "reason": args.reason,
        "generation_elapsed_seconds": args.generation_seconds,
        "created_at": plan.get("created_at"),
        "failed_at": now(),
        "raw_target": plan.get("raw_target"),
        "output_target": plan.get("output_target"),
        "real_image_created": False,
        "review_required": False,
    }
    write_json(report_path, report)
    write_json(generation_path, {
        "version": VERSION,
        "run_id": args.run_id,
        "status": status,
        "reason": args.reason,
        "generation_elapsed_seconds": args.generation_seconds,
        "recorded_at": now(),
    })

    plan["status"] = status
    plan["failure_report"] = str(report_path.relative_to(ep))
    write_json(plan_path, plan)
    update_latest_pointer(ep, args.run_id, status, str(report_path.relative_to(ep)))

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def visual_review(args):
    ep = v224.episode(args.episode_dir)
    _, plan = load_run_plan(ep, args.run_id)
    report_path = ep / plan["report_target"]
    if not report_path.is_file():
        raise SystemExit("VISUAL_TEST_REPORT_MISSING")
    report = read_json(report_path)
    if report.get("status") != "VISUAL_TEST_GENERATED_PENDING_REVIEW":
        raise SystemExit(f"VISUAL_TEST_NOT_REVIEWABLE: {report.get('status')}")

    decision = args.decision.strip().upper()
    if decision not in {"PASS", "FAIL"}:
        raise SystemExit("decision must be PASS or FAIL")
    report["status"] = f"VISUAL_TEST_REVIEW_{decision}"
    report["review"] = {
        "decision": decision,
        "note": args.note,
        "reviewed_at": now(),
    }
    write_json(report_path, report)
    update_latest_pointer(ep, args.run_id, report["status"], str(report_path.relative_to(ep)))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def history(args):
    ep = v224.episode(args.episode_dir)
    base = ep / "meta" / "tests" / "visual"
    rows = []
    if base.is_dir():
        for child in sorted(base.iterdir(), reverse=True):
            if not child.is_dir() or not child.name.startswith("VT_"):
                continue
            report = child / "report.json"
            plan = child / "plan.json"
            data = read_json(report) if report.is_file() else (read_json(plan) if plan.is_file() else {})
            rows.append({
                "run_id": child.name,
                "status": data.get("status"),
                "created_at": data.get("created_at"),
                "scene": data.get("scene"),
                "report": str(report.relative_to(ep)) if report.is_file() else None,
            })
            if len(rows) >= args.limit:
                break
    print(json.dumps({
        "version": VERSION,
        "history_policy": HISTORY_POLICY,
        "execution_note": "This command is for manual audit only. Visual Test prepare never calls it.",
        "runs": rows,
    }, ensure_ascii=False, indent=2))
    return 0


def check(args):
    ep = v224.episode(args.episode_dir)
    base_result = {
        "version": VERSION,
        "history_policy": HISTORY_POLICY,
        "append_only": True,
        "reuse_previous_visual_test": False,
        "skip_if_previous_pass": False,
        "latest_pointer_is_execution_input": False,
    }
    print(json.dumps(base_result, ensure_ascii=False, indent=2))
    return v225.check(args)


def self_test(args):
    assert HISTORY_POLICY == "AUDIT_ONLY_NEVER_EXECUTION_INPUT"
    assert new_run_id().startswith("VT_")
    assert NON_AUTHORITY == "NON_AUTHORITY_TEST_ONLY"
    assert codex_subscription_image.provider_size(1080, 1350) == "1024x1280"
    print("STORY OS V2.2.7 VISUAL TEST APPEND-ONLY RUNS SELF-TEST PASS")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Story OS V2.2.7 Visual Test Append-Only Runs")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("check")
    p.add_argument("episode_dir")
    p.set_defaults(func=check)

    p = sub.add_parser("visual")
    p.add_argument("episode_dir")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--scene")
    g.add_argument("--scene-file")
    p.add_argument("--image-model", default="gpt-image-2")
    p.add_argument("--strict-model", action="store_true")
    p.set_defaults(func=visual_prepare)

    p = sub.add_parser("visual-finalize")
    p.add_argument("episode_dir")
    p.add_argument("--run-id", required=True)
    p.add_argument("--generation-seconds", type=float)
    p.set_defaults(func=visual_finalize)

    p = sub.add_parser("visual-record-failure")
    p.add_argument("episode_dir")
    p.add_argument("--run-id", required=True)
    p.add_argument("--status", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--generation-seconds", type=float)
    p.set_defaults(func=visual_record_failure)

    p = sub.add_parser("visual-review")
    p.add_argument("episode_dir")
    p.add_argument("--run-id", required=True)
    p.add_argument("--decision", required=True)
    p.add_argument("--note")
    p.set_defaults(func=visual_review)

    p = sub.add_parser("visual-history")
    p.add_argument("episode_dir")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=history)

    p = sub.add_parser("production-smoke")
    p.add_argument("episode_dir")
    p.add_argument("--frame", required=True)
    p.add_argument("--prompt-file", required=True)
    p.add_argument("--image-model", default="gpt-image-2")
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--codex")
    p.set_defaults(func=v224.production_smoke)

    p = sub.add_parser("self-test")
    p.set_defaults(func=self_test)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
