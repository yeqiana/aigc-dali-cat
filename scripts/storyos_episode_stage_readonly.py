#!/usr/bin/env python3
"""Read only the canonical Episode stage for native full-auto admission.

The `CODEX_MANAGED` runner needs an explicit stage check. A healthy Codex
bridge and zero active Generation Attempts must not turn an already
PUBLISH_READY Episode into an invitation to re-run paid models.
No JSON fallback, writes, model calls or credential output.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import episode_state_persistence
from story_os_contract import canonical_stages


def inspect(raw: str, *, root: Path = ROOT, state_loader=None) -> dict:
    root = Path(root).resolve()
    episode = Path(raw)
    episode = (episode if episode.is_absolute() else root / episode).resolve()
    if not episode.is_dir() or not episode.is_relative_to(root / "episodes"):
        return {"status": "BLOCKED", "reason": "EPISODE_PATH_INVALID",
                "read_only": True, "sql_writes": 0, "model_calls": 0}
    loader = state_loader or episode_state_persistence.load_with_source
    try:
        row, source = loader(episode)
    except Exception:
        return {"status": "BLOCKED", "reason": "STAGE_AUTHORITY_READ_FAILED",
                "read_only": True, "sql_writes": 0, "model_calls": 0}
    if source != "mysql" or not isinstance(row, dict):
        reason = "STAGE_MYSQL_AUTHORITY_NOT_VERIFIED"
        status = "BLOCKED"
        stage = None
        disposition = None
    else:
        stage = str(row.get("current_state") or "")
        disposition = str(row.get("disposition") or "ACTIVE").upper()
        reason = None
        if disposition != "ACTIVE":
            status, reason = "BLOCKED", "EPISODE_DISPOSITION_NOT_ACTIVE"
        elif stage in {"PUBLISH_READY", "PUBLISHED", "DATA_REVIEWED"}:
            # All stages at or beyond publish readiness are completed work.
            # Full-auto creation/resume must never regenerate them.
            status = "ALREADY_PUBLISH_READY"
        elif stage not in canonical_stages():
            status, reason = "BLOCKED", "UNKNOWN_EPISODE_STAGE"
        else:
            status = "STAGE_ELIGIBLE"
    return {
        "status": status,
        "reason": reason,
        "stage": stage,
        "disposition": disposition,
        "source": source,
        "read_only": True, "sql_writes": 0, "model_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    args = parser.parse_args()
    result = inspect(args.episode)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "STAGE_ELIGIBLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
