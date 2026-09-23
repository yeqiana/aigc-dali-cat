#!/usr/bin/env python3
"""Create a non-executing Runtime production plan for an Episode."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import runtime_node_registry
import runtime_resource_manager
import runtime_scheduler
import storyos_config

REL = Path("meta/runtime/production-plan.json")

def build(episode: Path, *, max_workers: int = 2) -> dict:
    """Return a diagnostic topology estimate only; never a production scheduler input."""
    nodes = runtime_node_registry.first_batch_nodes()
    config=storyos_config.load_config()
    image_limit = int(storyos_config.get_path(config, "production.max_inflight_images", 5))
    # Logical topology estimate only. `authority` below maps to the explicit
    # local-Codex fallback pool; WORK+Workspace-Provider host concurrency is intentionally
    # not invented here. Review has no independent worker knob, and image work is
    # delegated to image_scheduler in production.
    pools={"authority":int(storyos_config.get_path(config,"runtime.workers.local_codex_preimage",4)),
           "derived":int(storyos_config.get_path(config,"runtime.workers.derived",6)),
           "image":image_limit}
    completed, waves = set(), []
    planning_workers=max(pools["authority"], pools["derived"])
    while len(completed) < len(nodes):
        result = runtime_scheduler.schedule(nodes, completed=completed, max_workers=planning_workers,
            resource_snapshot={"max_workers": planning_workers, "runtime_capacity": pools})
        dispatch = result["dispatch"]
        if not dispatch:
            break
        waves.append([item["node_id"] for item in dispatch])
        completed.update(item["node_id"] for item in dispatch)
    return {"schema_version": 1, "episode": str(Path(episode)), "dry_run": True,
            "production_consumer": False, "purpose": "diagnostic_topology_estimate",
            "node_count": len(nodes), "nodes": nodes,
            "dependency_graph": {node["node_id"]: node["depends_on"] for node in nodes},
            "parallel_groups": waves, "estimated_waves": waves,
            "serial_groups": [[node["node_id"]] for node in nodes if not (node.get("execution_policy") or {}).get("parallel_safe")],
            "authority_barriers": ["PREIMAGE_AUTHORITY_READY", "frame-contract-index single writer"],
            "preimage_host_protocol": {"kind": "PREIMAGE_TASK_SET", "tasks": ["CHARACTER_FINALIZE", "ENVIRONMENT_PREPARE", "WORLD_PREPARE", "VISUAL_NARRATIVE_PREPARE"], "commit": "single_transaction"},
            "configured_workers": pools,
            "safe_parallel_nodes": ["character_finalize", "environment_prepare", "world_prepare", "visual_narrative_prepare", "frame_contract_compile:frames"],
            "observed": {"preimage_parallelism_peak": None, "derived_parallelism_peak": None,
                         "note": "dry-run contains no observed execution metrics"},
            "estimated_parallelism": {"max_workers": planning_workers, "image_workers": image_limit,
                "parallel_preparation": ["character_finalize", "environment_prepare", "world_prepare", "visual_narrative_prepare"], "safe_preimage_parallelism": "PREIMAGE_TASK_SET candidate protocol"},
            "estimated_workers": {"max_workers": max_workers, "image_workers": image_limit},
            "risk_nodes": ["image_generation", "repair", "release"],
            "estimated_risks": ["image_generation remains governed by the existing image scheduler",
                                "repair/release require existing evidence and Gate decisions"],
            "authority": {"episode_state_mutated": False, "gate_decision": False, "node_executed": False}}

def write(episode: Path, **kwargs) -> Path:
    path = Path(episode) / REL; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build(episode, **kwargs), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode_dir"); parser.add_argument("--max-workers", type=int, default=2)
    parser.add_argument("--write", action="store_true", help="explicitly write meta/runtime/production-plan.json")
    args = parser.parse_args(); episode = Path(args.episode_dir)
    result = build(episode, max_workers=args.max_workers)
    if args.write: write(episode, max_workers=args.max_workers)
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main())
