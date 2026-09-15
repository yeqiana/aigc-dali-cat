#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import evidence_gate
import episode_runner
import runtime_evidence_contract as contract
import runtime_log_policy


class RuntimeEvidenceContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="runtime-evidence-")
        self.addCleanup(self.tmp.cleanup)
        self.ep = Path(self.tmp.name)
        (self.ep / "meta/runtime").mkdir(parents=True)

    def test_legacy_episode_without_marker_is_not_backfilled_or_failed(self):
        self.assertFalse(contract.required(self.ep))
        self.assertEqual(contract.verify(self.ep), [])
        self.assertFalse((self.ep / contract.REL).exists())

    def test_arm_declares_exact_four_sinks_without_claiming_gate_pass(self):
        row = contract.arm(self.ep)
        self.assertEqual(tuple(row["required_sinks"]), contract.REQUIRED_SINKS)
        self.assertIsNone(row["gate_pass"])
        self.assertFalse(row["historical_backfill_allowed"])
        errors = contract.verify(self.ep)
        self.assertEqual(len(errors), 4)
        self.assertTrue(all(x.startswith("RUNTIME_EVIDENCE_MISSING:") for x in errors))

    def test_all_real_sinks_are_required_and_validated(self):
        contract.arm(self.ep)
        (self.ep / "meta/episode-performance-ledger.json").write_text(
            json.dumps({"schema_version": 1, "runs": []}), encoding="utf-8")
        for rel in contract.REQUIRED_SINKS[1:]:
            path = self.ep / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"event": "proof"}) + "\n", encoding="utf-8")
        self.assertEqual(contract.verify(self.ep), [])

    def test_empty_or_broken_sink_fails_closed(self):
        contract.arm(self.ep)
        (self.ep / "meta/episode-performance-ledger.json").write_text("{}", encoding="utf-8")
        for rel in contract.REQUIRED_SINKS[1:]:
            path = self.ep / rel; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"event": "proof"}) + "\n", encoding="utf-8")
        broken = self.ep / "meta/runtime/node-execution.jsonl"
        broken.write_text("not-json\n", encoding="utf-8")
        self.assertIn(
            "RUNTIME_EVIDENCE_INVALID_JSONL:meta/runtime/node-execution.jsonl",
            contract.verify(self.ep))

    def test_resident_runner_arms_contract_before_dispatch(self):
        with mock.patch.object(episode_runner.effective_config, "write"), \
             mock.patch.object(episode_runner.next_action, "write", return_value={"action": "NOOP"}), \
             mock.patch.object(episode_runner, "local_host_action", return_value=None), \
             mock.patch.object(episode_runner.runtime_dag, "execute", return_value=0):
            self.assertEqual(episode_runner.execute_cycle(self.ep), 0)
        self.assertTrue(contract.required(self.ep))
        marker = json.loads((self.ep / contract.REL).read_text(encoding="utf-8"))
        self.assertEqual(tuple(marker["required_sinks"]), contract.REQUIRED_SINKS)

    def test_production_pass_evidence_gate_fails_closed_when_runtime_sinks_missing(self):
        (self.ep / "meta/episode-state.json").write_text(
            json.dumps({"tool_version": "2.6.1", "current_state": "STORYBOARD_LOCKED"}), encoding="utf-8")
        (self.ep / "meta/release-manifest.json").write_text(
            json.dumps({"tool_version": "2.6.1"}), encoding="utf-8")
        contract.arm(self.ep)
        with mock.patch.object(evidence_gate, "any_approval", return_value=(True, [], "test")), \
             mock.patch.object(evidence_gate, "story_review_required", return_value=False), \
             mock.patch.object(evidence_gate, "verify_recent5_evidence", return_value=[]):
            ok, messages = evidence_gate.run_gate(self.ep, "PRODUCTION_PASSED")
        self.assertFalse(ok)
        self.assertTrue(any(
            str(message).startswith("runtime_evidence: RUNTIME_EVIDENCE_MISSING:")
            for message in messages
        ), messages)

    def test_runtime_evidence_sinks_are_local_diagnostics_not_git_authority(self):
        for rel in (
            "episodes/**/meta/runtime/trace-events.jsonl",
            "episodes/**/meta/runtime/node-execution.jsonl",
            "episodes/**/meta/runtime/authority-commit.jsonl",
            "episodes/**/meta/episode-performance-ledger.json",
        ):
            self.assertIn(rel, runtime_log_policy.LOCAL_ONLY_PATTERNS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
