from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import p2_visual_narrative_paired_benchmark as benchmark
from agents import visual_narrative_prepare_model_producer as producer


class VisualNarrativePairedBenchmarkTest(unittest.TestCase):
    def _manifest(self):
        return {
            "episode": "episodes/fixture",
            "snapshot_id": "snapshot-fixed",
            "provider": producer.DEFAULT_PROVIDER,
            "model": producer.DEFAULT_MODEL,
            "reasoning_effort": producer.REASONING_EFFORT,
            "authority_scope": list(producer.VISUAL_SCOPE_ORDER),
        }

    def _row(self, index, *, legacy_wall=100.0, agent_wall=88.0, legacy_tokens=1000, agent_tokens=1000):
        checks = {
            "candidate_valid": True, "telemetry_complete": True, "semantic_equivalent": True,
            "fixed_provider_model_reasoning": True, "no_failure_timeout": True,
            "authority_zero_regression": True,
        }
        return {
            "pair_index": index, "valid": True, "checks": checks,
            "quality": {"legacy_quality_errors": 0, "agent_quality_errors": 0},
            "legacy": {"wall_seconds": legacy_wall, "total_tokens": legacy_tokens},
            "agent": {"wall_seconds": agent_wall, "total_tokens": agent_tokens},
        }

    def test_five_valid_pairs_use_medians_and_report_value_separately_from_safety(self):
        rows = [self._row(i) for i in range(1, 6)]
        report = benchmark.summarize(self._manifest(), rows)
        self.assertTrue(report["safety_pass"])
        self.assertTrue(report["measurable_value"])
        self.assertEqual(report["performance"]["median_legacy_wall_seconds"], 100.0)
        self.assertEqual(report["performance"]["median_agent_wall_seconds"], 88.0)
        self.assertNotIn("p90", report["performance"])
        self.assertEqual(report["production_decision"], "CONDITIONAL_REVIEW")
        self.assertFalse(report["production_cutover_performed"])

    def test_four_pairs_cannot_pass_minimum_safety_gate(self):
        report = benchmark.summarize(self._manifest(), [self._row(i) for i in range(1, 5)])
        self.assertFalse(report["safety_pass"])
        self.assertFalse(report["safety_checks"]["minimum_valid_pairs"])

    def test_token_regression_can_fail_safety_without_becoming_value(self):
        report = benchmark.summarize(self._manifest(), [
            self._row(i, agent_wall=100, legacy_tokens=1000, agent_tokens=1110) for i in range(1, 6)
        ])
        self.assertFalse(report["safety_pass"])
        self.assertFalse(report["value_checks"]["token_reduction_ge_20pct"])


if __name__ == "__main__":
    unittest.main()
