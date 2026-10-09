#!/usr/bin/env python3
"""Read-only, fail-closed reconciliation report for image Attempt authority.

Never reserves, retries, promotes, restores, or edits an image or Provider receipt.
The report distinguishes worker *completion* from Provider *success*.
Run via: python scripts/storyos_production_env.py scripts/storyos_generation_evidence_audit.py --episode episodes/...
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import generation_attempt_authority as attempts
import image_blocked_recovery
import scheduler_core


def inspect(ep: Path) -> dict:
    ep = Path(ep).resolve()
    ep.relative_to((ROOT / "episodes").resolve())  # never inspect foreign paths
    if not ep.is_dir():
        raise FileNotFoundError(ep)
    queue = scheduler_core.load_queue(ep)
    rows: list[dict] = []
    for item in queue.get("items") or []:
        if not isinstance(item, dict) or item.get("status") != "tech_failed":
            continue
        frame = int(item.get("frame") or 0)
        if frame <= 0:
            continue
        key = attempts.frame_key(ep, frame)
        state = attempts.load_asset_state(ep, key)
        consumed = int(state.get("attempts_consumed") or 0)
        previous = attempts.load_attempt(ep, key, consumed) if consumed else None
        status = str((previous or {}).get("status") or "MISSING")
        code = str(item.get("technical_failure_code") or "")
        recovery = image_blocked_recovery.inspect_item(ep, item)
        worker_logs = sorted((ep / "meta" / "image-workers").glob(f"{frame:02d}-*.lifecycle.json"))
        raw_files = sorted((ep / "media" / "raw").glob(f"{frame:02d}-*"))
        row = {
            "frame": frame,
            "queue_status": "tech_failed",
            "technical_failure_code": code,
            "attempts_consumed": consumed,
            "authority_status": status,
            "authority_provider": str((previous or {}).get("provider") or ""),
            "authority_result_ref_present": bool((previous or {}).get("result_ref")),
            "worker_lifecycle_file_count": len(worker_logs),
            "raw_candidate_count": sum(f.is_file() for f in raw_files),
            "non_regenerating_recovery_allowed": bool(recovery.get("auto_resolvable")),
            "recovery_reason": str(recovery.get("reason") or ""),
        }
        # A completed worker is never an Authority terminal receipt. Even with
        # available budget, UNKNOWN and in-flight states cannot authorize retry.
        row["automatic_retry_permitted"] = False  # this audit never grants retry authority
        row["decision"] = (
            "VERIFY_PROVIDER_TERMINAL_EVIDENCE"
            if status in {"OUTCOME_UNKNOWN", "DISPATCH_COMMITTED", "RESERVED", "MISSING"}
            else "REQUIRE_INDEPENDENT_RETRY_ADMISSION"
        )
        rows.append(row)
    rows.sort(key=lambda r: r["frame"])
    return {
        "schema_version": 1,
        "readonly": True,
        "image_generation_called": False,
        "attempt_authority_mutated": False,
        "unresolved_frames": [r["frame"] for r in rows],
        "items": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    args = parser.parse_args()
    ep = Path(args.episode)
    if not ep.is_absolute():
        ep = ROOT / ep
    print(json.dumps(inspect(ep), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
