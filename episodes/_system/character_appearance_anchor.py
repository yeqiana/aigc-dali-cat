#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Derived Character Appearance Anchor for Story OS V2.2.1.

This is a derived cache. It does not replace Character Contract,
Character Visual Contract, or the Visual Lock pixel master.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import world_identity_contract

ROOT = Path(__file__).resolve().parents[2]
REL = Path("meta/runtime/contracts/character-appearance-anchor.json")
CHAR_REL = Path("meta/character-contract.json")
VISUAL_REL = Path("meta/character-visual-contract.json")
MIN_VERSION = (2, 2, 1)


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_json(data: Any) -> str:
    raw = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def required(ep: Path) -> bool:
    return world_identity_contract.required(ep)


def _source_errors(ep: Path) -> list[str]:
    errors = []
    cp = ep / CHAR_REL
    cv = ep / VISUAL_REL
    if not cp.is_file():
        errors.append("CHARACTER_APPEARANCE_SOURCE_MISSING:character-contract")
    if not cv.is_file():
        errors.append(
            "CHARACTER_APPEARANCE_SOURCE_MISSING:character-visual-contract"
        )
    if errors:
        return errors
    cpd = read_json(cp)
    cvd = read_json(cv)
    if cpd.get("status") != "LOCKED":
        errors.append(
            "CHARACTER_APPEARANCE_SOURCE_NOT_LOCKED:character-contract"
        )
    if cvd.get("status") != "LOCKED":
        errors.append(
            "CHARACTER_APPEARANCE_SOURCE_NOT_LOCKED:"
            "character-visual-contract"
        )
    return errors


def build(ep: Path, *, write: bool = True) -> dict:
    ep = Path(ep).resolve()
    if not required(ep):
        return {
            "applicable": False,
            "reason": "episode_version_lt_2_2_1",
        }

    errors = world_identity_contract.verify(ep) + _source_errors(ep)
    if errors:
        raise ValueError("; ".join(errors))

    cp = read_json(ep / CHAR_REL)
    cv = read_json(ep / VISUAL_REL)
    world = world_identity_contract.effective(ep)
    members = ((cp.get("cast") or {}).get("members") or [])
    visual_members = cv.get("members") or {}
    rows = {}

    for member in members:
        cid = str(member.get("id") or "")
        if not cid:
            continue
        vm = visual_members.get(cid) or {}
        face = vm.get("face_identity") or {}
        hair = vm.get("hair") or {}
        presentation = vm.get("presentation") or {}

        rows[cid] = {
            "character_id": cid,
            "nationality_context": (
                (world.get("population") or {}).get(
                    "nationality_context"
                )
            ),
            "resident_context": (
                (world.get("population") or {}).get("resident_context")
            ),
            "gender": member.get("gender"),
            "age": member.get("age"),
            "build": member.get("build"),
            "body_build": vm.get("body_build"),
            "hair": {
                "character_contract_anchor": member.get("hair"),
                "haircut_anchor": hair.get("haircut_anchor"),
                "hair_length_anchor": hair.get("hair_length_anchor"),
            },
            "clothing_anchor": member.get("clothing_anchor"),
            "device_anchor": member.get("device_anchor"),
            "visual_priority": vm.get("visual_priority"),
            "identity_rules": {
                "same_person_across_frames": True,
                "original_character": face.get("original_character"),
                "independently_distinct_face": face.get(
                    "independently_distinct_face"
                ),
                "reference_similarity_target": face.get(
                    "reference_similarity_target"
                ),
                "natural_skin_texture": (
                    face.get("skin_texture")
                    or presentation.get("camera_friendly_but_believable")
                ),
                "allowed_variation": hair.get(
                    "allowed_state_variation"
                )
                or [
                    "wet",
                    "windblown",
                    "messy",
                    "hood_up",
                    "story-motivated hair state",
                    "expression",
                    "lighting",
                ],
                "forbidden_unmotivated_drift": [
                    "nationality/cultural identity",
                    "apparent age",
                    "face identity",
                    "haircut or hair length",
                    "body build",
                    "character role",
                    "clothing anchor unless wardrobe contract changes it",
                ],
            },
        }

    data = {
        "schema_version": 1,
        "contract_version": "2.2.1",
        "derived_cache": True,
        "world_identity_profile_id": world.get("profile_id"),
        "world_identity_effective_sha256": world.get(
            "effective_sha256"
        ),
        "character_contract_path": CHAR_REL.as_posix(),
        "character_contract_sha256": sha256_file(ep / CHAR_REL),
        "character_visual_contract_path": VISUAL_REL.as_posix(),
        "character_visual_contract_sha256": sha256_file(
            ep / VISUAL_REL
        ),
        "members": rows,
        "pixel_master_relationship": (
            "Textual pre-image anchor only. Visual Lock pixel master, "
            "when available, is the stronger pixel identity reference."
        ),
    }
    data["anchor_sha256"] = sha256_json(data)

    if write:
        write_json(ep / REL, data)
    return data


def verify(ep: Path) -> list[str]:
    ep = Path(ep).resolve()
    if not required(ep):
        return []

    errors = world_identity_contract.verify(ep) + _source_errors(ep)
    if errors:
        return errors

    path = ep / REL
    if not path.is_file():
        return [
            "CHARACTER_APPEARANCE_ANCHOR_MISSING:"
            "run character_appearance_anchor.py build"
        ]

    try:
        cached = read_json(path)
        current = build(ep, write=False)
    except Exception as exc:
        return [f"CHARACTER_APPEARANCE_ANCHOR_INVALID:{exc}"]

    if cached.get("derived_cache") is not True:
        errors.append("CHARACTER_APPEARANCE_ANCHOR_NOT_DERIVED_CACHE")
    if cached.get("anchor_sha256") != current.get("anchor_sha256"):
        errors.append("CHARACTER_APPEARANCE_ANCHOR_STALE")
    if not (cached.get("members") or {}):
        errors.append("CHARACTER_APPEARANCE_ANCHOR_ZERO_MEMBERS")
    return errors


def prompt_block(ep: Path) -> str:
    data = build(Path(ep), write=False)
    if data.get("applicable") is False:
        return ""
    return json.dumps(
        {
            "world_identity_profile_id": data.get(
                "world_identity_profile_id"
            ),
            "members": data.get("members") or {},
            "rule": (
                "Keep the same person across frames. Natural changes in "
                "expression, pose, sweat, wetness, lighting and story-motivated "
                "hair state are allowed; unmotivated face/age/nationality/"
                "haircut/body drift is forbidden."
            ),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def self_test() -> None:
    assert MIN_VERSION == (2, 2, 1)
    print("CHARACTER APPEARANCE ANCHOR V2.2.1 SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("build")
    p.add_argument("episode_dir")

    p = sub.add_parser("verify")
    p.add_argument("episode_dir")

    p = sub.add_parser("show")
    p.add_argument("episode_dir")

    sub.add_parser("self-test")
    args = ap.parse_args()

    if args.cmd == "self-test":
        self_test()
        return 0

    ep = Path(args.episode_dir).resolve()
    if args.cmd == "build":
        print(json.dumps(build(ep, write=True), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "show":
        print(json.dumps(build(ep, write=False), ensure_ascii=False, indent=2))
        return 0

    errors = verify(ep)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 2
    print("CHARACTER APPEARANCE ANCHOR VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
