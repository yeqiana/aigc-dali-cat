#!/usr/bin/env python3
"""Read-only inventory for P1/P2/P3 Agent shadow, P4 Router and P5 Guardian.

No Episode, Authority, Provider or runtime side effects: read config, classify
modes, and report candidates requiring an independent evidence-backed cutover.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

def _flags(value: object, label: str) -> tuple[bool, bool]:
    if not isinstance(value, dict):
        raise ValueError(f"{label}: missing configuration object")
    shadow = value.get("shadow_enabled")
    production = value.get("production_enabled")
    if type(shadow) is not bool or type(production) is not bool:
        raise ValueError(f"{label}: shadow_enabled/production_enabled must be boolean")
    return shadow, production


def inventory(config: dict) -> dict:
    runtime = config.get("agent_runtime") if isinstance(config, dict) else None
    if not isinstance(runtime, dict):
        raise ValueError("agent_runtime config missing")
    adapters = runtime.get("adapters")
    if not isinstance(adapters, dict):
        raise ValueError("agent_runtime.adapters config missing")
    sources = {f"adapter.{name}": value for name, value in sorted(adapters.items())}
    sources["task_capability_router"] = runtime.get("task_capability_router")
    sources["guardian_facade"] = runtime.get("guardian_facade")
    rows = []
    for label, value in sources.items():
        shadow, production = _flags(value, label)
        status = ("PRODUCTION_AND_SHADOW" if shadow and production else
                  "PRODUCTION_ONLY" if production else
                  "SHADOW_ONLY" if shadow else "DISABLED")
        rows.append({
            "component": label, "status": status,
            "shadow_enabled": shadow, "production_enabled": production,
            "requires_evidence_before_retirement": bool(shadow),
        })
    return {
        "schema_version": 1,
        "diagnostic_only": True,
        "writes_production_authority": False,
        "components": rows,
        "shadow_active_count": sum(x["shadow_enabled"] for x in rows),
        "production_active_count": sum(x["production_enabled"] for x in rows),
        "retirement_auto_authorized": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable inventory")
    args = parser.parse_args(argv)
    import storyos_config
    config = storyos_config.load_config()
    errors = storyos_config.validate(config)
    if errors:
        print(json.dumps({"status": "CONFIG_INVALID", "errors": errors}, ensure_ascii=False))
        return 2
    report = inventory(config)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
