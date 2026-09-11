#!/usr/bin/env python3
"""Story OS Visual Profile Registry (Visual Profile Governance Phase 2.1).

Why this module exists
----------------------
The Visual Profile audit in docs/Story_OS_Visual_Profile_Governance_V1.0.md (gap G8)
found that visual_profile_resolver.resolve_profile() silently replaced an
unregistered profile id with the default M00 profile and kept producing. A
runtime-request could therefore declare visual_profile=M00_ANCIENT_DAILY_LIFE_V1
while standards/visual_profiles/ held no such file, and nothing failed.

This module makes the registry the single source of truth for which Visual
Profile ids exist:

  standards/visual_profiles/index.json                  registry (id / path / status)
  standards/visual_profiles/schema/profile.schema.json  profile document contract

Boundaries
----------
  - Advisory only: it never touches Runtime, the machine gate, episode-state.json
    or story-gates.json, and it never rewrites a profile file.
  - It answers one question: "does this profile id exist, is it active, and is
    the document legal?"
  - An id that is not registered fails closed (VISUAL_PROFILE_NOT_REGISTERED).
    The default profile is used only when the caller did not ask for a profile,
    or when the caller explicitly opts in with allow_fallback=True.
  - Configured presence is not evidence. A registered id whose file is missing
    also fails (VISUAL_PROFILE_FILE_MISSING) instead of degrading to the default.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import story_json

ROOT = Path(__file__).resolve().parents[2]

REGISTRY_REL = Path("standards/visual_profiles/index.json")
SCHEMA_REL = Path("standards/visual_profiles/schema/profile.schema.json")
PROFILE_DIR_REL = Path("standards/visual_profiles")

ACTIVE_STATUS = "active"
VALID_STATUSES = ("active", "deprecated", "retired")

# Sibling content-asset repository, kept as a legacy probe only. The registry is
# the authority for existence; this path can never introduce a new profile id.
LEGACY_ASSET_ROOT_NAME = "aigc-dali-cat"

ERROR_NOT_REGISTERED = "VISUAL_PROFILE_NOT_REGISTERED"
ERROR_NOT_ACTIVE = "VISUAL_PROFILE_NOT_ACTIVE"
ERROR_REGISTRY_MISSING = "VISUAL_PROFILE_REGISTRY_MISSING"
ERROR_REGISTRY_INVALID = "VISUAL_PROFILE_REGISTRY_INVALID"
ERROR_FILE_MISSING = "VISUAL_PROFILE_FILE_MISSING"
ERROR_FILE_INVALID = "VISUAL_PROFILE_FILE_INVALID"
ERROR_SCHEMA_MISSING = "VISUAL_PROFILE_SCHEMA_MISSING"
ERROR_SCHEMA_INVALID = "VISUAL_PROFILE_SCHEMA_INVALID"


class VisualProfileError(SystemExit):
    """Fail-fast base error. SystemExit keeps CLI output clean (repo convention)."""

    code = "VISUAL_PROFILE_ERROR"

    def __init__(self, detail: str, code: str | None = None) -> None:
        if code:
            self.code = code
        super().__init__(f"{self.code}: {detail}")


class VisualProfileNotRegistered(VisualProfileError):
    code = ERROR_NOT_REGISTERED


class VisualProfileNotActive(VisualProfileError):
    code = ERROR_NOT_ACTIVE


class VisualProfileRegistryMissing(VisualProfileError):
    code = ERROR_REGISTRY_MISSING


class VisualProfileRegistryInvalid(VisualProfileError):
    code = ERROR_REGISTRY_INVALID


class VisualProfileFileMissing(VisualProfileError):
    code = ERROR_FILE_MISSING


class VisualProfileFileInvalid(VisualProfileError):
    code = ERROR_FILE_INVALID


class VisualProfileSchemaMissing(VisualProfileError):
    code = ERROR_SCHEMA_MISSING


class VisualProfileSchemaInvalid(VisualProfileError):
    code = ERROR_SCHEMA_INVALID


# --------------------------------------------------------------------------- #
# registry
# --------------------------------------------------------------------------- #

def _story_root(story_root: Path | str | None) -> Path:
    return Path(story_root) if story_root else ROOT


def _read_json(path: Path, *, missing: type[VisualProfileError], invalid: type[VisualProfileError]) -> Any:
    """Read one JSON document through the canonical story_json reader."""
    try:
        return story_json.read_json(path)
    except FileNotFoundError as exc:
        raise missing(f"not found: {path}") from exc
    except (json.JSONDecodeError, OSError, UnicodeDecodeError, ValueError) as exc:
        raise invalid(f"{path.name}: {exc}") from exc


def registry_errors(data: Any) -> list[str]:
    """Structural checks on a registry document. Returns error strings."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["registry root must be a JSON object"]

    default = data.get("default_profile")
    if not isinstance(default, str) or not default.strip():
        errors.append("default_profile must be a non-empty string")

    profiles = data.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        errors.append("profiles must be a non-empty array")
        return errors

    seen: set[str] = set()
    for index, entry in enumerate(profiles):
        where = f"profiles[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{where}: must be an object")
            continue
        pid = entry.get("id")
        rel = entry.get("path")
        status = entry.get("status")
        if not isinstance(pid, str) or not pid.strip():
            errors.append(f"{where}: id must be a non-empty string")
        elif pid in seen:
            errors.append(f"{where}: duplicate id {pid!r}")
        else:
            seen.add(pid)
        if not isinstance(rel, str) or not rel.strip():
            errors.append(f"{where}: path must be a non-empty string")
        if not isinstance(status, str) or status.strip() not in VALID_STATUSES:
            errors.append(f"{where}: status must be one of {', '.join(VALID_STATUSES)}")

    aliases = data.get("aliases")
    if aliases is not None:
        if not isinstance(aliases, list):
            errors.append("aliases must be an array when present")
        else:
            alias_seen: set[str] = set()
            for index, entry in enumerate(aliases):
                where = f"aliases[{index}]"
                if not isinstance(entry, dict):
                    errors.append(f"{where}: must be an object")
                    continue
                old_id = entry.get("old_id")
                status = entry.get("status")
                replacement = entry.get("replacement")
                if not isinstance(old_id, str) or not old_id.strip():
                    errors.append(f"{where}: old_id must be a non-empty string")
                elif old_id in alias_seen:
                    errors.append(f"{where}: duplicate old_id {old_id!r}")
                else:
                    alias_seen.add(old_id)
                    if old_id in seen:
                        errors.append(f"{where}: old_id {old_id!r} is already a registered profile id")
                if not isinstance(status, str) or status.strip() not in VALID_STATUSES:
                    errors.append(f"{where}: status must be one of {', '.join(VALID_STATUSES)}")
                if not isinstance(replacement, str) or not replacement.strip():
                    errors.append(f"{where}: replacement must be a non-empty string")
                elif replacement.strip() not in seen:
                    errors.append(f"{where}: replacement {replacement!r} is not a registered profile id")

    if isinstance(default, str) and default.strip() and default.strip() not in seen:
        errors.append(f"default_profile {default!r} is not registered")
    return errors


def load_registry(story_root: Path | str | None = None) -> dict[str, Any]:
    path = _story_root(story_root) / REGISTRY_REL
    data = _read_json(path, missing=VisualProfileRegistryMissing, invalid=VisualProfileRegistryInvalid)
    errors = registry_errors(data)
    if errors:
        raise VisualProfileRegistryInvalid(
            f"{REGISTRY_REL.as_posix()}: " + "; ".join(errors)
        )
    return data


def registry_entries(story_root: Path | str | None = None) -> list[dict[str, Any]]:
    return [dict(entry) for entry in load_registry(story_root)["profiles"]]


def registry_ids(story_root: Path | str | None = None) -> list[str]:
    return [str(entry["id"]).strip() for entry in registry_entries(story_root)]


def registry_entry(profile_id: str | None, story_root: Path | str | None = None) -> dict[str, Any] | None:
    wanted = _normalize_id(profile_id)
    if not wanted:
        return None
    for entry in registry_entries(story_root):
        if str(entry["id"]).strip() == wanted:
            return entry
    return None


def default_profile_id(story_root: Path | str | None = None) -> str:
    registry = load_registry(story_root)
    default = str(registry["default_profile"]).strip()
    if registry_entry(default, story_root) is None:
        raise VisualProfileRegistryInvalid(f"default_profile {default!r} is not registered")
    return default


def registry_aliases(story_root: Path | str | None = None) -> list[dict[str, Any]]:
    """The alias table (Visual Profile Governance Phase 2.2). Read-only metadata.

    Aliases record historical or planned profile ids. They are never registered
    profiles; a deprecated alias such as M00_ANCIENT_DAILY_LIFE_V1 stays
    unresolvable so an unregistered id still fails closed.
    """
    return [dict(entry) for entry in load_registry(story_root).get("aliases") or []]


def alias_entry(old_id: str | None, story_root: Path | str | None = None) -> dict[str, Any] | None:
    wanted = _normalize_id(old_id)
    if not wanted:
        return None
    for entry in registry_aliases(story_root):
        if str(entry.get("old_id", "")).strip() == wanted:
            return entry
    return None


def alias_replacement(
    old_id: str | None,
    *,
    story_root: Path | str | None = None,
    follow_deprecated: bool = False,
) -> str | None:
    """Map an alias to its registered replacement id.

    Deprecated aliases are not followed unless the caller opts in, so declaring
    an alias never changes how a historical id resolves by default.
    """
    entry = alias_entry(old_id, story_root)
    if entry is None:
        return None
    if not follow_deprecated and str(entry.get("status", "")).strip() == "deprecated":
        return None
    replacement = str(entry.get("replacement", "")).strip()
    return replacement or None


def _normalize_id(profile_id: str | None) -> str:
    return str(profile_id or "").strip()


def _assert_inside(path: Path, root: Path) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        raise VisualProfileFileInvalid(f"profile path escapes the repository root: {path}")


def _rel_label(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def declared_profile_id(data: dict[str, Any]) -> str:
    return str(data.get("id") or data.get("profile_id") or "").strip()


# --------------------------------------------------------------------------- #
# profile document + schema
# --------------------------------------------------------------------------- #

def load_profile_document(profile_id: str, story_root: Path | str | None = None) -> dict[str, Any]:
    """Load the registered profile document for an active profile id."""
    root = _story_root(story_root)
    entry = _active_entry(profile_id, root)
    if entry is None:
        registry = load_registry(root)
        raise VisualProfileNotRegistered(_not_registered_message(registry, _normalize_id(profile_id), root))
    path = (root / str(entry["path"])).resolve()
    _assert_inside(path, root)
    return _read_json(path, missing=VisualProfileFileMissing, invalid=VisualProfileFileInvalid)


def load_schema(story_root: Path | str | None = None) -> dict[str, Any]:
    path = _story_root(story_root) / SCHEMA_REL
    schema = _read_json(path, missing=VisualProfileSchemaMissing, invalid=VisualProfileSchemaInvalid)
    if not isinstance(schema, dict):
        raise VisualProfileSchemaInvalid("schema root must be a JSON object")
    return schema


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def validate_json(value: Any, schema: Any, path: str = "$") -> list[str]:
    """Validate against the JSON Schema subset used by the profile contract.

    Supported keywords: type, required, properties, items, enum, const,
    minLength, minimum, pattern, allOf, anyOf, oneOf, not, if/then/else.
    A dependency-free subset is deliberate: no schema library is added to the
    Runtime just for one governance contract.
    """
    if not isinstance(schema, dict):
        return []

    errors: list[str] = []

    if "type" in schema:
        expected = schema["type"]
        allowed = expected if isinstance(expected, list) else [expected]
        if not any(_type_ok(value, item) for item in allowed):
            return [f"{path}: expected type {'|'.join(allowed)}, got {type(value).__name__}"]

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} is not one of {schema['enum']!r}")
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: value {value!r} != const {schema['const']!r}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{path}: does not match pattern {schema['pattern']!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} is below minimum {schema['minimum']}")

    if isinstance(value, dict):
        for key in schema.get("required") or []:
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")
        for key, subschema in (schema.get("properties") or {}).items():
            if key in value:
                errors.extend(validate_json(value[key], subschema, f"{path}.{key}"))

    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            errors.extend(validate_json(item, schema["items"], f"{path}[{index}]"))

    for subschema in schema.get("allOf") or []:
        errors.extend(validate_json(value, subschema, path))

    for keyword in ("anyOf", "oneOf"):
        if keyword in schema:
            branches = schema[keyword] or []
            passing = sum(1 for branch in branches if not validate_json(value, branch, path))
            if keyword == "anyOf" and passing == 0:
                errors.append(f"{path}: does not match any of {len(branches)} subschemas")
            if keyword == "oneOf" and passing != 1:
                errors.append(f"{path}: matched {passing} subschemas, expected exactly 1")

    if "not" in schema:
        if not validate_json(value, schema["not"], path):
            errors.append(f"{path}: matched a 'not' subschema")

    if "if" in schema:
        condition_failed = bool(validate_json(value, schema["if"], path))
        branch = "else" if condition_failed else "then"
        if branch in schema:
            errors.extend(validate_json(value, schema[branch], path))

    return errors


def validate_profile_document(data: Any, story_root: Path | str | None = None) -> list[str]:
    """Return schema errors for a profile document ([] means legal)."""
    return validate_json(data, load_schema(story_root))


def validate_registered_profile(profile_id: str, story_root: Path | str | None = None) -> list[str]:
    return validate_profile_document(load_profile_document(profile_id, story_root), story_root)


# --------------------------------------------------------------------------- #
# resolution
# --------------------------------------------------------------------------- #

def _entry_for(registry: dict[str, Any], profile_id: str) -> dict[str, Any] | None:
    for entry in registry["profiles"]:
        if str(entry["id"]).strip() == profile_id:
            return entry
    return None


def _active_entry(profile_id: str | None, story_root: Path | str | None) -> dict[str, Any] | None:
    registry = load_registry(story_root)
    wanted = _normalize_id(profile_id)
    entry = _entry_for(registry, wanted)
    if entry is not None and str(entry.get("status")).strip() != ACTIVE_STATUS:
        raise VisualProfileNotActive(
            f"profile_id={wanted!r} status={entry.get('status')!r}"
        )
    return entry


def _candidate_paths(profile_id: str, entry: dict[str, Any], root: Path, episode: Path | None) -> list[Path]:
    candidates: list[Path] = []
    if episode:
        candidates.append(Path(episode) / "assets" / "visual_profiles" / f"{profile_id}.json")
    candidates.append(root / str(entry["path"]))
    candidates.append(root / PROFILE_DIR_REL / f"{profile_id}.json")
    candidates.append(root.parent / LEGACY_ASSET_ROOT_NAME / PROFILE_DIR_REL / f"{profile_id}.json")
    return candidates


def _not_registered_message(registry: dict[str, Any], requested: str, root: Path) -> str:
    registered = ", ".join(str(entry["id"]) for entry in registry["profiles"])
    return (
        f"profile_id={requested!r} is not registered in {REGISTRY_REL.as_posix()} "
        f"(registered: {registered}). "
        "Register the Visual Profile before production, or pass allow_fallback=True "
        "to accept the declared default explicitly. Silent substitution is not allowed."
    )


def resolve_registered_profile(
    profile_id: str | None,
    *,
    story_root: Path | str | None = None,
    episode: Path | None = None,
    allow_fallback: bool = False,
) -> dict[str, Any]:
    """Resolve a Visual Profile through the registry, failing closed.

    - empty profile_id        -> the registry default_profile (unspecified, not a fallback)
    - registered + active     -> the profile document
    - registered + inactive   -> FAIL (VISUAL_PROFILE_NOT_ACTIVE)
    - unregistered            -> FAIL (VISUAL_PROFILE_NOT_REGISTERED)
    - unregistered + allow_fallback=True -> registry default with fallback=True
    """
    root = _story_root(story_root)
    registry = load_registry(root)

    requested = _normalize_id(profile_id)
    explicit = bool(requested)
    if not explicit:
        requested = str(registry["default_profile"]).strip()

    entry = _entry_for(registry, requested)
    if entry is None or str(entry.get("status")).strip() != ACTIVE_STATUS:
        if explicit and allow_fallback:
            return _fallback_result(registry, requested, root, episode)
        if entry is None:
            raise VisualProfileNotRegistered(_not_registered_message(registry, requested, root))
        raise VisualProfileNotActive(f"profile_id={requested!r} status={entry.get('status')!r}")

    for path in _candidate_paths(requested, entry, root, episode):
        if not path.is_file():
            continue
        data = _read_json(path, missing=VisualProfileFileMissing, invalid=VisualProfileFileInvalid)
        declared = declared_profile_id(data)
        if declared and declared != requested:
            raise VisualProfileFileInvalid(
                f"{_rel_label(path, root)}: declares profile_id={declared!r}, expected {requested!r}"
            )
        return {
            "profile_id": requested,
            "source": str(path),
            "profile_path": _rel_label(path, root),
            "profile": data,
            "status": str(entry.get("status")).strip(),
            "registered": True,
            "fallback": False,
            "resolution": "registry_default" if not explicit else "registry",
            "requested_profile_id": requested,
        }

    raise VisualProfileFileMissing(
        f"{entry['path']} missing for registered profile_id={requested!r}"
    )


def _fallback_result(
    registry: dict[str, Any], requested: str, root: Path, episode: Path | None
) -> dict[str, Any]:
    default_id = str(registry["default_profile"]).strip()
    resolved = resolve_registered_profile(default_id, story_root=root, episode=episode)
    resolved.update(
        {
            "fallback": True,
            "resolution": "fallback_default",
            "requested_profile_id": requested,
            "fallback_default_id": default_id,
        }
    )
    return resolved


# --------------------------------------------------------------------------- #
# CLI (read-only)
# --------------------------------------------------------------------------- #

def cmd_list(args: argparse.Namespace) -> int:
    entries = registry_entries(args.root)
    if args.json:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
    else:
        for entry in entries:
            print(f"{entry['id']} | {entry['status']} | {entry['path']}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    entries = registry_entries(getattr(args, "root", None))
    failed = False
    for entry in entries:
        pid = str(entry["id"])
        errors = validate_registered_profile(pid, getattr(args, "root", None))
        if errors:
            failed = True
            print(f"FAIL {pid}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {pid}")
    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Story OS Visual Profile registry (governance Phase 2.1)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, func in (("list", cmd_list), ("validate", cmd_validate)):
        child = sub.add_parser(name)
        child.set_defaults(func=func)
        child.add_argument("--root", default=None, help="repository root (defaults to this checkout)")
        child.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
