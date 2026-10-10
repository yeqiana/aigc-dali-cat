#!/usr/bin/env python3
"""Read-only import-site inventory for routing, scheduling, gateway and adapters.

A static consumer is not proof of runtime invocation or safe deletion. The
production Scheduler/Generation Gateway remain the sole existing authorities.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"

ROLES = {
    "runtime_scheduler": "critic_dispatch_authorization",
    "capability_router": "advisory_capability_proposal",
    "runtime_router": "execution_runtime_detection",
    "runtime_mode_router": "workflow_mode_routing",
    "request_router": "user_intent_routing",
    "image_provider_router": "image_provider_selection",
    "image_generation_gateway": "generation_attempt_gateway",
    "product_runtime_adapter": "host_runtime_bridge",
    "product_review_adapter": "host_review_bridge",
}
# Use real Python import syntax; exclude comments, strings and docstrings.


def imported_modules(source: str) -> set[str]:
    tree = ast.parse(source)
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split(".")[0])
    return found


def inventory(system: Path, roles: dict[str, str] = ROLES) -> dict:
    consumers: dict[str, list[str]] = {key: [] for key in roles}
    parse_errors: dict[str, str] = {}
    for path in sorted(system.rglob("*.py")):
        if path.name.startswith("test_") or "_tests" in path.parts:
            continue
        relative = path.relative_to(system).as_posix()
        try:
            imported = imported_modules(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, SyntaxError) as exc:
            parse_errors[relative] = type(exc).__name__
            continue
        for module in imported & roles.keys():
            if relative != module + ".py":
                consumers[module].append(relative)
    rows = [
        {"module": module, "role": role,
         "defined": (system / (module + ".py")).is_file(),
         "static_consumer_count": len(consumers[module]),
         "static_consumers": sorted(consumers[module])}
        for module, role in sorted(roles.items())
    ]
    return {
        "schema_version": 1, "diagnostic_only": True,
        "dispatch_authority_unchanged": True,
        "absence_of_static_consumers_proves_unused": False,
        "modules": rows, "parse_errors": parse_errors,
        "limitations": [
            "dynamic imports and subprocess invocation are not counted",
            "shared consumer does not establish duplicate routing decisions",
            "do not retire adapters or gates without end-to-end review",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.parse_args()
    report = inventory(SYSTEM)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2 if report["parse_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
