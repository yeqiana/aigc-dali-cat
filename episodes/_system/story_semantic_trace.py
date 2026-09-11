#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W-22 Story Semantic Trace: prove why a frame exists, not just that it rendered.

The EP003 Production Exposure Audit found the machine could prove a story existed
and a frame rendered, but not that frame 19 exists *because* it is the climax or
that frame 20 exists *because* it is the payoff. This module owns the per-frame
evidence contract binding Story Lock -> Frame Contract -> frame review.

Recorded inside meta/frame-reviews/{frame}.json::

    "story_semantic_trace": {
      "required": true,
      "story_role": "climax",
      "story_lock": {"path": "<repo-relative>", "sha256": "<64 hex>"},
      "frame_contract_sha256": "<64 hex>",
      "evaluation": {"beat_delivered": true, "confidence": 0.9, "method": "..."},
      "provenance": {"source": "auto_review|human_review|delegated_review",
                     "reviewer": "<who>", "reviewed_at": "<iso>"}
    }

The Frame Contract publishes the matching requirement block::

    "story_semantic_requirements": {
      "required": true,
      "story_role": "climax",
      "story_function": null,
      "story_lock": {"path": "...", "sha256": "..."}
    }

Roles are derived from story-gates.story (hook_frames / escalation_frames /
climax_frame / payoff_frame); frames with no declared role are ordinary and carry
required=false. Nothing here is scored and no AI semantic model is used:
beat_delivered is a reviewer judgement recorded with its provenance. The gate
never accepts "story-gates has a role map" as evidence; it reads the review.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import story_json

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_REL = Path("meta/release-manifest.json")
GATES_REL = Path("meta/story-gates.json")
LEDGER_REL = Path("meta/production-ledger.json")
REVIEW_DIR = Path("meta/frame-reviews")
# Kept in sync with frame_contract.CACHE_ROOT (that module imports this one).
CONTRACT_CACHE_REL = Path("meta/runtime/contracts/frames")
PROVENANCE_SOURCES = ("auto_review", "human_review", "delegated_review")
ROLES = ("hook", "escalation", "climax", "payoff", "ordinary")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path, default=None):
    return story_json.read_json(path, default=default, require_object=False)


def write_json(path, data) -> None:
    story_json.write_json(path, data)


def sha256_file(path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_rel(path) -> str:
    return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()


def repo_abs(raw):
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = Path(raw.strip())
    candidate = candidate.resolve() if candidate.is_absolute() else (ROOT / candidate).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return candidate


def _as_frame(raw):
    try:
        return int(raw)
    except Exception:
        return None


def story_block(ep) -> dict:
    gates = read_json(Path(ep) / GATES_REL, {}) or {}
    story = gates.get("story") if isinstance(gates, dict) else None
    return story if isinstance(story, dict) else {}


def role_map(ep) -> dict:
    """Frame number -> declared story role, derived from story-gates.story.

    hook/escalation are lists; climax/payoff are singular and win over a list
    entry for the same frame. Frames absent from the map are ordinary.
    """
    story = story_block(ep)
    out = {}
    for key, role in (("hook_frames", "hook"), ("escalation_frames", "escalation")):
        values = story.get(key)
        if not isinstance(values, list):
            continue
        for value in values:
            number = _as_frame(value)
            if number is not None:
                out.setdefault(number, role)
    for key, role in (("climax_frame", "climax"), ("payoff_frame", "payoff")):
        number = _as_frame(story.get(key))
        if number is not None:
            out[number] = role
    return out


def required(ep) -> bool:
    """True when the episode declares any story role map at all."""
    return bool(role_map(ep))


def story_lock(ep) -> dict:
    """The Story Lock the episode is bound to (manifest.artifacts.story)."""
    manifest = read_json(Path(ep) / MANIFEST_REL, {}) or {}
    raw = (manifest.get("artifacts") or {}).get("story")
    path = repo_abs(raw)
    if path is None or not path.is_file():
        return {"path": (str(raw) if raw else None), "sha256": None}
    return {"path": repo_rel(path), "sha256": sha256_file(path)}


def story_function(ep, frame, role=None):
    """Optional free-text reason a frame exists; never required by the gate."""
    story = story_block(ep)
    number = _as_frame(frame)
    for key in ("frame_functions", "story_functions"):
        mapping = story.get(key)
        if not isinstance(mapping, dict):
            continue
        for candidate in (f"{number:02d}", str(number), number):
            if candidate in mapping:
                return mapping[candidate]
    role = role or role_map(ep).get(number, "ordinary")
    mapping = story.get("role_functions")
    if isinstance(mapping, dict) and role in mapping:
        return mapping[role]
    return None


def contract_requirements(ep, frame, story_lock_block=None) -> dict:
    """Per-frame semantic requirement published into the Frame Contract."""
    number = _as_frame(frame)
    role = role_map(ep).get(number, "ordinary")
    lock = story_lock_block if isinstance(story_lock_block, dict) else story_lock(ep)
    return {
        "required": role != "ordinary",
        "story_role": role,
        "story_function": story_function(ep, frame, role),
        "story_lock": {"path": lock.get("path"), "sha256": lock.get("sha256")},
    }


def requirements_from_contract(ep, frame):
    """Read the requirement block the Frame Contract published, if any."""
    data = read_json(Path(ep) / CONTRACT_CACHE_REL / f"{int(frame):02d}.json")
    block = data.get("story_semantic_requirements") if isinstance(data, dict) else None
    return block if isinstance(block, dict) else None


def frame_requirements(ep, frame) -> dict:
    return requirements_from_contract(ep, frame) or contract_requirements(ep, frame)


def trace_from_review(review):
    if not isinstance(review, dict):
        return None
    trace = review.get("story_semantic_trace")
    return trace if isinstance(trace, dict) else None


def attempt_contract_sha(attempt):
    """The Frame Contract SHA the accepted generation attempt was bound to."""
    if not isinstance(attempt, dict):
        return None
    request = attempt.get("request") if isinstance(attempt.get("request"), dict) else {}
    block = request.get("frame_contract") if isinstance(request.get("frame_contract"), dict) else {}
    token = str(block.get("contract_sha256") or "").strip()
    return token or None


def validate_frame(trace, requirement, expected_contract_sha=None) -> list:
    """Return (code, message) findings proving a frame carries its story role."""
    findings = []
    if not isinstance(trace, dict):
        return [("story_semantic_trace_missing",
                 "frame requires a story semantic trace but the frame review has none")]
    if trace.get("required") is not True:
        findings.append(("story_semantic_trace_not_required",
                         "story_semantic_trace.required must be true"))
    want_role = str((requirement or {}).get("story_role") or "").lower()
    got_role = str(trace.get("story_role") or "").lower()
    if got_role != want_role:
        findings.append(("story_role_mismatch",
                         "story_semantic_trace.story_role " + repr(got_role) + " != declared " + repr(want_role)))
    want_lock = (requirement or {}).get("story_lock") or {}
    lock = trace.get("story_lock")
    if not isinstance(lock, dict) or not lock.get("path") or not lock.get("sha256"):
        findings.append(("story_lock_missing",
                         "story_semantic_trace.story_lock needs path and sha256"))
    else:
        if str(lock.get("path")) != str(want_lock.get("path") or ""):
            findings.append(("story_lock_path_mismatch",
                             "trace story_lock " + str(lock.get("path")) + " != declared " + str(want_lock.get("path"))))
        want_sha = str(want_lock.get("sha256") or "").lower()
        got_sha = str(lock.get("sha256") or "").lower()
        if want_sha and got_sha != want_sha:
            findings.append(("story_lock_hash_drift",
                             "trace story_lock sha " + got_sha[:12] + " != current story lock " + want_sha[:12]))
    if expected_contract_sha:
        got_contract = str(trace.get("frame_contract_sha256") or "").lower()
        if got_contract != str(expected_contract_sha).lower():
            findings.append(("frame_contract_hash_drift",
                             "trace frame_contract_sha256 " + (got_contract[:12] or repr(got_contract))
                             + " != attempt contract " + str(expected_contract_sha).lower()[:12]))
    evaluation = trace.get("evaluation")
    if not isinstance(evaluation, dict):
        findings.append(("semantic_evaluation_missing",
                         "story_semantic_trace.evaluation is required"))
    else:
        if evaluation.get("beat_delivered") is not True:
            findings.append(("semantic_beat_not_delivered",
                             "evaluation.beat_delivered must be true"))
        confidence = evaluation.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            findings.append(("semantic_confidence_missing",
                             "evaluation.confidence must be a number"))
        if not str(evaluation.get("method") or "").strip():
            findings.append(("semantic_method_missing",
                             "evaluation.method must record how the beat was judged"))
    provenance = trace.get("provenance")
    if not isinstance(provenance, dict) or str(provenance.get("source") or "") not in PROVENANCE_SOURCES:
        findings.append(("semantic_evidence_missing_provenance",
                         "story_semantic_trace.provenance.source must be one of " + "/".join(PROVENANCE_SOURCES)))
    return findings


def review_path(ep, frame) -> Path:
    return Path(ep).resolve() / REVIEW_DIR / f"{int(frame):02d}.json"


def accepted_attempt(frame):
    """The generation attempt whose pixels the frame currently accepts."""
    if not isinstance(frame, dict):
        return None
    attempts = [a for a in (frame.get("attempts") or []) if isinstance(a, dict)]
    approved = frame.get("approved_asset") if isinstance(frame.get("approved_asset"), dict) else {}
    candidate = frame.get("current_candidate") if isinstance(frame.get("current_candidate"), dict) else {}
    for sha in (approved.get("source_sha256"), candidate.get("sha256")):
        token = str(sha or "")
        if not token:
            continue
        for attempt in reversed(attempts):
            if str((attempt.get("candidate") or {}).get("sha256") or "") == token:
                return attempt
    attempt_id = str(candidate.get("attempt_id") or "")
    if attempt_id:
        for attempt in reversed(attempts):
            if str(attempt.get("attempt_id") or "") == attempt_id:
                return attempt
    for attempt in reversed(attempts):
        if attempt.get("result") == "success":
            return attempt
    return None


def verify(ep, *, ledger=None, metadata_only=False) -> list:
    ep = Path(ep).resolve()
    if metadata_only:
        return []
    if not required(ep):
        return []
    ledger = ledger if isinstance(ledger, dict) else (read_json(ep / LEDGER_REL, {}) or {})
    marker = ledger.get("story_semantic_trace_evidence")
    if not isinstance(marker, dict) or marker.get("schema_version") != 1:
        # Ledger produced before the semantic trace existed: legacy scope.
        return []
    enforced_from = str(marker.get("enforced_from") or "")
    errors = []
    frames = ledger.get("frames") if isinstance(ledger.get("frames"), dict) else {}
    for key in sorted(frames):
        attempt = accepted_attempt(frames.get(key))
        if not isinstance(attempt, dict):
            continue
        requirement = frame_requirements(ep, int(key))
        if requirement.get("required") is not True:
            continue
        started_at = str(attempt.get("started_at") or "")
        if enforced_from and started_at and started_at < enforced_from:
            continue
        review = read_json(review_path(ep, int(key)), {}) or {}
        trace = trace_from_review(review)
        for code, message in validate_frame(trace, requirement, attempt_contract_sha(attempt)):
            errors.append(f"frame {key}: {code}: {message}")
    return errors


def _contract_sha(ep, frame):
    data = read_json(Path(ep) / CONTRACT_CACHE_REL / f"{int(frame):02d}.json")
    if isinstance(data, dict):
        token = str(data.get("contract_sha256") or "").strip()
        if token:
            return token
    return None


def attach(ep, frame, *, method, source, confidence, story_role=None, beat_delivered=True,
           reviewer=None, story_lock_path=None, story_lock_sha256=None,
           frame_contract_sha256=None, write=True) -> dict:
    """Merge one frame story semantic trace into meta/frame-reviews/{frame}.json."""
    ep = Path(ep).resolve()
    path = review_path(ep, frame)
    review = read_json(path)
    if not isinstance(review, dict):
        raise ValueError(f"frame review missing or invalid: {path}")
    requirement = contract_requirements(ep, frame)
    lock = dict(requirement.get("story_lock") or {})
    if story_lock_path is not None:
        resolved = repo_abs(story_lock_path)
        if resolved is not None and resolved.is_file():
            lock = {"path": repo_rel(resolved), "sha256": sha256_file(resolved)}
        else:
            lock = {"path": str(story_lock_path), "sha256": story_lock_sha256}
    if story_lock_sha256:
        lock["sha256"] = str(story_lock_sha256).lower()
    if frame_contract_sha256 is None:
        frame_contract_sha256 = _contract_sha(ep, frame)
    trace = trace_from_review(review) or {}
    trace.update({
        "required": bool(requirement.get("required")),
        "story_role": str(story_role or requirement.get("story_role") or "ordinary").lower(),
        "story_lock": {"path": lock.get("path"), "sha256": lock.get("sha256")},
        "frame_contract_sha256": frame_contract_sha256,
        "evaluation": {
            "beat_delivered": bool(beat_delivered),
            "confidence": float(confidence),
            "method": str(method),
        },
        "provenance": {"source": str(source), "reviewer": reviewer, "reviewed_at": now()},
    })
    review["story_semantic_trace"] = trace
    if write:
        write_json(path, review)
    return review


def self_test() -> None:
    import tempfile
    global ROOT
    with tempfile.TemporaryDirectory(prefix="story semantic self test ") as td:
        ep = Path(td) / "episodes/99_semantic"
        (ep / "meta").mkdir(parents=True)
        write_json(ep / "meta/story-gates.json", {"story": {
            "hook_frames": [1, 2], "escalation_frames": ["3"],
            "climax_frame": 19, "payoff_frame": 20}})
        original = ROOT
        ROOT = Path(td)
        try:
            roles = role_map(ep)
            assert roles[1] == "hook" and roles[2] == "hook"
            assert roles[3] == "escalation" and roles[19] == "climax" and roles[20] == "payoff"
            assert required(ep) is True
            assert contract_requirements(ep, 19)["story_role"] == "climax"
            assert contract_requirements(ep, 19)["required"] is True
            assert contract_requirements(ep, 7) == {
                "required": False, "story_role": "ordinary", "story_function": None,
                "story_lock": {"path": None, "sha256": None}}
        finally:
            ROOT = original
    assert validate_frame(None, {"story_role": "climax"}) != []
    print("STORY SEMANTIC TRACE SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("requirements"); p.add_argument("episode_dir"); p.add_argument("--frame", type=int)
    p = sub.add_parser("verify"); p.add_argument("episode_dir")
    p = sub.add_parser("attach")
    p.add_argument("episode_dir"); p.add_argument("--frame", type=int, required=True)
    p.add_argument("--method", required=True)
    p.add_argument("--source", choices=list(PROVENANCE_SOURCES), required=True)
    p.add_argument("--confidence", type=float, required=True)
    p.add_argument("--story-role")
    p.add_argument("--reviewer")
    p.add_argument("--not-delivered", action="store_true")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test(); return 0
    ep = Path(args.episode_dir).resolve()
    if args.cmd == "requirements":
        if args.frame:
            print(json.dumps(frame_requirements(ep, args.frame), ensure_ascii=False, indent=2)); return 0
        print(json.dumps({str(n): frame_requirements(ep, n) for n in range(1, 21)},
                         ensure_ascii=False, indent=2)); return 0
    if args.cmd == "attach":
        review = attach(ep, args.frame, method=args.method, source=args.source,
                        confidence=args.confidence, story_role=args.story_role,
                        beat_delivered=not args.not_delivered, reviewer=args.reviewer)
        print(json.dumps(review.get("story_semantic_trace"), ensure_ascii=False, indent=2)); return 0
    errors = verify(ep)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 2
    print("STORY SEMANTIC TRACE VERIFIED"); return 0


if __name__ == "__main__":
    raise SystemExit(main())

