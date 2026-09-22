#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import episode_discovery
import frame_scout_persistence
import story_json
from scripts.phase9_runtime_launcher import load_runtime_env_file


def scan() -> dict:
    rows, errors = [], []
    for ep in episode_discovery.iter_episode_roots(ROOT / "episodes"):
        ep = Path(ep).resolve()
        root = ep / frame_scout_persistence.REL
        if not root.is_dir():
            continue
        for path in sorted(root.glob("[0-9][0-9].json")):
            try:
                payload = story_json.read_json(path, default={}) or {}
                frame = int(payload.get("frame") or path.stem)
                if frame < 1 or not str(payload.get("decision") or "").strip():
                    raise ValueError("frame/decision missing")
                rows.append({"episode": ep, "path": path, "frame": frame, "payload": payload})
            except Exception as exc:
                errors.append(f"invalid frame scout {path}: {exc}")
    return {"rows": rows, "errors": errors}


def apply(plan: dict, *, reconcile: bool, delete_after_reconcile: bool) -> dict:
    if plan["errors"]:
        raise ValueError("frame scout scan failed: " + "; ".join(plan["errors"][:10]))
    if delete_after_reconcile and not reconcile:
        raise ValueError("--delete-after-reconcile requires --reconcile")
    written = reconciled = 0
    verified: list[Path] = []
    for row in plan["rows"]:
        saved = frame_scout_persistence.persist(row["episode"], row["payload"])
        if not saved.get("mysql_written"):
            raise RuntimeError(f"frame scout MySQL write unavailable: {row['path']}")
        written += 1
        if reconcile:
            loaded = frame_scout_persistence.load(row["episode"], row["frame"])
            if loaded != row["payload"]:
                raise ValueError(f"frame scout reconcile mismatch: {row['path']}")
            reconciled += 1
            verified.append(row["path"])
    deleted = 0
    if delete_after_reconcile:
        if reconciled != len(plan["rows"]):
            raise RuntimeError("refuse partial frame scout delete")
        for path in verified:
            path.unlink()
            deleted += 1
    return {"written": written, "reconciled": reconciled, "deleted": deleted}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--reconcile", action="store_true")
    ap.add_argument("--delete-after-reconcile", action="store_true")
    ap.add_argument("--runtime-env-file", default=str(ROOT / ".storyos/runtime-launcher/runtime.env"))
    args = ap.parse_args(argv)
    env, loaded = load_runtime_env_file(Path(args.runtime_env_file), dict(os.environ))
    os.environ.update(env)
    plan = scan()
    summary = {
        "mode": "apply" if args.apply else "dry-run",
        "files": len(plan["rows"]),
        "errors": plan["errors"],
        "runtime_env_keys": list(loaded),
        "secret_values_printed": False,
    }
    if args.apply:
        summary["result"] = apply(
            plan,
            reconcile=args.reconcile,
            delete_after_reconcile=args.delete_after_reconcile,
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not plan["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
