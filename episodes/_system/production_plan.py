#!/usr/bin/env python3
"""Create a non-executing Runtime production plan for an Episode."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import runtime_node_registry
import runtime_resource_manager
import runtime_scheduler

REL = Path("meta/runtime/production-plan.json")

def build(episode: Path, *, max_workers: int = 2) -> dict:
    """Return a topology/slot estimate only. No node, Gate, or state is executed."""
    nodes = runtime_node_registry.first_batch_nodes()
    completed, waves = set(), []
    while len(completed) < len(nodes):
        result = runtime_scheduler.schedule(nodes, completed=completed, max_workers=max_workers,
            resource_snapshot={"max_workers": max_workers, "runtime_capacity": {"text": max_workers, "image": 1}})
        dispatch = result["dispatch"]
        if not dispatch:
            break
        waves.append([item["node_id"] for item in dispatch])
        completed.update(item["node_id"] for item in dispatch)
    return {"schema_version": 1, "episode": str(Path(episode)), "dry_run": True,
            "node_count": len(nodes), "nodes": nodes, "estimated_waves": waves,
            "estimated_parallelism": {"max_workers": max_workers, "image_workers": 1,
                "parallel_preparation": ["character_prepare", "environment_prepare"]},
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
