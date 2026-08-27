#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATES = [
    "IDEA_LOCKED",
    "STORYBOARD_LOCKED",
    "VISUAL_CALIBRATED",
    "PRODUCTION_PASSED",
    "PUBLISH_READY",
    "PUBLISHED",
    "DATA_REVIEWED",
]
STATE_FILE = Path("meta/episode-state.json")
MANIFEST_FILE = Path("meta/release-manifest.json")
GATES_FILE = Path("meta/story-gates.json")
SYSTEM_VERSION = "1.3"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def ensure_episode_dir(raw: str) -> Path:
    p = Path(raw).resolve()
    if not p.exists() or not p.is_dir():
        raise SystemExit(f"episode directory not found: {p}")
    return p


def new_gates(episode_id: str) -> dict:
    return {
        "schema_version": 1,
        "tool_version": SYSTEM_VERSION,
        "episode_id": episode_id,
        "story": {
            "recent5_checked": False,
            "four_locks_diff_count": 0,
            "mechanism_skin_swap_veto": False,
            "task_closed": False,
            "competing_explanations": 0,
            "hook_frames": [1, 2, 3],
            "escalation_frames": [],
            "climax_frame": None,
            "payoff_frame": None,
        },
        "visual": {
            "admission_frames": [],
            "continuity": {
                "required": ["location", "key_prop", "weather_time"],
                "anchors": {
                    "protagonist": None,
                    "location": None,
                    "key_prop": None,
                    "wardrobe": None,
                    "weather_time": None,
                },
            },
        },
        "subtitles": {
            "required": True,
            "sound_card_completed": False,
        },
        "locks": {
            "edit_mode": "none",
            "assets": [],
        },
        "reviews": {
            "story": "pending",
            "authenticity": "pending",
            "continuity": "pending",
            "visual_admission": "pending",
            "subtitle": "pending",
            "production": "pending",
            "recommendation_fit": "pending",
            "publish": "pending",
        },
    }


def init_cmd(args: argparse.Namespace) -> None:
    episode_dir = ensure_episode_dir(args.episode_dir)
    state_path = episode_dir / STATE_FILE
    manifest_path = episode_dir / MANIFEST_FILE
    gates_path = episode_dir / GATES_FILE
    if state_path.exists() or manifest_path.exists() or gates_path.exists():
        raise SystemExit("meta already exists; refusing to overwrite")

    at = now_iso()
    state = {
        "schema_version": 1,
        "tool_version": SYSTEM_VERSION,
        "episode_id": args.id,
        "series": args.series,
        "title": args.title,
        "current_state": "IDEA_LOCKED",
        "updated_at": at,
        "history": [
            {
                "state": "IDEA_LOCKED",
                "at": at,
                "note": args.note or "项目已完成选题与核心故事锁定",
            }
        ],
    }
    manifest = {
        "schema_version": 1,
        "tool_version": SYSTEM_VERSION,
        "episode": {
            "id": args.id,
            "series": args.series,
            "title": args.title,
            "format": args.format,
            "aspect_ratio": args.aspect_ratio,
        },
        "release": {
            "version": None,
            "body_frame_count": args.frame_count,
            "publish_dir": None,
            "body_glob": "[0-9][0-9].png",
            "cover_path": None,
            "contact_sheet_path": None,
        },
        "artifacts": {
            "story": None,
            "storyboard": None,
            "visual_spec": None,
            "captions": None,
            "publish_copy": None,
            "production_review": None,
            "propagation_card": None,
        },
        "quality": {
            "production_gate": "pending",
            "propagation_score": None,
            "s_min_score": None,
            "propagation_decision": "pending",
            "publish_decision": "hold",
            "decision_note": None,
        },
        "publication": {
            "platform": "douyin",
            "actual_title": None,
            "description": None,
            "topics": [],
            "pinned_comment": None,
            "published_at": None,
            "timing_window": None,
            "post_url": None,
        },
        "data_review": {
            "report_path": "reports/数据验收报告.md",
            "completed_checkpoints": [],
            "first_hour_metrics": {
                "captured_at": None,
                "exposure": None,
                "plays": None,
                "likes": None,
                "comments": None,
                "saves": None,
                "shares": None,
                "followers_gained": None,
                "profile_visits": None,
                "avg_images_viewed": None,
                "swipe_away_rate": None,
                "caption_expand_rate": None,
            },
        },
    }
    save_json(state_path, state)
    save_json(manifest_path, manifest)
    save_json(gates_path, new_gates(args.id))
    print(f"initialized: {episode_dir}")
    print(f"state   : {state_path}")
    print(f"manifest: {manifest_path}")
    print(f"gates   : {gates_path}")


def migrate_gates_cmd(args: argparse.Namespace) -> None:
    episode_dir = ensure_episode_dir(args.episode_dir)
    state_path = episode_dir / STATE_FILE
    manifest_path = episode_dir / MANIFEST_FILE
    gates_path = episode_dir / GATES_FILE
    if gates_path.exists():
        raise SystemExit(f"story gates already exist: {gates_path}")
    if not state_path.exists() or not manifest_path.exists():
        raise SystemExit("legacy episode must already have episode-state.json + release-manifest.json")
    state = load_json(state_path)
    manifest = load_json(manifest_path)
    episode_id = state.get("episode_id") or (manifest.get("episode") or {}).get("id")
    if not isinstance(episode_id, str) or not episode_id.strip():
        raise SystemExit("cannot determine episode id")
    gates = new_gates(episode_id)
    gates["migration"] = {
        "legacy": True,
        "from_state_tool_version": state.get("tool_version"),
        "from_manifest_tool_version": manifest.get("tool_version"),
        "created_at": now_iso(),
        "note": args.note,
    }
    save_json(gates_path, gates)
    print(f"created: {gates_path}")
    print("Next: fill real gate evidence, then validate/transition. No stage was changed.")


def transition_cmd(args: argparse.Namespace) -> None:
    episode_dir = ensure_episode_dir(args.episode_dir)
    state_path = episode_dir / STATE_FILE
    if not state_path.exists():
        raise SystemExit(f"missing state file: {state_path}")

    data = load_json(state_path)
    current = data.get("current_state")
    target = args.target
    if current not in STATES:
        raise SystemExit(f"invalid current_state: {current!r}")
    if target == current:
        raise SystemExit(f"already in {target}")

    cur_idx = STATES.index(current)
    tgt_idx = STATES.index(target)
    if tgt_idx == cur_idx + 1:
        mode = "advance"
        validator = Path(__file__).with_name("validate_episode.py")
        result = subprocess.run(
            [sys.executable, str(validator), str(episode_dir), "--target", target],
            check=False,
        )
        if result.returncode != 0:
            raise SystemExit(f"target gate failed; state remains {current}")
    elif tgt_idx < cur_idx and args.rewind:
        mode = "rewind"
    else:
        raise SystemExit(
            f"illegal transition: {current} -> {target}; "
            "forward transitions must be adjacent, backward transitions require --rewind"
        )

    at = now_iso()
    data["current_state"] = target
    data["updated_at"] = at
    data["tool_version"] = SYSTEM_VERSION
    data.setdefault("history", []).append(
        {"state": target, "at": at, "mode": mode, "note": args.note}
    )
    save_json(state_path, data)
    print(f"{current} -> {target}")


def show_cmd(args: argparse.Namespace) -> None:
    episode_dir = ensure_episode_dir(args.episode_dir)
    data = {
        "state": load_json(episode_dir / STATE_FILE),
        "manifest": load_json(episode_dir / MANIFEST_FILE),
    }
    gates = episode_dir / GATES_FILE
    if gates.exists():
        data["gates"] = load_json(gates)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="DALI CAT episode state machine V1.3")
    sub = p.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="initialize state + release manifest + story gates")
    init.add_argument("episode_dir")
    init.add_argument("--id", required=True)
    init.add_argument("--series", required=True)
    init.add_argument("--title", required=True)
    init.add_argument("--frame-count", type=int, default=20)
    init.add_argument("--format", default="douyin_photo_carousel")
    init.add_argument("--aspect-ratio", default="9:16")
    init.add_argument("--note")
    init.set_defaults(func=init_cmd)

    mg = sub.add_parser("migrate-gates", help="add story-gates.json to a legacy episode without changing state")
    mg.add_argument("episode_dir")
    mg.add_argument("--note", default="旧剧集重新进入制作，接入 Story OS V1.1 门禁")
    mg.set_defaults(func=migrate_gates_cmd)

    tr = sub.add_parser("transition", help="move to next state or explicitly rewind")
    tr.add_argument("episode_dir")
    tr.add_argument("target", choices=STATES)
    tr.add_argument("--note", required=True)
    tr.add_argument("--rewind", action="store_true")
    tr.set_defaults(func=transition_cmd)

    show = sub.add_parser("show", help="show state + manifest + gates")
    show.add_argument("episode_dir")
    show.set_defaults(func=show_cmd)
    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
