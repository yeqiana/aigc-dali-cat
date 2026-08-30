#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from story_os_contract import canonical_stages

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = Path(__file__).resolve().parent
STATES = canonical_stages()


def run(args: list[object]) -> tuple[int, str]:
    cp = subprocess.run([str(x) for x in args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", check=False)
    return cp.returncode, cp.stdout


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def current_state(ep: Path) -> str:
    return str(read_json(ep / "meta/episode-state.json").get("current_state") or "UNKNOWN")


def state_at_least(state: str, target: str) -> bool:
    return state in STATES and STATES.index(state) >= STATES.index(target)


def command_ok(script: str, subcommand: str, ep: Path, *extra: str) -> tuple[bool, str]:
    rc, out = run([sys.executable, SYSTEM / script, subcommand, ep, *extra])
    return rc == 0, out[-2500:]


def subtitle_required(ep: Path) -> bool:
    gates = read_json(ep / "meta/story-gates.json")
    value = ((gates.get("subtitles") or {}).get("required"))
    return value is not False


def plan(ep: Path) -> dict:
    state = current_state(ep)
    result: dict = {
        "episode": ep.relative_to(ROOT).as_posix(),
        "state": state,
        "story": "NOT_APPLICABLE",
        "visual": "NOT_APPLICABLE",
        "frames": "NOT_APPLICABLE",
        "frame_plan": None,
        "subtitle": "NOT_APPLICABLE",
        "action": "RUN_WORKER",
        "missing": [],
    }

    story_path = ep / "meta/story-semantic-review.json"
    if story_path.is_file():
        ok, _ = command_ok("story_review.py", "verify", ep)
        result["story"] = "CLEAN" if ok else "DIRTY"
    elif state_at_least(state, "STORYBOARD_LOCKED"):
        result["story"] = "MISSING"; result["missing"].append("meta/story-semantic-review.json")

    visual_path = ep / "meta/visual-profile-review.json"
    if visual_path.is_file():
        ok, _ = command_ok("visual_review.py", "verify", ep)
        result["visual"] = "CLEAN" if ok else "DIRTY"
    elif state_at_least(state, "VISUAL_CALIBRATED"):
        result["visual"] = "MISSING"; result["missing"].append("meta/visual-profile-review.json")

    ledger = ep / "meta/production-ledger.json"
    if ledger.is_file():
        rc, out = run([sys.executable, SYSTEM / "incremental_frame_review.py", "plan", ep])
        if rc == 0:
            try:
                fp = json.loads(out)
            except Exception:
                fp = {"action": "ERROR", "raw": out[-1000:]}
            result["frame_plan"] = fp
            result["frames"] = "CLEAN" if fp.get("action") in {"NOOP", "NOT_REQUIRED"} else "DIRTY"
        else:
            result["frames"] = "DIRTY"
            result["frame_plan"] = {"action": "ERROR", "raw": out[-1500:]}
    elif state_at_least(state, "PRODUCTION_PASSED"):
        result["frames"] = "MISSING"; result["missing"].append("meta/production-ledger.json")

    audit = ep / "meta/subtitle-layout-audit.json"
    if subtitle_required(ep):
        if audit.is_file():
            ok, _ = command_ok("subtitle_layout.py", "audit", ep)
            result["subtitle"] = "CLEAN" if ok else "DIRTY"
        elif state_at_least(state, "PUBLISH_READY"):
            result["subtitle"] = "MISSING"; result["missing"].append("meta/subtitle-layout-audit.json")
    else:
        result["subtitle"] = "NOT_APPLICABLE"

    ordered = [result["story"], result["visual"], result["frames"], result["subtitle"]]
    if "MISSING" in ordered:
        result["action"] = "MISSING_EVIDENCE"
    elif result["story"] == "DIRTY":
        result["action"] = "STORY_REVIEW_REQUIRED"
    elif result["visual"] == "DIRTY":
        result["action"] = "VISUAL_REVIEW_REQUIRED"
    elif result["frames"] == "DIRTY":
        result["action"] = "PRODUCTION_INCREMENTAL_REQUIRED"
    elif result["subtitle"] == "DIRTY":
        result["action"] = "SUBTITLE_REVIEW_REQUIRED"
    else:
        clean_core = all(x in {"CLEAN", "NOT_APPLICABLE"} for x in (result["story"], result["visual"], result["frames"]))
        release_ready = result["subtitle"] in {"CLEAN", "NOT_APPLICABLE"}
        if clean_core and release_ready and state in {"PUBLISH_READY", "PUBLISHED", "DATA_REVIEWED"}:
            result["action"] = "POSTFLIGHT_ONLY"
        elif clean_core and release_ready and state == "PRODUCTION_PASSED":
            # Only safe when release text/subtitle evidence already exists.
            result["action"] = "POSTFLIGHT_ONLY" if (ep / "meta/text-audit.json").is_file() else "RUN_WORKER"
        else:
            result["action"] = "RUN_WORKER"
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Story OS V2.1 state-aware minimal-closure planner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("episode_dir"); p.add_argument("--json", action="store_true")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        assert state_at_least("PUBLISH_READY", "STORYBOARD_LOCKED")
        assert not state_at_least("IDEA_LOCKED", "STORYBOARD_LOCKED")
        print("INCREMENTAL CLOSURE V2.1 SELF-TEST PASS")
        return 0
    ep = Path(args.episode_dir).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    try:
        ep.relative_to(ROOT.resolve())
    except ValueError:
        raise SystemExit("episode must be inside repository")
    print(json.dumps(plan(ep), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
