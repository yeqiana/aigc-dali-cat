#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Iterable

import story_json
import production_ledger

ROOT = Path(__file__).resolve().parents[2]
FROZEN_STATES = {"PRODUCTION_PASSED", "PUBLISH_READY", "PUBLISHED", "DATA_REVIEWED"}
MEDIA_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".mp4", ".mov", ".avi", ".mkv"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def _read(path: Path) -> dict:
    return story_json.read_json(path, default={})


def _episode_prefix(ep: Path) -> str:
    return repo_relative(ep).rstrip("/") + "/"


def _normalize_expected(ep: Path, raw_path: object, raw_sha: object, role: str) -> dict | None:
    path_text = str(raw_path or "").strip().replace("\\", "/")
    sha = str(raw_sha or "").strip().lower()
    if not path_text or len(sha) != 64:
        return None
    if Path(path_text).suffix.lower() not in MEDIA_EXTS:
        return None
    prefix = _episode_prefix(ep)
    if not path_text.startswith(prefix):
        return None
    relative = path_text[len(prefix):]
    return {
        "role": role,
        "target": path_text,
        "episode_relative_path": relative,
        "expected_sha256": sha,
    }


def _snapshot_rows(ep: Path) -> Iterable[dict]:
    snapshot = _read(ep / "meta/final-candidate-snapshot.json")
    lock = snapshot.get("lock") if isinstance(snapshot.get("lock"), dict) else {}
    cover = lock.get("cover") if isinstance(lock.get("cover"), dict) else None
    if cover:
        row = _normalize_expected(ep, cover.get("path"), cover.get("sha256"), "snapshot:cover")
        if row:
            yield row
    for section in ("body", "delivery_files"):
        for idx, item in enumerate(lock.get(section) or []):
            if not isinstance(item, dict):
                continue
            row = _normalize_expected(
                ep,
                item.get("path"),
                item.get("sha256"),
                f"snapshot:{section}:{idx + 1}",
            )
            if row:
                yield row


def _ledger_rows(ep: Path) -> Iterable[dict]:
    ledger = production_ledger.load_authority(ep, default={}) or {}
    for frame_key, frame in (ledger.get("frames") or {}).items():
        if not isinstance(frame, dict):
            continue
        for field in ("approved_asset", "current_candidate"):
            asset = frame.get(field)
            if not isinstance(asset, dict):
                continue
            row = _normalize_expected(
                ep,
                asset.get("path"),
                asset.get("sha256"),
                f"ledger:{frame_key}:{field}",
            )
            if row:
                yield row


def _visual_lock_rows(ep: Path) -> Iterable[dict]:
    gates = _read(ep / "meta/story-gates.json")
    visual = gates.get("visual") if isinstance(gates.get("visual"), dict) else {}
    calibration = visual.get("calibration") if isinstance(visual.get("calibration"), dict) else {}
    for idx, item in enumerate(calibration.get("items") or []):
        if not isinstance(item, dict):
            continue
        row = _normalize_expected(
            ep,
            item.get("asset_path"),
            item.get("sha256"),
            f"visual_lock:{item.get('id') or idx + 1}",
        )
        if row:
            yield row


def expected_assets(ep: Path) -> tuple[list[dict], list[str]]:
    merged: dict[str, dict] = {}
    conflicts: list[str] = []
    for row in (*_snapshot_rows(ep), *_ledger_rows(ep), *_visual_lock_rows(ep)):
        target = row["target"]
        current = merged.get(target)
        if current is None:
            merged[target] = {**row, "roles": [row["role"]]}
            continue
        if current["expected_sha256"] != row["expected_sha256"]:
            conflicts.append(
                f"SHA authority conflict for {target}: {current['expected_sha256']} != {row['expected_sha256']}"
            )
            continue
        current["roles"].append(row["role"])
    return sorted(merged.values(), key=lambda row: row["target"]), conflicts


def build_plan(episode_dir: Path, source_episode_dir: Path) -> dict:
    ep = Path(episode_dir).resolve()
    source_ep = Path(source_episode_dir).resolve()
    state = _read(ep / "meta/episode-state.json")
    current_state = str(state.get("current_state") or "UNKNOWN")
    blockers: list[str] = []
    if current_state not in FROZEN_STATES:
        blockers.append(f"episode must be frozen before evidence-preserving recovery; state={current_state}")
    if not source_ep.is_dir():
        blockers.append(f"source episode directory missing: {source_ep}")

    assets, authority_conflicts = expected_assets(ep)
    blockers.extend(authority_conflicts)
    rows: list[dict] = []
    for asset in assets:
        target = ROOT / asset["target"]
        source = source_ep / asset["episode_relative_path"]
        row = dict(asset)
        row["source"] = str(source)
        row["target_exists"] = target.is_file()
        row["source_exists"] = source.is_file()
        if target.is_file():
            target_sha = sha256_file(target)
            row["target_sha256"] = target_sha
            if target_sha == asset["expected_sha256"]:
                row["status"] = "PRESENT_MATCH"
            else:
                row["status"] = "TARGET_SHA_DRIFT"
                blockers.append(f"target SHA drift: {asset['target']}")
            rows.append(row)
            continue
        if not source.is_file():
            row["status"] = "SOURCE_MISSING"
            blockers.append(f"recovery source missing: {source}")
            rows.append(row)
            continue
        source_sha = sha256_file(source)
        row["source_sha256"] = source_sha
        if source_sha != asset["expected_sha256"]:
            row["status"] = "SOURCE_SHA_MISMATCH"
            blockers.append(
                f"source SHA mismatch: {source}; expected={asset['expected_sha256']} actual={source_sha}"
            )
        else:
            row["status"] = "RESTORABLE"
        rows.append(row)

    restorable = [row for row in rows if row["status"] == "RESTORABLE"]
    return {
        "schema_version": 1,
        "policy": "restore_missing_bytes_only_never_rewrite_frozen_evidence",
        "episode": repo_relative(ep),
        "source_episode": str(source_ep),
        "episode_state": current_state,
        "asset_count": len(rows),
        "restorable_count": len(restorable),
        "present_match_count": sum(1 for row in rows if row["status"] == "PRESENT_MATCH"),
        "blocked": bool(blockers),
        "blockers": blockers,
        "assets": rows,
    }


def restore(episode_dir: Path, source_episode_dir: Path) -> dict:
    plan = build_plan(episode_dir, source_episode_dir)
    if plan["blocked"]:
        raise RuntimeError("frozen media recovery blocked: " + "; ".join(plan["blockers"][:8]))
    created: list[Path] = []
    try:
        for row in plan["assets"]:
            if row["status"] != "RESTORABLE":
                continue
            source = Path(row["source"])
            target = ROOT / row["target"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            if sha256_file(target) != row["expected_sha256"]:
                raise RuntimeError(f"post-copy SHA mismatch: {target}")
            created.append(target)
    except Exception:
        for target in reversed(created):
            target.unlink(missing_ok=True)
        raise
    verified = build_plan(episode_dir, source_episode_dir)
    if verified["blocked"] or any(row["status"] != "PRESENT_MATCH" for row in verified["assets"]):
        for target in reversed(created):
            target.unlink(missing_ok=True)
        raise RuntimeError("post-recovery verification failed")
    return {
        **verified,
        "status": "RESTORED",
        "restored_count": len(created),
        "restored_paths": [repo_relative(path) for path in created],
        "evidence_rewritten": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Recover missing frozen Episode media by existing SHA evidence")
    sub = ap.add_subparsers(dest="command", required=True)
    for command in ("plan", "restore"):
        parser = sub.add_parser(command)
        parser.add_argument("episode_dir", type=Path)
        parser.add_argument("--source-episode", type=Path, required=True)
    args = ap.parse_args()
    if args.command == "plan":
        print(json.dumps(build_plan(args.episode_dir, args.source_episode), ensure_ascii=False, indent=2))
        return 0
    result = restore(args.episode_dir, args.source_episode)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
