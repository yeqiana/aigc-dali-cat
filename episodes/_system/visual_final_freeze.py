#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final Visual Freeze for Story OS V2.6.0.

Once actual-pixel final review passes, freeze only visual inputs:
image SHA + Frame Contract SHA + visual context hashes.
Caption/title/description edits do NOT invalidate this freeze.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import frame_contract
import frame_semantic_review as base
from final_acceptance import valid as acceptance_valid

ROOT = Path(__file__).resolve().parents[2]
REL = Path("meta/visual-final-freeze.json")

def _row(ep: Path, frame: dict) -> dict:
    prov = frame_contract.provenance(ep, int(frame["frame"])) or {}
    phase3 = base.phase3_context_hashes(ep, frame["frame"])
    return {
        "frame": frame["frame"],
        "asset_path": frame["path_rel"],
        "asset_sha256": frame["sha256"],
        "frame_contract_sha256": prov.get("contract_sha256"),
        "visual_context": phase3,
    }

def build(ep: Path) -> dict:
    ep = Path(ep).resolve()
    errors = base.verify_episode(ep, metadata_only=False, write_audit=False)
    accepted = acceptance_valid(ep)
    if errors and accepted is None:
        raise ValueError("final visual semantic review not clean: " + "; ".join(errors[:8]))
    frames = base.frame_records(ep, require_files=True)
    data = {
        "schema_version": 1,
        "module_version": "2.6.0",
        "authority": "visual evidence only; captions are deliberately excluded",
        "caption_changes_invalidate_visual_freeze": False,
        "accepted_known_defects": bool(errors and accepted is not None),
        "frames": [_row(ep, row) for row in frames],
        "summary": {"passed": True, "frame_count": len(frames), "accepted_known_defects": bool(errors and accepted is not None)},
    }
    base.write_json(ep / REL, data)
    return data

def verify(ep: Path) -> list[str]:
    ep = Path(ep).resolve()
    p = ep / REL
    if not p.is_file():
        return ["meta/visual-final-freeze.json missing"]
    try:
        saved = json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return [f"visual final freeze unreadable: {exc}"]
    frames = base.frame_records(ep, require_files=True)
    current = [_row(ep, row) for row in frames]
    errors = []
    if saved.get("frames") != current:
        errors.append("visual final freeze drift: image/frame-contract/visual-context changed")
    if (saved.get("summary") or {}).get("passed") is not True:
        errors.append("visual final freeze summary is not PASS")
    return errors

def ensure(ep: Path) -> dict:
    errors = verify(ep)
    if not errors:
        return json.loads((Path(ep).resolve() / REL).read_text(encoding="utf-8-sig"))
    return build(Path(ep).resolve())

def self_test():
    assert REL.as_posix().endswith("visual-final-freeze.json")
    print("VISUAL FINAL FREEZE V2.6.0 SELF-TEST PASS")

def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("build", "ensure", "verify", "show"):
        p = sub.add_parser(name); p.add_argument("episode_dir")
    sub.add_parser("self-test")
    a = ap.parse_args()
    if a.cmd == "self-test": self_test(); return 0
    ep = Path(a.episode_dir).resolve()
    if a.cmd == "build": data = build(ep); print(json.dumps(data.get("summary"), ensure_ascii=False, indent=2)); return 0
    if a.cmd == "ensure": data = ensure(ep); print(json.dumps(data.get("summary"), ensure_ascii=False, indent=2)); return 0
    if a.cmd == "show":
        print((ep / REL).read_text(encoding="utf-8-sig") if (ep / REL).is_file() else "{}")
        return 0
    errors = verify(ep)
    for e in errors: print("FAIL:", e)
    if not errors: print("VISUAL FINAL FREEZE VERIFY PASS")
    return 2 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
