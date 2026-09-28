"""P4 paired comparison, failure injection, performance, and Gate acceptance."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))

import p4_capability_router_validation as validation
from capability_router_gate import MANDATORY_CHECKS, evaluate_gate


class P4PreCutoverValidationTests(unittest.TestCase):
    def test_p4_paired_route_comparison(self):
        report = validation.paired_route_comparison()
        self.assertGreaterEqual(report["valid_pairs"], 12)
        self.assertEqual(report["unexplained_divergence_count"], 0)
        self.assertEqual(report["llm_calls"], 0)
        self.assertEqual(report["authority_writes"], 0)
        self.assertTrue(all(sample["request_sha256"] and sample["health_snapshot_sha256"]
                            and sample["capability_registry_sha256"] and sample["policy_sha256"]
                            and sample["config_sha256"] for sample in report["samples"]))

    def test_p4_story_divergence_has_explicit_classification(self):
        report = validation.paired_route_comparison()
        story = next(row for row in report["samples"] if row["sample_id"] == "story_critic_work_to_codex")
        self.assertEqual(story["divergence_type"], "LEGACY_ROUTE_UNDER_SPECIFIED")
        self.assertEqual(story["legacy_provider"], "WORK")
        self.assertEqual(story["proposed_provider"], "codex_user_runner")

    def test_p4_unexplained_divergence_blocks_gate(self):
        outcome = evaluate_gate({name: True for name in MANDATORY_CHECKS},
                                unexplained_divergence_count=1,
                                real_health_unknown_count=0, production_enabled=False)
        self.assertEqual(outcome["status"], "BLOCKED")
        self.assertFalse(outcome["ready_for_cutover_review"])

    def test_p4_429_sets_degraded_health(self):
        result = validation.failure_injection()
        self.assertTrue(result["429_degraded_pass"])
        for entry in result["technical_failures"].values():
            self.assertEqual(entry["status"], "DEGRADED")
            self.assertEqual(entry["ttl_seconds"], 300)
            self.assertEqual(entry["source"], "injected_execution_telemetry")

    def test_p4_success_recovers_health(self):
        result = validation.failure_injection()
        self.assertTrue(result["success_recovery_pass"])
        self.assertNotEqual(result["recovery"]["health_snapshot_sha_before"],
                            result["recovery"]["health_snapshot_sha_after"])

    def test_p4_health_ttl_expiry(self):
        self.assertTrue(validation.failure_injection()["ttl_expiry_pass"])

    def test_p4_unknown_health_behavior(self):
        audit = validation.real_health_audit()
        self.assertFalse(audit["llm_probe_used"])
        self.assertEqual(audit["provider_count"], 3)
        for row in audit["providers"]:
            if not row["fresh"]:
                self.assertEqual(row["status"], "UNKNOWN")

    def test_p4_unavailable_preferred_fallback(self):
        self.assertTrue(validation.failure_injection()["provider_unavailable_pass"])

    def test_p4_no_route_when_all_invalid(self):
        result = validation.failure_injection()
        self.assertTrue(result["no_route_pass"])
        self.assertTrue(all(row["reasons"] for row in result["no_route_decision"]["rejected_candidates"]))

    def test_p4_fallback_depth_bounded(self):
        result = validation.failure_injection()
        self.assertTrue(result["cycle_protection_pass"])
        self.assertLessEqual(result["cycle_decision"]["fallback_depth"], 3)

    def test_p4_route_determinism(self):
        result = validation.performance_and_determinism(100)
        self.assertTrue(result["deterministic"])
        self.assertEqual(result["distinct_logical_decision_sha_count"], 1)

    def test_p4_performance_threshold(self):
        result = validation.performance_and_determinism(1200)
        self.assertTrue(result["performance_pass"], json.dumps(result, ensure_ascii=False))

    def test_p4_gate_requires_zero_llm(self):
        checks = {name: True for name in MANDATORY_CHECKS}
        checks["llm_zero"] = False
        outcome = evaluate_gate(checks, unexplained_divergence_count=0,
                                real_health_unknown_count=0, production_enabled=False)
        self.assertEqual(outcome["status"], "BLOCKED")

    def test_p4_gate_requires_zero_authority_write(self):
        checks = {name: True for name in MANDATORY_CHECKS}
        checks["authority_writes_zero"] = False
        outcome = evaluate_gate(checks, unexplained_divergence_count=0,
                                real_health_unknown_count=0, production_enabled=False)
        self.assertEqual(outcome["status"], "BLOCKED")

    def test_p4_gate_never_enables_production(self):
        outcome = evaluate_gate({name: True for name in MANDATORY_CHECKS},
                                unexplained_divergence_count=0,
                                real_health_unknown_count=1, production_enabled=True)
        self.assertEqual(outcome["status"], "BLOCKED")
        self.assertFalse(outcome["ready_for_cutover_review"])


if __name__ == "__main__":
    unittest.main()
