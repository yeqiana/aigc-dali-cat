"""In-memory Runtime Node Contract scheduler.

It plans dependency release and worker slots only.  Execution, persistence,
evidence generation and every Gate decision remain with existing Runtime code.
"""
from __future__ import annotations

import json
from pathlib import Path

import runtime_dag
import runtime_resource_manager
import task_priority

NODE_TYPES = {
    "concept", "story", "character", "environment", "frame_contract",
    "image_generation", "review", "repair", "release",
}


def load_node_contract(source) -> list[dict]:
    """Load a Node Contract from a dict/list or a JSON file; no files are written."""
    if isinstance(source, (str, Path)):
        source = json.loads(Path(source).read_text(encoding="utf-8"))
    rows = runtime_dag.normalize_node_contracts(source)
    for row in rows:
        if str(row.get("node_type") or "") not in NODE_TYPES:
            raise ValueError("unsupported node_type for " + row["node_id"])
        task_priority.normalize(row.get("priority"))
        row["priority_score"] = task_priority.priority_score(row.get("priority"), row.get("priority_score"))
        for field in ("input_contract", "output_contract", "retry_policy"):
            if field in row and not isinstance(row[field], dict):
                raise ValueError(f"node {row['node_id']} {field} must be an object")
        if "evidence_required" in row and not isinstance(row["evidence_required"], list):
            raise ValueError(f"node {row['node_id']} evidence_required must be a list")
    return rows


def schedule(source, *, completed=(), failed=(), max_workers: int = 1, resource_snapshot=None) -> dict:
    """Plan one dispatch wave; no node is executed and no state is persisted."""
    if isinstance(max_workers, bool) or int(max_workers) < 1:
        raise ValueError("max_workers must be at least 1")
    workers = int(max_workers)
    rows = load_node_contract(source)
    resolved = runtime_dag.resolve_node_dependencies(rows, completed=completed, failed=failed)
    ready = task_priority.stable_sort(resolved["ready"])
    resources = runtime_resource_manager.normalize(resource_snapshot, max_workers=workers)
    allocation = runtime_resource_manager.allocate(ready, resources)
    return {
        "schema_version": 1,
        "max_workers": resources["max_workers"],
        "dispatch": allocation["dispatch"],
        "queued": allocation["queued"],
        "waiting": resolved["waiting"],
        "blocked": resolved["blocked"],
        "authority": {
            "episode_state_mutated": False,
            "gate_decision": False,
            "evidence_generated": False,
            "note": "scheduling plan only; node completion is not Gate PASS",
        },
        "resources": allocation["resources"],
    }
