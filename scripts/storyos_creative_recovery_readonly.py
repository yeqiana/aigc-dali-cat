#!/usr/bin/env python3
"""Read-only triage for a paid CREATIVE_STORY receipt with an unfinished Story Lock.

Never infers Story Gate PASS from a model SUCCESS. Does not write or dispatch.
For formal MySQL production state, invoke via storyos_production_env.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYS = ROOT / "episodes" / "_system"
if str(SYS) not in sys.path:
    sys.path.insert(0, str(SYS))
import character_contract

MAX_JSON_BYTES = 65536


def _json_bounded(path: Path) -> dict | None:
    try:
        if not path.is_file() or path.stat().st_size > MAX_JSON_BYTES:
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (ValueError, OSError):
        return None


def _creative_receipts(ep: Path) -> int:
    folder = ep / "meta" / "provider-receipts"
    if not folder.is_dir():
        return 0
    number = 0
    for f in folder.glob("*.json"):
        receipt = _json_bounded(f)
        if not receipt:
            continue
        if (receipt.get("step") == "CREATIVE_STORY"
                and receipt.get("provider") == "codex_subscription"
                and receipt.get("status") == "SUCCESS"):
            number += 1
    return number


def inspect(ep: Path) -> dict:
    """Return evidence disposition only, NOT entitlement or authorization."""
    ep = Path(ep).resolve()
    if not ep.is_dir():
        return {"status": "EPISODE_PATH_NOT_FOUND", "read_only": True}
    try:
        contract = character_contract.load(ep)
        current_sha = character_contract.authority_sha256(ep)
    except Exception:
        # Never render database DSNs or exception repr in diagnostics.
        return {"status": "CHARACTER_AUTHORITY_UNAVAILABLE", "read_only": True}
    if not isinstance(contract, dict) or not current_sha:
        return {"status": "CHARACTER_AUTHORITY_MISSING", "read_only": True}
    successful = _creative_receipts(ep)
    review_path = ep / "meta" / "character-story-review.json"
    review = _json_bounded(review_path)
    base = {
        "scope": "CREATIVE_STORY_READ_ONLY_RECOVERY",
        "status": "NEEDS_EVIDENCE",
        "contract_status": contract.get("status"),
        "model_success_receipt_count": successful,
        "model_success_is_story_lock": False,
        "model_generation_required": None,
        "review_path_present": bool(review),
        "read_only": True,
        "sql_writes": 0,
        "model_calls": 0,
    }
    if contract.get("status") == "LOCKED":
        base["status"] = "CONTRACT_ALREADY_LOCKED_VERIFY_STORY_GATES"
        return base
    if contract.get("status") != "DRAFT":
        base["status"] = "CONTRACT_STATUS_UNSUPPORTED_FOR_AUTOMATIC_REPAIR"
        return base
    if not review:
        base["status"] = ("MODEL_SUCCEEDED_BUT_STORY_REVIEW_MISSING"
                          if successful else "REVIEW_EVIDENCE_NOT_YET_CREATED")
        return base
    if review.get("schema_version") != 1:
        base["status"] = "REVIEW_SCHEMA_INVALID"
        return base
    if review.get("expected_contract_sha256") != current_sha:
        base["status"] = "REVIEW_CONTRACT_SHA_STALE"
        return base
    rel = Path(str(review.get("story_path") or ""))
    story = (ep / rel).resolve()
    if (rel.is_absolute() or not story.is_relative_to(ep) or not story.is_file()
            or story.suffix.lower() not in {".md", ".txt", ".json"}):
        base["status"] = "REVIEW_STORY_PATH_INVALID"
        return base
    try:
        source = story.read_bytes()
    except OSError:
        base["status"] = "REVIEW_STORY_UNREADABLE"
        return base
    if len(source) < 100 or hashlib.sha256(source).hexdigest() != review.get("story_sha256"):
        base["status"] = "REVIEW_STORY_SHA_DRIFT"
        return base
    no = review.get("no_anomaly_test") or {}
    if (no.get("pass") is not True
            or len(str(no.get("ordinary_day_plan") or "").strip()) < 10
            or len(str(no.get("review_reason") or "").strip()) < 20):
        base["status"] = "REVIEW_NO_ANOMALY_EVIDENCE_INCOMPLETE"
        return base
    # This does not independently validate creative quality or lock the contract.
    base["status"] = "REVIEW_EVIDENCE_PRESENT_CAN_ATTEMPT_CANONICAL_LOCK"
    return base


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    ns = parser.parse_args(argv)
    root = ROOT / "episodes"
    ep = Path(ns.episode)
    ep = (ep if ep.is_absolute() else ROOT / ep).resolve()
    if not ep.is_relative_to(root.resolve()):
        print(json.dumps({"status": "EPISODE_PATH_INVALID", "read_only": True}))
        return 2
    report = inspect(ep)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] not in {
        "EPISODE_PATH_NOT_FOUND", "EPISODE_PATH_INVALID",
        "CHARACTER_AUTHORITY_UNAVAILABLE", "CHARACTER_AUTHORITY_MISSING"
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
