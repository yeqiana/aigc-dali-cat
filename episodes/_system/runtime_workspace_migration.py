#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Safe planner/executor for copying mutable Episode runtime files to Runtime Workspace.

Planning is deliberately non-mutating and remains the CLI default.  An explicit
``--execute-copy`` performs copy -> checksum verify only for OPERATIONAL_STATE /
DERIVED_CACHE. Authority, formal evidence and content assets always remain under
the Episode boundary. Legacy sources are never deleted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path

import runtime_asset_policy
import runtime_workspace
import effective_config

MIGRATABLE = frozenset({runtime_asset_policy.OPERATIONAL_STATE, runtime_asset_policy.DERIVED_CACHE})
COPY_READY_EXACT = frozenset({
    effective_config.REL.as_posix(),
    "meta/runtime/next-action.json",
    "meta/runtime-checkpoint.json",
    "meta/runtime-dag-state.json",
    "meta/runtime-runner-state.json",
    "meta/runtime-resume-token.json",
})
COPY_READY_PREFIXES = (
    "meta/runtime/execution-capsules/",
    "meta/runtime/prompt-packages/",
    "meta/runtime/contracts/frames/",
)


def copy_ready(rel: str) -> bool:
    return rel in COPY_READY_EXACT or any(rel.startswith(prefix) for prefix in COPY_READY_PREFIXES)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_plan(ep: Path) -> dict:
    ep = Path(ep).resolve()
    rows: list[dict] = []
    counts: Counter[str] = Counter()
    for source in sorted((p for p in ep.rglob("*") if p.is_file()), key=lambda p: p.as_posix()):
        rel = source.relative_to(ep).as_posix()
        policy = runtime_asset_policy.classify(rel)
        counts[policy.category] += 1
        if policy.category in MIGRATABLE and copy_ready(rel):
            source_sha256 = sha256_file(source)
            rows.append({
                "path": rel,
                "category": policy.category,
                "action": "COPY_VERIFY_THEN_SWITCH_READ",
                "source": str(source),
                "target": str(runtime_workspace.workspace_path(ep, rel)),
                "source_sha256": source_sha256,
                "source_size": source.stat().st_size,
                "delete_source": False,
            })
        elif policy.category in MIGRATABLE:
            rows.append({
                "path": rel,
                "category": policy.category,
                "action": "DEFER_CONSUMER_MIGRATION",
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
        if category in MIGRATABLE:
            expected = "COPY_VERIFY_THEN_SWITCH_READ" if copy_ready(str(row.get("path") or "")) else "DEFER_CONSUMER_MIGRATION"
            if action != expected:
                errors.append(f"MIGRATABLE_ASSET_ACTION_INVALID:{row.get('path')}")
        if row.get("delete_source") is not False:
            errors.append(f"SOURCE_DELETE_NOT_ALLOWED_IN_DRY_RUN:{row.get('path')}")
    return errors


def _preflight(ep: Path, plan: dict) -> tuple[list[dict], list[str]]:
    errors = list(validate_plan(plan))
    rows: list[dict] = []
    if str(Path(plan.get("episode") or "").resolve()) != str(ep):
        errors.append("PLAN_EPISODE_MISMATCH")
    for row in plan.get("items") or []:
        if row.get("action") != "COPY_VERIFY_THEN_SWITCH_READ":
            continue
        rel = str(row.get("path") or "")
        try:
            policy = runtime_asset_policy.classify(rel)
            source = runtime_workspace.legacy_path(ep, rel)
            target = runtime_workspace.workspace_path(ep, rel)
        except Exception as exc:
            errors.append(f"PATH_RESOLUTION_FAILED:{rel}:{type(exc).__name__}")
            continue
        if policy.category not in MIGRATABLE or policy.category != row.get("category"):
            errors.append(f"ASSET_POLICY_CHANGED:{rel}")
            continue
        if str(source) != str(row.get("source") or "") or str(target) != str(row.get("target") or ""):
            errors.append(f"PLAN_PATH_TAMPERED:{rel}")
            continue
        if not source.is_file():
            errors.append(f"SOURCE_MISSING:{rel}")
            continue
        source_sha = sha256_file(source)
        source_size = source.stat().st_size
        if source_sha != str(row.get("source_sha256") or "") or source_size != int(row.get("source_size") or -1):
            errors.append(f"SOURCE_CHANGED_SINCE_PLAN:{rel}")
            continue
        target_state = "COPY"
        if target.exists():
            if not target.is_file() or sha256_file(target) != source_sha:
                errors.append(f"TARGET_CONFLICT:{rel}")
                continue
            target_state = "REUSE"
        rows.append({"path": rel, "source": source, "target": target, "sha256": source_sha,
                     "size": source_size, "target_state": target_state})
    return rows, errors


def execute_copy(ep: Path, plan: dict) -> dict:
    """Explicit, resumable copy+verify. Never removes or rewrites a legacy source."""
    ep = Path(ep).resolve()
    rows, errors = _preflight(ep, plan)
    report = {
        "schema_version": 1,
        "mode": "COPY_VERIFY",
        "episode": str(ep),
        "status": "BLOCKED" if errors else "RUNNING",
        "copied": 0,
        "reused_verified": 0,
        "verified": 0,
        "bytes_copied": 0,
        "deletes_performed": 0,
        "legacy_preserved": True,
        "errors": errors,
        "items": [],
    }
    # Fail closed before the first write when the plan is stale/tampered/conflicting.
    if errors:
        return report
    for row in rows:
        target: Path = row["target"]
        source: Path = row["source"]
        state = row["target_state"]
        if state == "COPY":
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, raw_tmp = tempfile.mkstemp(prefix=target.name + ".", suffix=".migration-tmp", dir=target.parent)
            tmp = Path(raw_tmp)
            try:
                with os.fdopen(fd, "wb") as out, source.open("rb") as src:
                    shutil.copyfileobj(src, out, length=1024 * 1024)
                    out.flush()
                    os.fsync(out.fileno())
                if sha256_file(tmp) != row["sha256"]:
                    raise RuntimeError(f"TEMP_CHECKSUM_MISMATCH:{row['path']}")
                if target.exists():
                    if not target.is_file() or sha256_file(target) != row["sha256"]:
                        raise RuntimeError(f"TARGET_RACE_CONFLICT:{row['path']}")
                    tmp.unlink()
                    state = "REUSE"
                else:
                    tmp.replace(target)
                    report["copied"] += 1
                    report["bytes_copied"] += int(row["size"])
            finally:
                if tmp.exists():
                    tmp.unlink()
        if sha256_file(target) != row["sha256"]:
            raise RuntimeError(f"TARGET_CHECKSUM_MISMATCH:{row['path']}")
        if runtime_workspace.resolve_read_path(ep, row["path"]) != target:
            raise RuntimeError(f"SWITCH_READ_NOT_EFFECTIVE:{row['path']}")
        if state == "REUSE":
            report["reused_verified"] += 1
        report["verified"] += 1
        report["items"].append({"path": row["path"], "status": "VERIFIED", "copy_result": state,
                                "sha256": row["sha256"], "legacy_preserved": source.is_file()})
    report["status"] = "PASS"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode_dir")
    parser.add_argument("--execute-copy", action="store_true",
                        help="explicitly copy+verify migratable files; legacy sources are preserved")
    args = parser.parse_args()
    ep = Path(args.episode_dir).resolve()
    plan = build_plan(ep)
    plan["validation_errors"] = validate_plan(plan)
    result = execute_copy(ep, plan) if args.execute_copy and not plan["validation_errors"] else plan
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if plan["validation_errors"]:
        return 2
    return 0 if not args.execute_copy or result.get("status") == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
