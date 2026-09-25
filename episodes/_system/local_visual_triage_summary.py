#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aggregate Local Visual Triage evidence for production KPI measurement."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import story_json

REL_ROOT = Path("meta/runtime/diagnostics/local-visual-triage")
REL = Path("meta/runtime/diagnostics/local-visual-triage-summary.json")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def collect(ep: Path, *, write: bool = True) -> dict:
    ep = Path(ep).resolve()
    rows = []
    root = ep / REL_ROOT
    if root.is_dir():
        for path in sorted(root.glob("*.json")):
            data = story_json.read_json(path, default={})
            if isinstance(data, dict) and data.get("queue_item_id"):
                rows.append(data)
    statuses = {}
    issue_counts = {}
    provider_status_counts = {}
    duplicate_count = 0
    near_duplicate_count = 0
    repair_noop_count = 0
    elapsed = 0.0
    for row in rows:
        status = str(row.get("status") or "UNKNOWN")
        statuses[status] = statuses.get(status, 0) + 1
        elapsed += float(row.get("elapsed_seconds") or 0.0)
        provider_rows = {
            "embedding": row.get("embedding"),
            "sface_shadow": row.get("sface_shadow"),
            "object_presence": row.get("object_presence"),
            "pose_diagnostic": row.get("pose_diagnostic"),
            "sam2_mask": (row.get("repair_integrity") or {}).get("sam2_mask"),
            "lpips": (row.get("repair_integrity") or {}).get("lpips"),
        }
        for provider_name, provider_row in provider_rows.items():
            if not isinstance(provider_row, dict):
                continue
            provider_status = str(provider_row.get("status") or "UNKNOWN")
            bucket = provider_status_counts.setdefault(provider_name, {})
            bucket[provider_status] = bucket.get(provider_status, 0) + 1
        for issue in row.get("issue_codes") or []:
            key = str(issue)
            issue_counts[key] = issue_counts.get(key, 0) + 1
        for dup in row.get("duplicates") or []:
            duplicate_count += 1
            if dup.get("kind") == "NEAR_DUPLICATE":
                near_duplicate_count += 1
        issues = set((row.get("repair_integrity") or {}).get("issues") or [])
        if issues & {"REPAIR_EXACT_NOOP", "REPAIR_NEAR_NOOP"}:
            repair_noop_count += 1
    result = {
        "schema_version": 1,
        "generated_at": now(),
        "derived_evidence": True,
        "report_count": len(rows),
        "status_counts": statuses,
        "issue_counts": issue_counts,
        "provider_status_counts": provider_status_counts,
        "duplicate_evidence_count": duplicate_count,
        "near_duplicate_evidence_count": near_duplicate_count,
        "repair_noop_count": repair_noop_count,
        "local_triage_elapsed_seconds": round(elapsed, 4),
    }
    if write:
        target = ep / REL
        target.parent.mkdir(parents=True, exist_ok=True)
        story_json.write_json(target, result)
    return result
