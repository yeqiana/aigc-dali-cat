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


def init_cmd(args: argparse.Namespace) -> None:
    episode_dir = ensure_episode_dir(args.episode_dir)
    state_path = episode_dir / STATE_FILE
    manifest_path = episode_dir / MANIFEST_FILE
    if state_path.exists() or manifest_path.exists():
        raise SystemExit("meta already exists; refusing to overwrite")

    at = now_iso()
    state = {
        "schema_version": 1,
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
            "post_url": None,
        },
        "data_review": {
            "report_path": "reports/数据验收报告.md",
            "completed_checkpoints": [],
        },
    }
    save_json(state_path, state)
    save_json(manifest_path, manifest)
    print(f"initialized: {episode_dir}")
    print(f"state: {state_path}")
    print(f"manifest: {manifest_path}")


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
    data.setdefault("history", []).append(
        {"state": target, "at": at, "mode": mode, "note": args.note}
    )
    save_json(state_path, data)
    print(f"{current} -> {target}")


def show_cmd(args: argparse.Namespace) -> None:
    episode_dir = ensure_episode_dir(args.episode_dir)
    data = load_json(episode_dir / STATE_FILE)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Lightweight episode state machine")
    sub = p.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="initialize state + draft manifest")
    init.add_argument("episode_dir")
    init.add_argument("--id", required=True)
    init.add_argument("--series", required=True)
    init.add_argument("--title", required=True)
    init.add_argument("--frame-count", type=int, default=20)
    init.add_argument("--format", default="douyin_photo_carousel")
    init.add_argument("--aspect-ratio", default="9:16")
    init.add_argument("--note")
    init.set_defaults(func=init_cmd)

    tr = sub.add_parser("transition", help="move to next state or explicitly rewind")
    tr.add_argument("episode_dir")
    tr.add_argument("target", choices=STATES)
    tr.add_argument("--note", required=True)
    tr.add_argument("--rewind", action="store_true")
    tr.set_defaults(func=transition_cmd)

    show = sub.add_parser("show", help="show current state")
    show.add_argument("episode_dir")
    show.set_defaults(func=show_cmd)
    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
