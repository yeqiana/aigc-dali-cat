#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only Final Candidate Snapshot drift diagnostic."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import final_candidate_snapshot as fcs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_dir")
    args = ap.parse_args()

    ep = Path(args.episode_dir).resolve()
    snap_path = ep / fcs.SNAPSHOT_REL
    if not snap_path.is_file():
        print("SNAPSHOT MISSING:", snap_path)
        return 2

    saved = fcs.read_json(snap_path)
    saved_lock = saved.get("lock") or {}
    current = fcs.build_lock(ep, write_evidence=False)

    saved_rows = {
        row["path"]: row
        for row in (saved_lock.get("delivery_files") or [])
        if isinstance(row, dict) and row.get("path")
    }
    current_rows = {
        row["path"]: row
        for row in (current.get("delivery_files") or [])
        if isinstance(row, dict) and row.get("path")
    }

    drifts = []
    for path in sorted(set(saved_rows) | set(current_rows)):
        old = saved_rows.get(path)
        new = current_rows.get(path)
        if old is None:
            drifts.append({
                "path": path,
                "kind": "NEW_IN_CURRENT",
                "saved_sha": None,
                "current_sha": new.get("sha256"),
            })
        elif new is None:
            drifts.append({
                "path": path,
                "kind": "MISSING_IN_CURRENT",
                "saved_sha": old.get("sha256"),
                "current_sha": None,
            })
        elif str(old.get("sha256")) != str(new.get("sha256")):
            drifts.append({
                "path": path,
                "kind": "SHA_DRIFT",
                "saved_sha": old.get("sha256"),
                "current_sha": new.get("sha256"),
            })

    current_sha = fcs.sha256_json(current)
    result = {
        "saved_snapshot_sha256": saved.get("snapshot_sha256"),
        "current_snapshot_sha256": current_sha,
        "snapshot_sha_matches": str(saved.get("snapshot_sha256")) == current_sha,
        "story_gates_contract_sha_matches": (
            saved_lock.get("story_gates_contract_sha256")
            == current.get("story_gates_contract_sha256")
        ),
        "publication_sha_matches": (
            saved_lock.get("publication_sha256")
            == current.get("publication_sha256")
        ),
        "file_drift_count": len(drifts),
        "file_drifts": drifts,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["snapshot_sha_matches"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
