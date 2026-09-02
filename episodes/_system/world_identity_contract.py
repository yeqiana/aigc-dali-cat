#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.2.1 World Identity Contract.

The default profile is Mainland China + ordinary Chinese young adults.
An Episode may explicitly override it with meta/world-identity.json.

This contract is not a Story authority. It is a world/cultural default and
generation/review constraint. Story Lock can override it explicitly.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REL = Path("config/story_os/world_identity.default.json")
OVERRIDE_REL = Path("meta/world-identity.json")
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


def sha256_json(data: Any) -> str:
    raw = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def version_tuple(raw: object) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(raw or "").split("."))
    except Exception:
        return (0,)


def episode_version(ep: Path) -> str:
    ep = Path(ep)
    versions = []
    for rel in (
        "meta/episode-state.json",
        "meta/release-manifest.json",
        "meta/story-gates.json",
    ):
        p = ep / rel
        if not p.is_file():
            continue
        try:
            raw = str(read_json(p).get("tool_version") or "")
            vt = version_tuple(raw)
            if vt != (0,):
                versions.append((vt, raw))
        except Exception:
            continue
    return max(versions, key=lambda x: x[0])[1] if versions else ""


def required(ep: Path) -> bool:
    return version_tuple(episode_version(ep)) >= MIN_VERSION


def deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in override.items():
        if key in {"inherit_default", "status", "note"}:
            continue
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def default_profile() -> dict:
    p = ROOT / DEFAULT_REL
    if not p.is_file():
        raise ValueError(f"world identity default missing: {DEFAULT_REL}")
    data = read_json(p)
    if int(data.get("schema_version") or 0) != 1:
        raise ValueError("world identity default schema_version must be 1")
    return data


def effective(ep: Path) -> dict:
    ep = Path(ep).resolve()
    base = default_profile()
    override_path = ep / OVERRIDE_REL
    override = read_json(override_path) if override_path.is_file() else None

    if override is None:
        merged = copy.deepcopy(base)
        source = "GLOBAL_DEFAULT"
        inherit = True
        override_sha = None
    else:
        inherit = override.get("inherit_default", True) is not False
        if inherit:
            merged = deep_merge(base, override)
        else:
            merged = {
                "schema_version": 1,
                "profile_id": str(
                    override.get("profile_id")
                    or "EPISODE_WORLD_IDENTITY_OVERRIDE"
                ),
                "description": str(
                    override.get("description")
                    or "Episode explicit world identity override"
                ),
                "world": copy.deepcopy(override.get("world") or {}),
                "population": copy.deepcopy(
                    override.get("population") or {}
                ),
                "visual_rules": copy.deepcopy(
                    override.get("visual_rules") or {}
                ),
            }
        source = "EPISODE_OVERRIDE"
        override_sha = sha256_file(override_path)

    effective_data = {
        "schema_version": 1,
        "contract_version": "2.2.1",
        "source": source,
        "inherit_default": inherit,
        "profile_id": merged.get("profile_id"),
        "world": merged.get("world") or {},
        "population": merged.get("population") or {},
        "visual_rules": merged.get("visual_rules") or {},
        "default_config_path": DEFAULT_REL.as_posix(),
        "default_config_sha256": sha256_file(ROOT / DEFAULT_REL),
        "override_path": OVERRIDE_REL.as_posix() if override else None,
        "override_sha256": override_sha,
    }
    effective_data["effective_sha256"] = sha256_json(effective_data)
    return effective_data


def verify(ep: Path) -> list[str]:
    ep = Path(ep).resolve()
    if not required(ep):
        return []
    errors = []
    try:
        data = effective(ep)
    except Exception as exc:
        return [f"WORLD_IDENTITY_CONFIG_INVALID:{exc}"]

    world = data.get("world") or {}
    pop = data.get("population") or {}
    for key in (
        "country",
        "region",
        "culture_context",
        "language_context",
        "architecture_context",
    ):
        if not str(world.get(key) or "").strip():
            errors.append(f"WORLD_IDENTITY_FIELD_MISSING:world.{key}")
    for key in (
        "nationality_context",
        "resident_context",
        "default_protagonist_identity",
    ):
        if not str(pop.get(key) or "").strip():
            errors.append(f"WORLD_IDENTITY_FIELD_MISSING:population.{key}")

    ages = pop.get("default_protagonist_age_range")
    if (
        not isinstance(ages, list)
        or len(ages) != 2
        or not all(isinstance(x, int) for x in ages)
        or ages[0] > ages[1]
    ):
        errors.append(
            "WORLD_IDENTITY_FIELD_INVALID:"
            "population.default_protagonist_age_range"
        )

    override = ep / OVERRIDE_REL
    if override.is_file():
        raw = read_json(override)
        if raw.get("inherit_default") is False:
            if not isinstance(raw.get("world"), dict):
                errors.append(
                    "WORLD_IDENTITY_OVERRIDE_INVALID:"
                    "inherit_default=false requires world"
                )
            if not isinstance(raw.get("population"), dict):
                errors.append(
                    "WORLD_IDENTITY_OVERRIDE_INVALID:"
                    "inherit_default=false requires population"
                )
    return errors


def prompt_block(ep: Path) -> str:
    data = effective(ep)
    world = data["world"]
    pop = data["population"]
    rules = data["visual_rules"]
    return "\n".join(
        [
            f"WORLD_IDENTITY_PROFILE={data.get('profile_id')}",
            f"country={world.get('country')}",
            f"region={world.get('region')}",
            f"culture_context={world.get('culture_context')}",
            f"language_context={world.get('language_context')}",
            f"architecture_context={world.get('architecture_context')}",
            f"population={pop.get('resident_context')}",
            f"default_character={pop.get('default_protagonist_identity')}",
            f"nationality_context={pop.get('nationality_context')}",
            (
                "Do not introduce a foreign population, foreign architecture, "
                "foreign traffic convention or foreign cultural props unless "
                "the Episode world identity explicitly overrides the default."
                if rules.get("do_not_import_foreign_population_by_default")
                else "Follow the explicit Episode world identity."
            ),
            (
                "Do not force ethnicity inside China; preserve natural Chinese "
                "regional/ethnic diversity unless Story explicitly specifies it."
            ),
        ]
    )


def set_override(
    ep: Path,
    *,
    country: str,
    region: str,
    culture_context: str,
    language_context: str,
    architecture_context: str,
    nationality_context: str,
    resident_context: str,
    protagonist_identity: str,
) -> dict:
    ep = Path(ep).resolve()
    data = {
        "schema_version": 1,
        "inherit_default": False,
        "profile_id": "EPISODE_WORLD_IDENTITY_OVERRIDE",
        "world": {
            "country": country,
            "region": region,
            "culture_context": culture_context,
            "language_context": language_context,
            "architecture_context": architecture_context,
            "traffic_context": "story/location appropriate",
            "consumer_goods_context": "story/location appropriate",
        },
        "population": {
            "nationality_context": nationality_context,
            "resident_context": resident_context,
            "default_protagonist_age_range": [19, 30],
            "default_protagonist_identity": protagonist_identity,
            "ethnicity_policy": "story_defined",
            "foreign_character_policy": "story_defined",
        },
        "visual_rules": {
            "visible_text_context": language_context,
            "do_not_import_foreign_architecture_by_default": False,
            "do_not_import_foreign_population_by_default": False,
            "do_not_import_foreign_cultural_props_by_default": False,
            "preserve_location_specific_chinese_regional_detail": False,
        },
        "note": (
            "Explicit Episode override. This replaces the default Mainland "
            "China profile for this Episode."
        ),
    }
    write_json(ep / OVERRIDE_REL, data)
    return data


def self_test() -> None:
    base = {
        "a": 1,
        "nested": {"x": 1, "y": 2},
    }
    merged = deep_merge(base, {"nested": {"y": 3}})
    assert merged["nested"] == {"x": 1, "y": 3}
    cfg = default_profile()
    assert cfg["world"]["country"] == "China"
    assert cfg["population"]["nationality_context"] == "Chinese"
    print("WORLD IDENTITY CONTRACT V2.2.1 SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("show")
    p.add_argument("episode_dir")

    p = sub.add_parser("verify")
    p.add_argument("episode_dir")

    p = sub.add_parser("set-override")
    p.add_argument("episode_dir")
    p.add_argument("--country", required=True)
    p.add_argument("--region", required=True)
    p.add_argument("--culture-context", required=True)
    p.add_argument("--language-context", required=True)
    p.add_argument("--architecture-context", required=True)
    p.add_argument("--nationality-context", required=True)
    p.add_argument("--resident-context", required=True)
    p.add_argument("--protagonist-identity", required=True)

    sub.add_parser("self-test")
    args = ap.parse_args()

    if args.cmd == "self-test":
        self_test()
        return 0

    ep = Path(args.episode_dir).resolve()
    if args.cmd == "show":
        print(json.dumps(effective(ep), ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "set-override":
        out = set_override(
            ep,
            country=args.country,
            region=args.region,
            culture_context=args.culture_context,
            language_context=args.language_context,
            architecture_context=args.architecture_context,
            nationality_context=args.nationality_context,
            resident_context=args.resident_context,
            protagonist_identity=args.protagonist_identity,
        )
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    errors = verify(ep)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 2
    print("WORLD IDENTITY CONTRACT VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
