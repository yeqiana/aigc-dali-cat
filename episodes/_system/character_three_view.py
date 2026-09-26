#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Optional preproduction three-view character identity anchors.

The manifest is user-supplied production input, not a generated Pixel Master.
When absent, StoryOS follows the existing Character Visual -> Visual Lock route.
When present, each character binds one front/side/back board that can be used as
an identity reference until a current-Episode Pixel Master supersedes it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import character_contract
import story_json

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_REL = Path("references/characters/three-view.json")
SCHEMA_VERSION = 1
VIEW_ORDER = ("front", "side", "back")


def _canonical_sha(data: dict) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def repo_rel(path: Path) -> str:
    return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()


def repo_asset(raw) -> Path:
    path = Path(str(raw))
    path = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    path.relative_to(ROOT.resolve())
    return path


def manifest_path(ep: Path) -> Path:
    return Path(ep).resolve() / MANIFEST_REL


def load(ep: Path) -> dict | None:
    path = manifest_path(ep)
    if not path.is_file():
        return None
    return story_json.read_json(path)


def manifest_sha256(ep: Path) -> str | None:
    data = load(ep)
    return _canonical_sha(data) if isinstance(data, dict) else None


def validate(ep: Path) -> list[str]:
    ep = Path(ep).resolve()
    data = load(ep)
    if data is None:
        return []
    errors = []
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append("character three-view schema_version must be 1")
    characters = data.get("characters")
    if not isinstance(characters, dict) or not characters:
        errors.append("character three-view characters missing")
        return errors
    contract = character_contract.load(ep) or {}
    expected_ids = {
        str(row.get("id") or "")
        for row in ((contract.get("cast") or {}).get("members") or [])
        if str(row.get("id") or "")
    }
    for cid, row in characters.items():
        cid = str(cid)
        if expected_ids and cid not in expected_ids:
            errors.append(f"character three-view unknown cast id: {cid}")
        if not isinstance(row, dict):
            errors.append(f"character three-view {cid} invalid")
            continue
        if tuple(row.get("views") or ()) != VIEW_ORDER:
            errors.append(f"character three-view {cid} views must be front/side/back")
        raw = row.get("board")
        if not raw:
            errors.append(f"character three-view {cid} board missing")
            continue
        try:
            asset = repo_asset(raw)
            if not asset.is_file():
                errors.append(f"character three-view {cid} board asset missing")
                continue
            actual = sha_file(asset)
            if actual.lower() != str(row.get("sha256") or "").lower():
                errors.append(f"character three-view {cid} board sha mismatch")
        except Exception:
            errors.append(f"character three-view {cid} board path invalid")
    return errors


def summary(ep: Path) -> dict:
    data = load(ep)
    if data is None:
        return {"applicable": False}
    errors = validate(ep)
    if errors:
        raise ValueError("invalid character three-view: " + "; ".join(errors[:8]))
    rows = {}
    for cid, row in sorted((data.get("characters") or {}).items()):
        rows[str(cid)] = {
            "board": row["board"],
            "sha256": row["sha256"],
            "views": list(VIEW_ORDER),
        }
    return {
        "applicable": True,
        "manifest_path": MANIFEST_REL.as_posix(),
        "manifest_sha256": manifest_sha256(ep),
        "characters": rows,
        "role": "PREPRODUCTION_IDENTITY_ANCHOR",
        "superseded_by": "character_pixel_master",
    }


def reference(ep: Path, character_id: str | None) -> dict | None:
    if not character_id:
        return None
    data = load(ep)
    if data is None:
        return None
    errors = validate(ep)
    if errors:
        raise ValueError("invalid character three-view: " + "; ".join(errors[:8]))
    row = (data.get("characters") or {}).get(str(character_id))
    if not isinstance(row, dict):
        return None
    return {
        "path": row["board"],
        "role": f"character_three_view:{character_id}",
        "kind": "identity",
        "sha256": row["sha256"],
        "character_id": str(character_id),
        "status": "PREPRODUCTION_LOCKED",
        "views": list(VIEW_ORDER),
        "authority_path": MANIFEST_REL.as_posix(),
    }


def register(ep: Path, character_id: str, board: Path) -> dict:
    ep = Path(ep).resolve()
    board = Path(board).resolve()
    board.relative_to(ROOT.resolve())
    if not board.is_file():
        raise ValueError(f"three-view board missing: {board}")
    contract = character_contract.load(ep) or {}
    valid_ids = {
        str(row.get("id") or "")
        for row in ((contract.get("cast") or {}).get("members") or [])
        if str(row.get("id") or "")
    }
    cid = str(character_id).strip()
    if valid_ids and cid not in valid_ids:
        raise ValueError(f"unknown character id: {cid}")
    data = load(ep) or {"schema_version": SCHEMA_VERSION, "characters": {}}
    data["schema_version"] = SCHEMA_VERSION
    data.setdefault("characters", {})[cid] = {
        "board": repo_rel(board),
        "sha256": sha_file(board),
        "views": list(VIEW_ORDER),
    }
    path = manifest_path(ep)
    path.parent.mkdir(parents=True, exist_ok=True)
    story_json.write_json(path, data)
    errors = validate(ep)
    if errors:
        raise ValueError("invalid character three-view after register: " + "; ".join(errors[:8]))
    return summary(ep)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("register")
    p.add_argument("episode_dir")
    p.add_argument("--character", required=True)
    p.add_argument("--board", required=True)
    p = sub.add_parser("validate")
    p.add_argument("episode_dir")
    p = sub.add_parser("show")
    p.add_argument("episode_dir")
    args = ap.parse_args()
    ep = Path(args.episode_dir).resolve()
    if args.cmd == "register":
        print(json.dumps(register(ep, args.character, Path(args.board)), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "show":
        print(json.dumps(summary(ep), ensure_ascii=False, indent=2))
        return 0
    errors = validate(ep)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 2
    print("VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
