#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS Visual Profile Selection Evidence Gate (governance Phase 3.5).

Why this module exists
----------------------
Phase 3.3 gave Story OS a rule engine that picks a Visual Profile and emits
selection evidence; Phase 3.4 fixed the record shape a Visual Lock has to carry.
Nothing verified those records, so "the lock file exists" could still be mistaken
for "a profile was chosen, on purpose, by someone, at some time".

This module owns that verification and nothing else. It never re-runs the
Selector, never re-picks a profile, never repairs a lock and never writes to an
Episode. It is an evidence contract, not a policy.

    Selector -> Selection Evidence -> Visual Lock -> [validate] -> Gate

Checks, in evaluation order (the first failure decides result["code"])
----------------------------------------------------------------------
    1. profile_id is registered and active        VISUAL_PROFILE_NOT_REGISTERED / _NOT_ACTIVE
    2. profile_path matches the registry entry     VISUAL_PROFILE_PATH_MISMATCH
       and the file it points at exists            VISUAL_PROFILE_FILE_MISSING
    3. selection_evidence carries the selection    VISUAL_PROFILE_SELECTION_EVIDENCE_MISSING
       fact (selector_version, inputs_digest,
       matched_rules, reason, source)
    4. the selection was adjudicated               VISUAL_PROFILE_NOT_CONFIRMED
       (not needs_confirmation / rejected)
    5. the adjudication is recorded                VISUAL_PROFILE_CONFIRMATION_MISSING
       (human review needs confirmed_by + confirmed_at)
    shape violations that are none of the above    VISUAL_PROFILE_LOCK_INVALID

Historical compatibility
------------------------
    - Episode with no Visual Lock                     -> legacy_unmanaged (not FAIL)
    - pre-governance V2.2.4 meta/visual-profile.json  -> legacy_unmanaged (not FAIL)
      (profile_id/profile_path plus tool_version/mode and no governance field)
    - Episode that opted in (a governed lock, or a runtime-request carrying
      visual_profile_selection) but has no lock       -> VISUAL_PROFILE_LOCK_MISSING

The module is standalone in Phase 3.5: machine_gate does not call it yet, so no
production flow changes behaviour because of it.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import story_json
import visual_profile_registry as registry

ROOT = Path(__file__).resolve().parents[2]

LOCK_REL = Path("meta/visual-profile.json")
LOCK_ALT_REL = Path("meta/visual_profile.json")
RUNTIME_REQUEST_REL = Path("meta/runtime-request.json")
LOCK_SCHEMA_REL = Path("standards/visual_profiles/schema/visual-lock.schema.json")

# A pre-governance V2.2.4 episode meta lock carries profile_id / profile_path plus
# tool_version / lock_status / mode. It never carries any of these fields, so one
# of them present is the opt-in signal that the document claims the Phase 3.5
# Visual Lock contract and must therefore be judged rather than waved through.
GOVERNANCE_FIELDS = (
    "selection",
    "status",
    "selection_evidence",
    "confirmation_mode",
    "confirmed_by",
    "confirmed_at",
)

SELECTION_STATUSES = ("selected", "needs_confirmation", "defaulted", "rejected")
BLOCKED_STATUSES = ("needs_confirmation", "rejected")
HUMAN_CONFIRMATION_MODES = ("human", "direct_user", "delegated_auto")
CONFIRMATION_MODES = HUMAN_CONFIRMATION_MODES + ("system",)

EVIDENCE_REQUIRED_FIELDS = (
    "selector_version",
    "inputs_digest",
    "matched_rules",
    "reason",
    "source",
)

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")

STATUS_PASS = "pass"
STATUS_FAIL = "fail"
STATUS_LEGACY = "legacy_unmanaged"

ERROR_NOT_REGISTERED = "VISUAL_PROFILE_NOT_REGISTERED"
ERROR_NOT_ACTIVE = "VISUAL_PROFILE_NOT_ACTIVE"
ERROR_PATH_MISMATCH = "VISUAL_PROFILE_PATH_MISMATCH"
ERROR_FILE_MISSING = "VISUAL_PROFILE_FILE_MISSING"
ERROR_EVIDENCE_MISSING = "VISUAL_PROFILE_SELECTION_EVIDENCE_MISSING"
ERROR_NOT_CONFIRMED = "VISUAL_PROFILE_NOT_CONFIRMED"
ERROR_CONFIRMATION_MISSING = "VISUAL_PROFILE_CONFIRMATION_MISSING"
ERROR_LOCK_MISSING = "VISUAL_PROFILE_LOCK_MISSING"
ERROR_LOCK_INVALID = "VISUAL_PROFILE_LOCK_INVALID"
ERROR_LOCK_UNREADABLE = "VISUAL_PROFILE_LOCK_UNREADABLE"

ERROR_CODES = (
    ERROR_NOT_REGISTERED,
    ERROR_NOT_ACTIVE,
    ERROR_PATH_MISMATCH,
    ERROR_FILE_MISSING,
    ERROR_EVIDENCE_MISSING,
    ERROR_NOT_CONFIRMED,
    ERROR_CONFIRMATION_MISSING,
    ERROR_LOCK_MISSING,
    ERROR_LOCK_INVALID,
    ERROR_LOCK_UNREADABLE,
)


def _root(story_root: Path | str | None = None) -> Path:
    return Path(story_root) if story_root else ROOT


def read_json(path, default=None):
    # Lenient read: a lock or request that cannot be parsed is reported through an
    # explicit error code by the caller, never silently treated as absent evidence.
    return story_json.read_json(path, default=default, require_object=False)


def normalize_rel(value) -> str:
    text = str(value or "").strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text.strip("/")


def repo_rel(path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(Path(ROOT).resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def load_lock_schema(story_root: Path | str | None = None) -> dict[str, Any]:
    data = read_json(_root(story_root) / LOCK_SCHEMA_REL, default=None)
    return data if isinstance(data, dict) else {}


def lock_path(episode) -> Path | None:
    ep = Path(episode)
    for rel in (LOCK_REL, LOCK_ALT_REL):
        candidate = ep / rel
        if candidate.is_file():
            return candidate
    return None


def load_lock(episode) -> tuple[dict | None, str | None, str | None]:
    """Return (lock, source, error). lock is None when the Episode has no lock."""
    path = lock_path(episode)
    if path is None:
        return None, None, None
    source = repo_rel(path)
    data = read_json(path, default=None)
    if not isinstance(data, dict):
        return None, source, f"lock document is unreadable or not a JSON object: {source}"
    return data, source, None


def lock_is_governed(lock) -> bool:
    """True when the document claims the Phase 3.5 Visual Lock contract."""
    if not isinstance(lock, dict):
        return False
    return any(field in lock for field in GOVERNANCE_FIELDS)


def lock_status(lock) -> str | None:
    """Resolve the adjudicated selector status from status / selection."""
    if not isinstance(lock, dict):
        return None
    raw = lock.get("status")
    if not isinstance(raw, str) or not raw.strip():
        selection = lock.get("selection")
        if isinstance(selection, str):
            raw = selection
        elif isinstance(selection, dict):
            raw = selection.get("status") or selection.get("selection")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def confirmation_mode(lock) -> str:
    """Resolved confirmation mode. An undeclared mode counts as human review."""
    mode = lock.get("confirmation_mode") if isinstance(lock, dict) else None
    if isinstance(mode, str) and mode.strip():
        return mode.strip()
    return "human"


def visual_profile_requirement(episode) -> dict[str, Any]:
    """Does this Episode declare that it needs a governed Visual Lock?"""
    ep = Path(episode)
    request = read_json(ep / RUNTIME_REQUEST_REL, default={}) or {}
    if not isinstance(request, dict):
        request = {}
    if isinstance(request.get("visual_profile_selection"), dict):
        return {"required": True, "reason": "runtime-request.visual_profile_selection"}
    if isinstance(request.get("visual_profile_lock"), dict):
        return {"required": True, "reason": "runtime-request.visual_profile_lock"}
    if request.get("visual_profile_lock_required") is True:
        return {"required": True, "reason": "runtime-request.visual_profile_lock_required"}
    lock, source, _ = load_lock(ep)
    if lock is not None and lock_is_governed(lock):
        return {"required": True, "reason": f"governed lock present: {source}"}
    return {"required": False, "reason": "no governance opt-in declared"}


# --------------------------------------------------------------------------- #
# result assembly
# --------------------------------------------------------------------------- #

def _blank_result() -> dict[str, Any]:
    return {
        "status": STATUS_LEGACY,
        "code": None,
        "required": False,
        "requirement_reason": None,
        "governed": False,
        "judged": False,
        "source": None,
        "profile_id": None,
        "profile_path": None,
        "checks": [],
        "errors": [],
    }


def _record(result: dict, check: str, status: str, detail: str, code: str | None = None) -> None:
    result["checks"].append({"name": check, "status": status, "code": code, "detail": detail})
    if status == "fail":
        result["errors"].append({"code": code, "detail": detail})


def _pass(result: dict, check: str, detail: str = "ok") -> None:
    _record(result, check, "pass", detail)


def _fail(result: dict, check: str, code: str, detail: str) -> None:
    _record(result, check, "fail", detail, code)


def _skip(result: dict, check: str, detail: str) -> None:
    _record(result, check, "skip", detail)


def _finish(result: dict) -> dict[str, Any]:
    if result["errors"]:
        result["status"] = STATUS_FAIL
        result["code"] = result["errors"][0]["code"]
    elif result.get("judged"):
        result["status"] = STATUS_PASS
        result["code"] = None
    else:
        # Nothing was verified: no lock, or a pre-governance lock. That is
        # legacy_unmanaged, deliberately not PASS and not FAIL.
        result["status"] = STATUS_LEGACY
        result["code"] = None
    return result


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #

def _check_registry(result: dict, profile_id: str, root: Path) -> dict | None:
    try:
        entry = registry.registry_entry(profile_id, root)
        registered = registry.registry_ids(root)
    except registry.VisualProfileError as exc:
        _fail(result, "profile_registered", getattr(exc, "code", ERROR_LOCK_INVALID),
              f"registry could not be read: {exc}")
        return None
    if entry is None:
        _fail(result, "profile_registered", ERROR_NOT_REGISTERED,
              f"profile_id={profile_id!r} is not registered in {registry.REGISTRY_REL.as_posix()} "
              f"(registered: {', '.join(registered)})")
        return None
    status = str(entry.get("status") or "").strip()
    if status != registry.ACTIVE_STATUS:
        _fail(result, "profile_registered", ERROR_NOT_ACTIVE,
              f"profile_id={profile_id!r} status={status!r} is not '{registry.ACTIVE_STATUS}'")
        return None
    _pass(result, "profile_registered", f"profile_id={profile_id!r} is registered and active")
    return entry


def _check_path(result: dict, lock: dict, entry: dict, root: Path) -> None:
    declared = normalize_rel(lock.get("profile_path"))
    expected = normalize_rel(entry.get("path"))
    result["profile_path"] = declared or None
    if not declared:
        _fail(result, "profile_path_matches_registry", ERROR_LOCK_INVALID,
              "profile_path is missing; a Visual Lock must name the registered profile document it locked")
        return
    if declared != expected:
        _fail(result, "profile_path_matches_registry", ERROR_PATH_MISMATCH,
              f"profile_path={declared} does not match the registry path {expected} for profile_id={lock.get('profile_id')!r}")
        return
    if not (root / declared).is_file():
        _fail(result, "profile_path_matches_registry", ERROR_FILE_MISSING,
              f"registered profile document is missing: {declared}")
        return
    _pass(result, "profile_path_matches_registry", f"profile_path matches the registry entry: {declared}")


def _check_evidence(result: dict, lock: dict) -> bool:
    evidence = lock.get("selection_evidence")
    if not isinstance(evidence, dict) or not evidence:
        _fail(result, "selection_evidence_present", ERROR_EVIDENCE_MISSING,
              "selection_evidence is missing; a locked profile must carry the selection fact "
              "(selector_version, inputs_digest, matched_rules, reason, source)")
        return False
    missing = []
    for field in EVIDENCE_REQUIRED_FIELDS:
        if field not in evidence:
            missing.append(field)
        elif field != "matched_rules" and evidence.get(field) in (None, "", [], {}):
            missing.append(field)
    if "matched_rules" not in missing and not isinstance(evidence.get("matched_rules"), list):
        missing.append("matched_rules")
    if missing:
        _fail(result, "selection_evidence_present", ERROR_EVIDENCE_MISSING,
              f"selection_evidence is missing required field(s): {', '.join(missing)}")
        return False
    digest = str(evidence.get("inputs_digest") or "")
    if DIGEST_RE.match(digest) is None:
        _fail(result, "selection_evidence_present", ERROR_EVIDENCE_MISSING,
              f"selection_evidence.inputs_digest={digest!r} is not 'sha256:' followed by 64 hex characters")
        return False
    matched_rules = evidence.get("matched_rules")
    if not all(isinstance(item, str) for item in matched_rules):
        _fail(result, "selection_evidence_present", ERROR_EVIDENCE_MISSING,
              "selection_evidence.matched_rules must be an array of strings")
        return False
    reason = evidence.get("reason")
    empty = (isinstance(reason, str) and not reason.strip()) or (isinstance(reason, list) and not reason)
    if empty:
        _fail(result, "selection_evidence_present", ERROR_EVIDENCE_MISSING,
              "selection_evidence.reason is empty; a selection must record why the profile was chosen")
        return False
    _pass(result, "selection_evidence_present",
          f"selection fact carried from selector_version={evidence.get('selector_version')!r} source={evidence.get('source')!r}")
    return True


def _check_adjudicated(result: dict, lock: dict) -> bool:
    status = lock_status(lock)
    if status is None:
        _skip(result, "selection_adjudicated", "no selector status declared; adjudication is not asserted by this lock")
        return True
    if status not in SELECTION_STATUSES:
        _fail(result, "selection_adjudicated", ERROR_LOCK_INVALID,
              f"selection status {status!r} is not one of {', '.join(SELECTION_STATUSES)}")
        return True
    if status in BLOCKED_STATUSES:
        _fail(result, "selection_adjudicated", ERROR_NOT_CONFIRMED,
              f"selection status is {status!r}; the profile choice is not adjudicated yet and must not enter a locked state")
        return False
    _pass(result, "selection_adjudicated", f"selection status is {status!r}")
    return True


def _check_confirmation(result: dict, lock: dict) -> None:
    mode = confirmation_mode(lock)
    if mode not in CONFIRMATION_MODES:
        _fail(result, "confirmation_recorded", ERROR_LOCK_INVALID,
              f"confirmation_mode={mode!r} is not one of {', '.join(CONFIRMATION_MODES)}")
        return
    if mode not in HUMAN_CONFIRMATION_MODES:
        _pass(result, "confirmation_recorded", f"confirmation_mode={mode!r} does not require a human confirmation record")
        return
    confirmed_by = str(lock.get("confirmed_by") or "").strip()
    confirmed_at = str(lock.get("confirmed_at") or "").strip()
    missing = [name for name, value in (("confirmed_by", confirmed_by), ("confirmed_at", confirmed_at)) if not value]
    if missing:
        _fail(result, "confirmation_recorded", ERROR_CONFIRMATION_MISSING,
              f"confirmation_mode={mode!r} requires {', '.join(missing)}")
        return
    if TIMESTAMP_RE.match(confirmed_at) is None:
        _fail(result, "confirmation_recorded", ERROR_CONFIRMATION_MISSING,
              f"confirmed_at={confirmed_at!r} is not an ISO-8601 timestamp")
        return
    _pass(result, "confirmation_recorded", f"confirmed_by={confirmed_by!r} confirmed_at={confirmed_at}")


def _check_shape(result: dict, lock: dict, root: Path) -> None:
    """Schema-subset pass for anything the named checks do not already cover."""
    schema = load_lock_schema(root)
    if not schema:
        return
    findings = registry.validate_json(lock, schema)
    if not findings:
        _pass(result, "lock_shape", "lock matches visual-lock.schema.json")
        return
    _fail(result, "lock_shape", ERROR_LOCK_INVALID, "; ".join(findings))


# --------------------------------------------------------------------------- #
# public API
# --------------------------------------------------------------------------- #

def validate_visual_profile_lock(
    lock: Any = None,
    *,
    story_root: Path | str | None = None,
    episode: Path | str | None = None,
    required: bool | None = None,
) -> dict[str, Any]:
    """Validate a Visual Lock. Read-only; it never writes to an Episode.

    lock        Visual Lock document (dict). When omitted and episode is given,
                meta/visual-profile.json is read.
    story_root  repository root used to resolve the registry (tests).
    episode     Episode directory used to locate the lock and to detect whether
                the Episode opted into Visual Profile governance.
    required    forced requirement flag. Default: derived from the Episode, or
                from the supplied document when there is no Episode.

    Returns a dict with status pass|fail|legacy_unmanaged, an explicit code for
    failures, the requirement decision, per-check detail and the error list.
    """
    root = _root(story_root)
    result = _blank_result()

    if lock is None and episode is not None:
        lock, source, load_error = load_lock(episode)
        result["source"] = source
        if load_error:
            _fail(result, "lock_readable", ERROR_LOCK_UNREADABLE, load_error)
            return _finish(result)
    elif lock is not None:
        result["source"] = "lock_document"

    if isinstance(required, bool):
        requirement = {"required": required, "reason": "explicit caller override"}
    elif episode is not None:
        requirement = visual_profile_requirement(episode)
    else:
        requirement = {
            "required": lock_is_governed(lock),
            "reason": "supplied lock document claims the visual lock contract" if lock_is_governed(lock)
                      else "no Episode context supplied",
        }
    result["required"] = bool(requirement["required"])
    result["requirement_reason"] = requirement["reason"]

    if lock is None:
        if result["required"]:
            _fail(result, "lock_present", ERROR_LOCK_MISSING,
                  f"this Episode declares it needs a Visual Profile ({requirement['reason']}) but has no "
                  f"{LOCK_REL.as_posix()}")
        else:
            _skip(result, "lock_present", f"no Visual Lock and no governance opt-in ({requirement['reason']})")
        return _finish(result)

    if not isinstance(lock, dict):
        _fail(result, "lock_readable", ERROR_LOCK_INVALID, "Visual Lock root must be a JSON object")
        return _finish(result)

    if not lock_is_governed(lock):
        result["governed"] = False
        result["requirement_reason"] = "pre-governance episode meta lock (no governance field)"
        _skip(result, "lock_present", "legacy episode meta lock: presence is not governance evidence, not judged")
        return _finish(result)
    result["governed"] = True
    result["judged"] = True

    profile_id = str(lock.get("profile_id") or "").strip()
    result["profile_id"] = profile_id or None
    if not profile_id:
        _fail(result, "profile_registered", ERROR_NOT_REGISTERED,
              "profile_id is missing; a Visual Lock must name the profile it locked")
        return _finish(result)

    entry = _check_registry(result, profile_id, root)
    if entry is None:
        return _finish(result)
    _check_path(result, lock, entry, root)
    _check_evidence(result, lock)
    if _check_adjudicated(result, lock):
        _check_confirmation(result, lock)
    else:
        _skip(result, "confirmation_recorded", "selection is not adjudicated yet; confirmation is not evaluated")
    _check_shape(result, lock, root)
    return _finish(result)


def verify(episode, *, metadata_only: bool = False, story_root: Path | str | None = None) -> list[str]:
    """Gate adapter: return error strings for a failing Episode, [] otherwise.

    A legacy or unmanaged Episode never produces errors, so wiring this into a
    future gate cannot retroactively fail historical Episodes.
    """
    if metadata_only:
        return []
    result = validate_visual_profile_lock(story_root=story_root, episode=episode)
    if result["status"] != STATUS_FAIL:
        return []
    return [f"{error['code']}: {error['detail']}" for error in result["errors"]]


# --------------------------------------------------------------------------- #
# CLI (read-only)
# --------------------------------------------------------------------------- #

def cmd_validate(args: argparse.Namespace) -> int:
    target = Path(args.target)
    if target.is_dir():
        result = validate_visual_profile_lock(episode=target)
    else:
        lock = read_json(target, default=None)
        if lock is None:
            result = _finish(_blank_result_with(ERROR_LOCK_UNREADABLE,
                                                f"lock document is unreadable or not a JSON object: {target}"))
        else:
            result = validate_visual_profile_lock(lock)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == STATUS_FAIL else 0


def _blank_result_with(code: str, detail: str) -> dict[str, Any]:
    result = _blank_result()
    _fail(result, "lock_readable", code, detail)
    result["status"] = STATUS_FAIL
    result["code"] = code
    return result


def cmd_verify(args: argparse.Namespace) -> int:
    errors = verify(Path(args.episode_dir), metadata_only=getattr(args, "metadata_only", False))
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 2
    print("VISUAL PROFILE LOCK VERIFIED")
    return 0


def self_test() -> None:
    assert normalize_rel(".\\standards/visual_profiles\\M00.json") == "standards/visual_profiles/M00.json"
    assert lock_status({"selection": "selected"}) == "selected"
    assert lock_status({"selection": {"status": "defaulted"}}) == "defaulted"
    assert lock_status({"status": "selected", "selection": {"status": "defaulted"}}) == "selected"
    assert lock_status({"lock_status": "locked"}) is None
    assert lock_is_governed({"profile_id": "M00", "mode": "explicit_user_locked"}) is False
    assert lock_is_governed({"selection_evidence": {}}) is True
    assert confirmation_mode({}) == "human"
    assert confirmation_mode({"confirmation_mode": "system"}) == "system"

    entry = registry.registry_entry("M00")
    assert entry is not None, "M00 must be registered"
    lock = {
        "schema_version": 1,
        "profile_id": "M00",
        "profile_path": entry["path"],
        "selection": "selected",
        "selection_evidence": {
            "selector_version": "1.0",
            "inputs_digest": "sha256:" + "a" * 64,
            "matched_rules": ["world=real"],
            "reason": ["prio=semantic"],
            "source": "rule_engine",
        },
        "confirmed_by": "reviewer",
        "confirmed_at": "2026-09-11T00:00:00+08:00",
        "confirmation_mode": "human",
    }
    assert validate_visual_profile_lock(lock)["status"] == STATUS_PASS, validate_visual_profile_lock(lock)
    drifted = dict(lock, profile_path="standards/visual_profiles/nope.json")
    assert validate_visual_profile_lock(drifted)["code"] == ERROR_PATH_MISMATCH
    blocked = dict(lock, selection="needs_confirmation")
    assert validate_visual_profile_lock(blocked)["code"] == ERROR_NOT_CONFIRMED
    assert validate_visual_profile_lock(None)["status"] == STATUS_LEGACY
    assert validate_visual_profile_lock({"profile_id": "M00", "mode": "x"})["status"] == STATUS_LEGACY
    print("VISUAL PROFILE LOCK SELF-TEST PASS")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Story OS Visual Profile selection evidence gate (governance Phase 3.5)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    child = sub.add_parser("validate", help="validate an Episode directory or a Visual Lock document")
    child.add_argument("target")
    child.set_defaults(func=cmd_validate)
    child = sub.add_parser("verify", help="gate adapter: non-zero exit when the Episode lock fails")
    child.add_argument("episode_dir")
    child.add_argument("--metadata-only", action="store_true", dest="metadata_only")
    child.set_defaults(func=cmd_verify)
    sub.add_parser("self-test").set_defaults(func=lambda args: (self_test(), 0)[1])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
