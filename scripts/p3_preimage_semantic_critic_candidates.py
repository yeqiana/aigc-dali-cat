#!/usr/bin/env python3
"""Read-only scan for existing, SHA-valid PREIMAGE candidate sets."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
sys.path.insert(0, str(SYSTEM))


def scan() -> dict:
    from phase9_runtime_launcher import load_runtime_env_file
    env, _source = load_runtime_env_file(ROOT / ".storyos/runtime-launcher/runtime.env", dict(os.environ))
    os.environ.update(env)
    from preimage_authority_snapshot import REL as SNAPSHOT_REL, stale_owned
    import preimage_task_contract as contract
    import story_json

    rows = []
    excluded = {".git", ".pytest_cache", "__pycache__", ".storyos_cache", "node_modules"}
    for meta in ROOT.glob("episodes/**/meta/runtime/preimage-authority-snapshot.json"):
        if any(part in excluded for part in meta.parts):
            continue
        episode = meta.parents[2]
        try:
            snapshot = story_json.read_json(meta, default={}) or {}
            episode_state_path = episode / "meta/episode-state.json"
            episode_state = story_json.read_json(episode_state_path, default={}) or {}
            tasks = contract.plan_tasks(episode, snapshot, resume=True)
            checks = []
            for task in tasks:
                candidate = contract.read_candidate(episode, task)
                errors = contract.verify_candidate(candidate or {}, task)
                checks.append({
                    "task_type": task["task_type"],
                    "task_id": task["task_id"],
                    "candidate_path": task["candidate_output"],
                    "candidate_present": candidate is not None,
                    "candidate_sha256": contract.sha(contract.candidate_path(episode, task["task_type"])),
                    "candidate_valid": not errors,
                    "candidate_errors": errors,
                    "task_status": task.get("status"),
                })
            stale = stale_owned(episode, snapshot)
            eligible = bool(tasks) and not stale and all(x["candidate_valid"] and x["task_status"] == "REUSED" for x in checks)
            rows.append({
                "episode": episode.relative_to(ROOT).as_posix(),
                "episode_state": episode_state.get("current_state"),
                "snapshot_id": snapshot.get("snapshot_id"),
                "snapshot_stale": stale,
                "candidate_set_complete": all(x["candidate_present"] for x in checks),
                "existing_semantic_result": "ALL_CANONICAL_TASK_VERIFIERS_PASS" if eligible else "NOT_ELIGIBLE",
                "tasks": checks,
                "eligible_read_only_smoke": eligible,
            })
        except Exception as exc:
            rows.append({"episode": meta.parents[2].relative_to(ROOT).as_posix(), "eligible_read_only_smoke": False,
                         "scan_error": f"{type(exc).__name__}: {exc}"})
    rows.sort(key=lambda item: item["episode"])
    return {
        "schema_version": 1,
        "kind": "p3_preimage_semantic_critic_real_smoke_candidates",
        "read_only": True,
        "runtime_env_loaded": bool(os.environ.get("STORYOS_MYSQL_HOST") or os.environ.get("STORYOS_DB_HOST")),
        "candidate_count": len(rows),
        "eligible_count": sum(bool(row.get("eligible_read_only_smoke")) for row in rows),
        "episodes": rows,
        "canonical_files_modified": False,
        "authority_write": False,
        "episode_transition": False,
        "image_generation_invoked": False,
    }


def main() -> int:
    report = scan()
    output = ROOT / "reports/p3-preimage-semantic-critic-real-smoke-candidates-20260928.json"
    encoded = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if output.exists():
        existing = output.read_text(encoding="utf-8-sig")
        if existing != encoded:
            print(f"refusing to overwrite candidate scan evidence: {output}", file=sys.stderr)
            return 2
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
    print(json.dumps({"report": output.relative_to(ROOT).as_posix(), "eligible_count": report["eligible_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
