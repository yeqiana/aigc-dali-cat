#!/usr/bin/env python3
"""Read-only static import graph for StoryOS's existing runtime nucleus.

Direct Python imports are evidence of module coupling, NOT a dynamic call trace,
runtime cost measurement, a dispatch owner, or proof that a module is removable.
"""
from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
NUCLEUS = (
    "runtime_driver", "runtime_dag", "runtime_scheduler",
    "runtime_node_execution", "runtime_node_registry",
    "runtime_router", "runtime_mode_router", "capability_router",
    "codex_critic_runner", "image_generation_gateway",
    "runtime_checkpoint", "runtime_trace", "runtime_observability",
    "episode_state_persistence", "runtime_ownership",
    "product_runtime_adapter", "runtime_failure_strategy",
)


def direct_imports(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def eager_imports(source: str) -> set[str]:
    """Imports that execute at module load, excluding deferred function imports."""
    tree = ast.parse(source)
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def collect(system: Path, nucleus: tuple[str, ...] = NUCLEUS) -> dict:
    names = tuple(sorted(set(nucleus)))
    observed = {name for name in names if (system / f"{name}.py").is_file()}
    edges: list[dict[str, str]] = []
    eager_edges: list[dict[str, str]] = []
    parse_errors: dict[str, str] = {}
    for name in sorted(observed):
        try:
            source = (system / f"{name}.py").read_text(encoding="utf-8-sig")
            imported = direct_imports(source)
            eager = eager_imports(source)
        except (OSError, SyntaxError, UnicodeError) as exc:
            parse_errors[name] = type(exc).__name__
            continue
        edges.extend({"from": name, "to": target}
                     for target in sorted(imported & observed) if target != name)
        eager_edges.extend({"from": name, "to": target}
                           for target in sorted(eager & observed) if target != name)
    fan_in = Counter(edge["to"] for edge in edges)
    fan_out = Counter(edge["from"] for edge in edges)
    return {
        "schema_version": 1,
        "analysis_kind": "static_import_graph_only",
        "diagnostic_only": True,
        "runtime_invocations_measured": False,
        "modules": sorted(observed),
        "missing_modules": sorted(set(names) - observed),
        "edges": edges,
        "eager_edges": eager_edges,
        "deferred_edges": [edge for edge in edges if edge not in eager_edges],
        "fan_in": dict(sorted(fan_in.items())),
        "fan_out": dict(sorted(fan_out.items())),
        "parse_errors": parse_errors,
        "limitations": [
            "dynamic imports and lazy imports may not appear",
            "imports do not imply execution, duplicate authority, or runtime latency",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = collect(SYSTEM)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if report["parse_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
