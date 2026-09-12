#!/usr/bin/env python3
"""Story DNA Trace evidence for Story Lock -> Frame Contract -> Final Frame.

This module is deliberately evidence-only.  It never changes episode-state; a
trace is built from the already locked Story/Storyboard and consumed by the
existing PUBLISH_READY gate.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import story_json

REL = Path("meta/story-dna-trace.json")
CONTRACT_ROOT = Path("meta/runtime/contracts/frames")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def _read(path: Path, default=None):
    return story_json.read_json(path, default=default, require_object=False)


def _frame_total(ep: Path) -> int:
    manifest = _read(ep / "meta/release-manifest.json", {}) or {}
    return int(manifest.get("body_frame_count") or 20)


def build(ep: Path, *, story_core: str | None = None, emotional_goal: str | None = None,
          character_relationship: str | None = None, reversal_point: str | None = None,
          required_frames: list[int] | None = None, forbidden_deviation: list[str] | None = None) -> dict:
    """Create the canonical trace; callers provide editorial fields explicitly.

    We refuse to invent editorial intent from a prompt.  The only automatic
    mapping is the already-declared story role from story_semantic_trace.
    """
    import story_semantic_trace
    ep = Path(ep).resolve()
    gates = _read(ep / "meta/story-gates.json", {}) or {}
    story = gates.get("story") if isinstance(gates.get("story"), dict) else {}
    total = _frame_total(ep)
    requested = sorted({int(x) for x in (required_frames or []) if 1 <= int(x) <= total})
    mapping = {}
    for frame in range(1, total + 1):
        role = story_semantic_trace.contract_requirements(ep, frame).get("story_role", "ordinary")
        mapping[f"{frame:02d}"] = {
            "story_goal": role if role != "ordinary" else ("reversal" if frame in requested else None),
            "emotional_goal": emotional_goal,
            "reversal_contribution": "reversal" if frame in requested else None,
            "required": frame in requested or role != "ordinary",
        }
    doc = {
        "schema_version": 1,
        "generated_at": now(),
        "authority": {"episode_state_mutated": False, "source": "Story Lock + story-gates"},
        "story_core": story_core or story.get("story_core") or story.get("logline"),
        "emotional_goal": emotional_goal or story.get("emotional_goal"),
        "character_relationship": character_relationship or story.get("character_relationship"),
        "reversal_point": reversal_point or story.get("reversal_point"),
        "required_frames": requested,
        "forbidden_deviation": list(forbidden_deviation or story.get("forbidden_deviation") or []),
        "frame_mapping": mapping,
    }
    story_json.write_json(ep / REL, doc)
    return doc


def verify(ep: Path) -> list[str]:
    ep = Path(ep).resolve()
    path = ep / REL
    if not path.is_file():
        return ["Historical Evidence Missing: meta/story-dna-trace.json"]
    data = _read(path, {}) or {}
    errors = []
    for field in ("story_core", "emotional_goal", "character_relationship", "reversal_point"):
        if not str(data.get(field) or "").strip():
            errors.append(f"story_dna_{field}_missing")
    mapping = data.get("frame_mapping")
    if not isinstance(mapping, dict):
        return errors + ["story_dna_frame_mapping_missing"]
    total = _frame_total(ep)
    required = set()
    for raw in data.get("required_frames") or []:
        try: required.add(f"{int(raw):02d}")
        except (TypeError, ValueError): errors.append("story_dna_required_frames_invalid")
    covered = set()
    for frame in range(1, total + 1):
        key = f"{frame:02d}"; item = mapping.get(key)
        if not isinstance(item, dict):
            errors.append(f"story_dna_frame_mapping_missing:{key}"); continue
        contract = _read(ep / CONTRACT_ROOT / f"{key}.json", {}) or {}
        contract_mapping = contract.get("story_dna_mapping")
        if not isinstance(contract_mapping, dict):
            errors.append(f"story_dna_contract_mapping_missing:{key}")
        elif contract_mapping.get("story_goal") != item.get("story_goal"):
            errors.append(f"story_dna_contract_mapping_drift:{key}")
        if item.get("required") is True:
            required.add(key)
        if str(item.get("story_goal") or "").strip(): covered.add(key)
    if required and not required.issubset(covered):
        errors.append("story_dna_required_frames_uncovered:" + ",".join(sorted(required - covered)))
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build"); p.add_argument("episode_dir"); p.add_argument("--story-core"); p.add_argument("--emotional-goal"); p.add_argument("--character-relationship"); p.add_argument("--reversal-point"); p.add_argument("--required-frame", action="append", type=int); p.add_argument("--forbidden-deviation", action="append")
    p = sub.add_parser("verify"); p.add_argument("episode_dir")
    a = ap.parse_args(); ep = Path(a.episode_dir)
    if a.cmd == "build":
        print(json.dumps(build(ep, story_core=a.story_core, emotional_goal=a.emotional_goal, character_relationship=a.character_relationship, reversal_point=a.reversal_point, required_frames=a.required_frame, forbidden_deviation=a.forbidden_deviation), ensure_ascii=False, indent=2)); return 0
    errors = verify(ep)
    for error in errors: print("FAIL:", error)
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
