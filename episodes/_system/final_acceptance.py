#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Episode-local final acceptance evidence reader (Story OS controlled exception).

A valid <episode>/meta/final-acceptance.json records that the direct user
accepted the current approved assets as final and accepts known defects on
publish. Gates honor it only for the episode that carries the file; every other
episode keeps full enforcement. Removing the file restores full gates.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path
import story_json
import runtime_portability
import approval_persistence

REL = Path("meta/final-acceptance.json")
EVENT_REL = Path("meta/runtime/final-acceptance-events.jsonl")
ALLOWED_SCOPES = frozenset({
    "production_gate",
    "frame_semantic",
    "story_semantic_trace",
    "fast_frame_scout",
})


def read_json(path: Path) -> dict:
    return story_json.read_json(path)


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def _normalized_frames(values: object) -> list[int]:
    if not isinstance(values, list):
        return []
    out: list[int] = []
    for raw in values:
        try:
            value = int(raw)
        except (TypeError, ValueError):
            continue
        if value > 0 and value not in out:
            out.append(value)
    return sorted(out)


def _normalized_scopes(values: object, *, legacy_default: bool = False) -> list[str]:
    if values is None and legacy_default:
        return sorted(ALLOWED_SCOPES)
    if not isinstance(values, list):
        return []
    return sorted({str(value) for value in values if str(value) in ALLOWED_SCOPES})


def _append_event(ep: Path, payload: dict) -> None:
    path = ep / EVENT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def valid(episode_dir) -> dict | None:
    """Return the acceptance payload when valid for gates, else None."""
    ep = Path(episode_dir).resolve()
    data = approval_persistence.load(ep, approval_persistence.FINAL_ACCEPTANCE)
    if not isinstance(data, dict):
        return None
    if data.get("schema_version") != 1:
        return None
    if data.get("decision") != "accept_current_as_final":
        return None
    if data.get("basis") != "direct_user_review":
        return None
    if data.get("accepted_assets") is not True:
        return None
    if data.get("revokes") is True:
        return None
    if not _nonempty(data.get("user_statement")):
        return None
    if not _nonempty(data.get("declared_at")):
        return None
    frames = _normalized_frames(data.get("known_defect_frames"))
    if not frames:
        return None
    scopes = _normalized_scopes(data.get("accepted_scopes"), legacy_default=True)
    if not scopes:
        return None
    return {**data, "known_defect_frames": frames, "accepted_scopes": scopes}


def allows(episode_dir, scope: str, frame=None) -> bool:
    """Canonical downgrade boundary for every final-acceptance consumer."""
    if scope not in ALLOWED_SCOPES:
        return False
    data = valid(episode_dir)
    if data is None or scope not in set(data.get("accepted_scopes") or []):
        return False
    if frame is None:
        return True
    try:
        wanted = int(frame)
    except (TypeError, ValueError):
        return False
    return wanted in set(_normalized_frames(data.get("known_defect_frames")))


def covers(episode_dir, frame) -> bool:
    """Backward-compatible frame-semantic acceptance query."""
    return allows(episode_dir, "frame_semantic", frame)


def record(episode_dir, *, user_statement: str, known_defect_frames: list[int], accepted_scopes: list[str], declared_at: str | None = None) -> dict:
    """Record direct-user final acceptance and append the corresponding event.

    This is the only canonical writer. It never infers user approval: callers must
    supply the exact direct-user statement and explicit downgrade scopes.
    """
    ep = Path(episode_dir).resolve()
    runtime_portability.assert_episode_directory(ep)
    statement = str(user_statement or "").strip()
    if not statement:
        raise ValueError("direct user statement is required")
    frames = _normalized_frames(known_defect_frames)
    if not frames:
        raise ValueError("at least one known defect frame is required")
    scopes = _normalized_scopes(accepted_scopes)
    if not scopes or set(scopes) != {str(x) for x in accepted_scopes}:
        raise ValueError(f"accepted scopes must be explicit subset of {sorted(ALLOWED_SCOPES)}")
    at = str(declared_at or now()).strip()
    payload = {
        "schema_version": 1,
        "decision": "accept_current_as_final",
        "basis": "direct_user_review",
        "accepted_assets": True,
        "revokes": False,
        "user_statement": statement,
        "declared_at": at,
        "known_defect_frames": frames,
        "accepted_scopes": scopes,
    }
    event = {
        "schema_version": 1,
        "event": "FINAL_ACCEPTANCE_RECORDED",
        "at": at,
        "user_statement": statement,
        "known_defect_frames": frames,
        "accepted_scopes": scopes,
    }
    # Event first is fail-closed: a crash can leave an inert event, but never an
    # active acceptance without its audit event.
    _append_event(ep, event)
    approval_persistence.save(ep, approval_persistence.FINAL_ACCEPTANCE, payload)
    return payload


def revoke(episode_dir, *, user_statement: str, declared_at: str | None = None) -> dict:
    """Revoke current acceptance while retaining immutable event history."""
    ep = Path(episode_dir).resolve()
    runtime_portability.assert_episode_directory(ep)
    statement = str(user_statement or "").strip()
    if not statement:
        raise ValueError("direct user revocation statement is required")
    current = approval_persistence.load(ep, approval_persistence.FINAL_ACCEPTANCE) or {}
    at = str(declared_at or now()).strip()
    event = {
        "schema_version": 1,
        "event": "FINAL_ACCEPTANCE_REVOKED",
        "at": at,
        "user_statement": statement,
    }
    _append_event(ep, event)
    payload = {
        **current,
        "schema_version": 1,
        "decision": "accept_current_as_final",
        "basis": "direct_user_review",
        "accepted_assets": True,
        "revokes": True,
        "user_statement": statement,
        "declared_at": at,
        "known_defect_frames": _normalized_frames(current.get("known_defect_frames")),
        "accepted_scopes": _normalized_scopes(current.get("accepted_scopes"), legacy_default=True),
    }
    approval_persistence.save(ep, approval_persistence.FINAL_ACCEPTANCE, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("record")
    p.add_argument("episode_dir")
    p.add_argument("--user-statement", required=True)
    p.add_argument("--frame", action="append", type=int, required=True)
    p.add_argument("--scope", action="append", required=True, choices=sorted(ALLOWED_SCOPES))
    p = sub.add_parser("revoke")
    p.add_argument("episode_dir")
    p.add_argument("--user-statement", required=True)
    p = sub.add_parser("show")
    p.add_argument("episode_dir")
    args = parser.parse_args()
    if args.cmd == "record":
        data = record(args.episode_dir, user_statement=args.user_statement, known_defect_frames=args.frame, accepted_scopes=args.scope)
    elif args.cmd == "revoke":
        data = revoke(args.episode_dir, user_statement=args.user_statement)
    else:
        data = valid(args.episode_dir)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
