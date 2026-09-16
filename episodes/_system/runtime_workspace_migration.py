#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dry-run planner for moving mutable Episode runtime files to Runtime Workspace.

The planner is deliberately non-mutating. It classifies current Episode files and
proposes targets for OPERATIONAL_STATE / DERIVED_CACHE only. Authority, formal
evidence and content assets always remain under the Episode boundary.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import runtime_asset_policy
import runtime_workspace

MIGRATABLE = frozenset({runtime_asset_policy.OPERATIONAL_STATE, runtime_asset_policy.DERIVED_CACHE})


def build_plan(ep: Path) -> dict:
    ep = Path(ep).resolve()
    rows: list[dict] = []
    counts: Counter[str] = Counter()
    for source in sorted((p for p in ep.rglob("*") if p.is_file()), key=lambda p: p.as_posix()):
        rel = source.relative_to(ep).as_posix()
        policy = runtime_asset_policy.classify(rel)
        counts[policy.category] += 1
        if policy.category in MIGRATABLE:
            rows.append({
                "path": rel,
                "category": policy.category,
                "action": "COPY_VERIFY_THEN_SWITCH_READ",
                "source": str(source),
                "target": str(runtime_workspace.workspace_path(ep, rel)),
                "delete_source": False,
            })
        else:
            rows.append({
                "path": rel,
                "category": policy.category,
                "action": "KEEP_EPISODE",
                "source": str(source),
                "target": None,
                "delete_source": False,
            })
    return {
        "schema_version": 1,
        "mode": "DRY_RUN_ONLY",
        "episode": str(ep),
        "runtime_root": str(runtime_workspace.runtime_root()),
        "counts": dict(sorted(counts.items())),
        "items": rows,
        "safety": {
            "moves_performed": 0,
            "deletes_performed": 0,
            "formal_evidence_must_remain_episode": True,
            "authority_must_remain_episode": True,
        },
    }


def validate_plan(plan: dict) -> list[str]:
    errors: list[str] = []
    for row in plan.get("items") or []:
        category = row.get("category")
        action = row.get("action")
        if category in {runtime_asset_policy.AUTHORITY, runtime_asset_policy.FORMAL_EVIDENCE, runtime_asset_policy.CONTENT_ASSET}:
            if action != "KEEP_EPISODE" or row.get("target") is not None:
                errors.append(f"PROTECTED_ASSET_MIGRATION_PROPOSED:{row.get('path')}")
        if category in MIGRATABLE and action != "COPY_VERIFY_THEN_SWITCH_READ":
            errors.append(f"MIGRATABLE_ASSET_ACTION_INVALID:{row.get('path')}")
        if row.get("delete_source") is not False:
            errors.append(f"SOURCE_DELETE_NOT_ALLOWED_IN_DRY_RUN:{row.get('path')}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode_dir")
    args = parser.parse_args()
    plan = build_plan(Path(args.episode_dir))
    plan["validation_errors"] = validate_plan(plan)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0 if not plan["validation_errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
