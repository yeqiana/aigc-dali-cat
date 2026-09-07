#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B3 anti-regression scan: private JSON I/O helpers must delegate to story_json.

Story OS B3 converges the _system JSON persistence onto episodes/_system/story_json.py.
Any new module-level private helper in the JSON read/write family must forward to
story_json (same-line or block body). Explicit whitelist entries below document the
intentional exceptions: canonical base modules, findings-parameterized evidence
loaders, cache wrapper reads, and helpers whose loud-failure channel (SystemExit or
ProductReviewError) is an existing CLI/exception contract.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"

HELPER_NAMES = {
    "read_json",
    "write_json",
    "load_json",
    "save_json",
    "_read_json",
    "_write_json",
    "_load_json",
}

# (module, function) -> reason the helper may keep its own body.
WHITELIST = {
    ("story_json.py", "read_json"): "canonical JSON reader base module",
    ("story_json.py", "write_json"): "canonical JSON writer base module",
    ("runtime_atomic_store.py", "read_json"): "atomic lenient read base used by story_json",
    ("production_ledger_core.py", "load_json"): "SystemExit loud-evidence contract",
    ("production_ledger_core.py", "save_json"): "already delegates to atomic_write_json (same atomic path)",
    ("machine_gate.py", "load_json"): "findings-parameterized evidence loader",
    ("validate_episode.py", "load_json"): "findings-parameterized evidence loader",
    ("intro_policy.py", "read_json"): "cache wrapper read; write side delegates to story_json",
    ("resource_library.py", "read_json"): "cache wrapper read; write side delegates to story_json",
    ("capture_grammar_v226.py", "load_json"): "SystemExit contract",
    ("capture_grammar_v228.py", "load_json"): "SystemExit contract",
    ("evidence_tool.py", "load_json"): "SystemExit contract",
    ("approval_lock.py", "load_json"): "SystemExit contract",
    ("calibration_sheet.py", "load_json"): "SystemExit contract",
    ("release_package.py", "load_json"): "SystemExit contract",
    ("visual_profile.py", "load_json"): "SystemExit contract",
    ("delegated_approval.py", "read_json"): "SystemExit contract",
    ("delegated_delivery.py", "read_json"): "SystemExit contract",
    ("text_revision.py", "load_json"): "SystemExit contract",
    ("transport_guard.py", "load_json"): "SystemExit contract",
    ("product_review_adapter.py", "_read_json"): "ProductReviewError contract",
}


def _module_helpers(module_path: Path):
    tree = ast.parse(module_path.read_text(encoding="utf-8-sig"))
    lines = module_path.read_text(encoding="utf-8-sig").splitlines()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name not in HELPER_NAMES:
            continue
        span = lines[node.lineno - 1:node.end_lineno]
        yield node.name, "\n".join(span)


class JsonIoDelegationScanTests(unittest.TestCase):
    def test_all_private_json_helpers_delegate_or_are_whitelisted(self):
        violations = []
        scanned = 0
        for py in sorted(SYSTEM.glob("*.py")):
            for name, span in _module_helpers(py):
                scanned += 1
                if "story_json." in span:
                    continue
                key = (py.name, name)
                if key in WHITELIST:
                    continue
                violations.append(f"{py.name}:{name} keeps a private JSON implementation")
        self.assertEqual(violations, [], "\n".join(violations))
        # Sanity: the scan must actually see the canonical module helpers.
        self.assertGreaterEqual(scanned, 120)

    def test_whitelisted_entries_still_exist(self):
        missing = []
        for module, name in WHITELIST:
            py = SYSTEM / module
            if not py.is_file():
                missing.append(f"{module} missing")
                continue
            present = any(n == name for n, _ in _module_helpers(py))
            if not present:
                missing.append(f"{module}:{name} no longer exists")
        self.assertEqual(missing, [], "\n".join(missing))

    def test_every_remaining_migration_group_covered(self):
        # G1..G5b migrated modules must appear as delegating helpers, proving the
        # scan covers the full set (guards against a too-narrow module glob).
        migrated_modules = {
            "account_learning_index.py",
            "approval_lock.py",
            "calibration_sheet.py",
            "contract_sync.py",
            "delegated_approval.py",
            "delegated_delivery.py",
            "evidence_gate.py",
            "evidence_tool.py",
            "final_acceptance.py",
            "product_review_adapter.py",
            "product_runtime_adapter.py",
            "raw_candidate_budget.py",
            "release_package.py",
            "runtime_fault_replay_v211.py",
            "runtime_mode_router.py",
            "test_machine_gate.py",
            "test_stage_v224.py",
            "test_stage_v227.py",
            "test_v2033_frame_semantic_enforcement.py",
            "test_v211_performance_regression.py",
            "test_v261_full_mock_pipeline.py",
            "test_validator.py",
            "text_revision.py",
            "transport_guard.py",
            "v18_gate.py",
            "validation_stage_v223.py",
            "visual_profile.py",
        }
        seen = set()
        for py in SYSTEM.glob("*.py"):
            for name, span in _module_helpers(py):
                if py.name in migrated_modules and "story_json." in span:
                    seen.add(py.name)
        missing = sorted(migrated_modules - seen)
        self.assertEqual(missing, [], "\n".join(missing))


if __name__ == "__main__":
    unittest.main()
