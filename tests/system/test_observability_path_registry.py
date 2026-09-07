#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B6 anti-regression scan: S2.6 observability paths must live in one registry.

runtime_observability.py is the single registration point for the runtime
performance/observability documents and the trace channel. Production code
outside the registry module must reference the constants instead of re-embedding
meta/... literal paths. Intentional exceptions:
- gitignore/strategy glob patterns ("episodes/**/...") in contract_sync.py and
  runtime_log_policy.py are policy strings, not direct file paths;
- episodes/_system/test_*.py fixtures build temporary episode documents by
  literal path, which is test isolation and does not add a production writer;
- runtime_observability.py itself is the registration point.
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"

PATH_LITERALS = (
    "meta/episode-performance-ledger.json",
    "meta/workflow-performance.json",
    "meta/workflow-observability.json",
    "meta/image-scheduler-performance.json",
    "meta/batch-runtime-performance.json",
    "meta/quota-observability.json",
    "meta/runtime/trace-events.jsonl",
)

EXPECTED_CONSUMERS = {
    "episode_performance.py",
    "critic_runtime_v211.py",
    "performance_guard_v211.py",
    "workflow_performance.py",
    "workflow_observability.py",
    "batch_runtime_metrics.py",
    "batch_scheduler.py",
    "final_candidate_snapshot.py",
    "quota_observability.py",
    "runtime_daemon_event_bridge.py",
    "runtime_fast_path.py",
}


def _is_test_fixture(py):
    return py.name.startswith("test_")


def _is_policy_glob(line):
    return "episodes/**/" in line


class ObservabilityPathRegistryTests(unittest.TestCase):
    def test_path_literals_only_in_registry_or_documented_exceptions(self):
        violations = []
        for py in sorted(SYSTEM.glob("*.py")):
            if py.name == "runtime_observability.py":
                continue
            if _is_test_fixture(py):
                continue
            for lineno, line in enumerate(py.read_text(encoding="utf-8-sig").splitlines(), 1):
                if _is_policy_glob(line):
                    continue
                for literal in PATH_LITERALS:
                    if literal in line:
                        violations.append(f"{py.name}:{lineno}: {literal}")
        self.assertEqual(violations, [], "\n".join(violations))

    def test_registry_consumers_import_the_registry(self):
        missing = []
        for py in sorted(SYSTEM.glob("*.py")):
            if py.name not in EXPECTED_CONSUMERS:
                continue
            src = py.read_text(encoding="utf-8-sig")
            if "import runtime_observability" not in src and \
                    "from runtime_observability import" not in src:
                missing.append(f"{py.name} does not reference runtime_observability")
        self.assertEqual(missing, [], "\n".join(missing))

    def test_registry_exposes_all_known_paths(self):
        import sys

        sys.path.insert(0, str(SYSTEM))
        import runtime_observability

        known = {p.as_posix() for p in runtime_observability.KNOWN_PATHS.values()}
        known.add(runtime_observability.TRACE_EVENTS_REL.as_posix())
        self.assertEqual(known, set(PATH_LITERALS))


if __name__ == "__main__":
    unittest.main()
