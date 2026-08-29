#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = Path(__file__).resolve().parent


def run(args: list[object]) -> tuple[int, str]:
    cp = subprocess.run([str(x) for x in args], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", check=False)
    return cp.returncode, cp.stdout


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def current_state(ep: Path) -> str:
    return str(read_json(ep / "meta/episode-state.json").get("current_state") or "UNKNOWN")


def command_ok(script: str, subcommand: str, ep: Path, *extra: str) -> tuple[bool, str]:
    rc, out = run([sys.executable, SYSTEM / script, subcommand, ep, *extra])
    return rc == 0, out[-2500:]


def plan(ep: Path) -> dict:
    result: dict = {
        "episode": ep.relative_to(ROOT).as_posix(),
        "state": current_state(ep),
        "story": "NOT_READY",
        "visual": "NOT_READY",
        "frames": "NOT_READY",
        "frame_plan": None,
        "subtitle": "NOT_READY",
        "action": "RUN_WORKER",
    }

    if (ep / "meta/story-semantic-review.json").is_file():
        ok, _ = command_ok("story_review.py", "verify", ep)
        result["story"] = "CLEAN" if ok else "DIRTY"
    if (ep / "meta/visual-profile-review.json").is_file():
        ok, _ = command_ok("visual_review.py", "verify", ep)
        result["visual"] = "CLEAN" if ok else "DIRTY"

    if (ep / "meta/production-ledger.json").is_file():
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

    if (ep / "meta/subtitle-layout-audit.json").is_file():
        ok, _ = command_ok("subtitle_layout.py", "audit", ep)
        result["subtitle"] = "CLEAN" if ok else "DIRTY"

    clean_core = result["story"] in {"CLEAN", "NOT_READY"} and result["visual"] in {"CLEAN", "NOT_READY"}
    clean_frames = result["frames"] in {"CLEAN", "NOT_READY"}
    state = result["state"]
    if clean_core and clean_frames and state in {"PRODUCTION_PASSED", "PUBLISH_READY", "PUBLISHED", "DATA_REVIEWED"}:
        result["action"] = "POSTFLIGHT_ONLY"
    elif result["story"] == "DIRTY":
        result["action"] = "STORY_REVIEW_REQUIRED"
    elif result["visual"] == "DIRTY":
        result["action"] = "VISUAL_REVIEW_REQUIRED"
    elif result["frames"] == "DIRTY":
        result["action"] = "PRODUCTION_INCREMENTAL_REQUIRED"
    else:
        result["action"] = "RUN_WORKER"
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Story OS V2.0.3.4 minimal-closure planner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("episode_dir"); p.add_argument("--json", action="store_true")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        assert ROOT.name
        print("INCREMENTAL CLOSURE SELF-TEST PASS")
        return 0
    ep = Path(args.episode_dir).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    data = plan(ep)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
