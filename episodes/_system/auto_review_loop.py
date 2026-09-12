#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS Auto Review Loop (Autonomous Production Pipeline Phase 5.3).

Purpose:
    Rule review of an Episode's *existing* evidence. For every frame known to the
    Episode it re-uses the contracts that already own the rules:

        story_semantic_trace    why a frame exists (W-22)
        identity_continuity     who is in a frame (P1-1)
        visual_profile_gate     which visual world the Episode renders in (4.3)

    and reports one of

        PASS -> REPAIR_REQUIRED -> FAILED

Boundaries
----------
- Report only. Nothing is written and nothing is blocked: no model, no scoring,
  no image inspection, no Runtime call. repair_engine owns the legal repair
  actions, so this module never invents a remedy.
- Legacy scope is respected exactly like the machine gate: a frame is only judged
  when its module's ledger marker is present and the accepted attempt started at
  or after the recorded enforced_from.
- FAILED means "no automatic repair task can be derived from this finding", not
  "the picture is bad". A report with no known frames is a vacuous PASS and says so.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    # Repo convention is script execution (python episodes/_system/x.py). The same
    # module is also runnable as python -m episodes._system.x, which puts the
    # repository root on sys.path instead, so both entry points are kept working.
    sys.path.insert(0, str(_HERE))

import identity_continuity  # noqa: E402
import repair_engine  # noqa: E402
import story_json  # noqa: E402
import story_semantic_trace  # noqa: E402
import visual_profile_gate  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

LOOP_VERSION = "1.0"
MODE = "report_only"

LEDGER_REL = Path("meta/production-ledger.json")
REVIEW_DIR = Path("meta/frame-reviews")
CONTRACT_CACHE_REL = Path("meta/runtime/contracts/frames")

SEMANTIC_MARKER = "story_semantic_trace_evidence"
IDENTITY_MARKER = "identity_continuity_evidence"

STATUS_PASS = "PASS"
STATUS_REPAIR_REQUIRED = "REPAIR_REQUIRED"
STATUS_FAILED = "FAILED"
STATUSES = (STATUS_PASS, STATUS_REPAIR_REQUIRED, STATUS_FAILED)

ERROR_EPISODE_MISSING = "AUTO_REVIEW_EPISODE_MISSING"
ERROR_VISUAL_PROFILE_GATE = "VISUAL_PROFILE_GATE_FAILED"


class AutoReviewError(SystemExit):
    """Fail-fast loop error (shares the registry SystemExit convention)."""

    code = ERROR_EPISODE_MISSING

    def __init__(self, message, code=None):
        self.code = code or self.code
        super().__init__(self.code + ": " + str(message))


def _root(story_root=None) -> Path:
    return Path(story_root) if story_root else ROOT


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path, default=None):
    return story_json.read_json(path, default=default, require_object=False)


def ledger_of(ep, ledger=None) -> dict:
    if isinstance(ledger, dict):
        return ledger
    data = read_json(Path(ep) / LEDGER_REL, {})
    return data if isinstance(data, dict) else {}


def frame_numbers(ep, ledger=None) -> list:
    """Frames this Episode knows about: ledger, frame reviews, contract cache."""
    ep = Path(ep)
    numbers = set()
    for key in (ledger_of(ep, ledger).get("frames") or {}):
        try:
            numbers.add(int(key))
        except (TypeError, ValueError):
            continue
    for folder in (ep / REVIEW_DIR, ep / CONTRACT_CACHE_REL):
        if not folder.is_dir():
            continue
        for path in folder.glob("*.json"):
            try:
                numbers.add(int(path.stem))
            except ValueError:
                continue
    return sorted(numbers)


def _marker(ledger: dict, key: str):
    marker = (ledger or {}).get(key)
    if isinstance(marker, dict) and marker.get("schema_version") == 1:
        return marker
    return None


def _in_scope(attempt, enforced_from: str) -> bool:
    """Mirror the gate legacy scope: only attempts inside enforced_from count."""
    if not isinstance(attempt, dict):
        return False
    if not enforced_from:
        return True
    started_at = str(attempt.get("started_at") or "")
    if not started_at:
        return True
    return started_at >= enforced_from


def _issue(code, message, *, frame, category=None, action=None, owner=None,
           repairable=None) -> dict:
    rule = repair_engine.classify(code)
    return {
        "frame": frame,
        "code": str(code),
        "message": str(message),
        "category": category or rule["category"],
        "action": action or rule["action"],
        "owner": owner or rule["owner"],
        "repairable": rule["repairable"] if repairable is None else bool(repairable),
        "source": rule["source"],
    }


def evaluate_frame(ep, frame, *, ledger=None, story_root=None) -> dict:
    """Rule review of one frame. Read-only."""
    ep = Path(ep)
    ledger = ledger_of(ep, ledger)
    key = "%02d" % int(frame)
    row = (ledger.get("frames") or {}).get(key)
    review = read_json(ep / REVIEW_DIR / (key + ".json"), {})
    review = review if isinstance(review, dict) else {}
    issues: list = []

    semantic_marker = _marker(ledger, SEMANTIC_MARKER)
    if semantic_marker and story_semantic_trace.required(ep):
        attempt = story_semantic_trace.accepted_attempt(row)
        requirement = story_semantic_trace.frame_requirements(ep, int(frame))
        if attempt is not None and requirement.get("required") is True \
                and _in_scope(attempt, str(semantic_marker.get("enforced_from") or "")):
            trace = story_semantic_trace.trace_from_review(review)
            for code, message in story_semantic_trace.validate_frame(
                    trace, requirement, story_semantic_trace.attempt_contract_sha(attempt)):
                issues.append(_issue(code, message, frame=key))

    identity_marker = _marker(ledger, IDENTITY_MARKER)
    if identity_marker and identity_continuity.identity_contract(ep).get("required"):
        attempt = identity_continuity.accepted_attempt(row)
        requirements = identity_continuity.frame_requirements(ep, int(frame), ledger)
        if attempt is not None and requirements \
                and _in_scope(attempt, str(identity_marker.get("enforced_from") or "")):
            authority = identity_continuity.anchor_authority(ep)
            for code, message in identity_continuity.validate_frame(
                    identity_continuity.evidence_from_review(review), requirements, authority):
                issues.append(_issue(code, message, frame=key))

    status = STATUS_PASS
    if any(not issue["repairable"] for issue in issues):
        status = STATUS_FAILED
    elif issues:
        status = STATUS_REPAIR_REQUIRED
    return {"frame": key, "status": status, "issues": issues}


def review(ep, *, story_root=None, frames=None, ledger=None) -> dict:
    """Report the review status of an Episode. Writes nothing."""
    ep = Path(ep).resolve()
    if not ep.is_dir():
        raise AutoReviewError("episode directory not found: " + ep.as_posix())
    repo = _root(story_root)
    ledger = ledger_of(ep, ledger)

    visual = visual_profile_gate.validate_visual_profile_for_production(
        episode=ep, story_root=repo)
    issues: list = []
    if visual.get("status") == visual_profile_gate.STATUS_FAIL:
        issues.append(_issue(
            str(visual.get("code") or ERROR_VISUAL_PROFILE_GATE),
            "the Visual Profile gate refuses this Episode: "
            + str((visual.get("errors") or ["unknown reason"])[0]),
            frame=None, category=repair_engine.CATEGORY_VISUAL_PROFILE,
        ))

    numbers = [int(n) for n in frames] if frames else frame_numbers(ep, ledger)
    frame_reports = [evaluate_frame(ep, n, ledger=ledger, story_root=repo) for n in numbers]
    for report in frame_reports:
        issues.extend(report["issues"])

    if any(not issue["repairable"] for issue in issues):
        status = STATUS_FAILED
    elif issues:
        status = STATUS_REPAIR_REQUIRED
    else:
        status = STATUS_PASS

    semantic_gate = story_semantic_trace.verify(ep, ledger=ledger)
    identity_gate = identity_continuity.verify(ep, ledger=ledger)
    semantic_loop = [i for i in issues
                     if i["frame"] and i["category"] == repair_engine.CATEGORY_SEMANTIC]
    identity_loop = [i for i in issues
                     if i["frame"] and i["category"] == repair_engine.CATEGORY_IDENTITY]
    cross_check = {
        "story_semantic_trace": {
            "gate_findings": len(semantic_gate),
            "loop_findings": len(semantic_loop),
            "agree": len(semantic_gate) == len(semantic_loop),
        },
        "identity_continuity": {
            "gate_findings": len(identity_gate),
            "loop_findings": len(identity_loop),
            "agree": len(identity_gate) == len(identity_loop),
        },
    }
    notes = []
    if not numbers:
        notes.append("no production artifacts known yet: vacuous PASS, nothing was reviewed")
    for name, block in cross_check.items():
        if not block["agree"]:
            notes.append("review loop and " + name + " gate disagree on the finding count; "
                         "treat as drift until reconciled")

    return {
        "schema_version": 1,
        "loop_version": LOOP_VERSION,
        "mode": MODE,
        "episode_id": ep.name,
        "episode_dir": ep.as_posix(),
        "status": status,
        "coverage": {
            "frames_known": len(numbers),
            "frames_checked": len(frame_reports),
            "vacuous": not numbers,
            "story_semantic_required": bool(story_semantic_trace.required(ep)),
            "identity_required": bool(identity_continuity.identity_contract(ep).get("required")),
            "visual_profile_required": bool(visual.get("required")),
        },
        "visual_profile": {
            "status": visual.get("status"),
            "code": visual.get("code"),
            "required": bool(visual.get("required")),
            "profile_id": visual.get("profile_id"),
            "lifecycle_state": visual.get("lifecycle_state"),
        },
        "frames": frame_reports,
        "issues": issues,
        "evidence": {
            "sources": [
                LEDGER_REL.as_posix(),
                REVIEW_DIR.as_posix(),
                CONTRACT_CACHE_REL.as_posix(),
            ],
            "read_only": True,
            "checked_at": now(),
            "cross_check": cross_check,
        },
        "notes": notes,
    }


def format_report(report: dict) -> str:
    coverage = report.get("coverage") or {}
    visual = report.get("visual_profile") or {}
    lines = [
        "Auto Review Loop (report only)",
        "Episode:        " + str(report.get("episode_id")),
        "Status:         " + str(report.get("status")),
        "Frames:         " + str(coverage.get("frames_known")) + " known / "
        + str(coverage.get("frames_checked")) + " checked"
        + ("   (vacuous: nothing produced yet)" if coverage.get("vacuous") else ""),
        "Visual Profile: " + str(visual.get("status")) + " / "
        + str(visual.get("lifecycle_state") or "-"),
        "Issues:         " + str(len(report.get("issues") or [])),
    ]
    for frame in report.get("frames") or []:
        if not frame["issues"]:
            continue
        lines.append("")
        lines.append("frame " + frame["frame"] + "  " + frame["status"])
        for issue in frame["issues"]:
            lines.append("  - " + issue["code"] + " [" + issue["category"]
                         + (", auto-repairable" if issue["repairable"]
                            else ", needs human review") + "]")
            lines.append("    " + issue["message"])
    for issue in report.get("issues") or []:
        if issue["frame"]:
            continue
        lines.append("")
        lines.append("episode  " + str(issue["code"]) + " [" + issue["category"] + "]")
        lines.append("    " + issue["message"])
    for note in report.get("notes") or []:
        lines.append("")
        lines.append("note: " + note)
    return chr(10).join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("review", help="report the review status of an Episode")
    p.add_argument("episode_dir")
    p.add_argument("--root", help="repository root (defaults to this checkout)")
    p.add_argument("--json", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = review(args.episode_dir, story_root=_root(args.root))
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json
          else format_report(report))
    return 0 if report["status"] == STATUS_PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
