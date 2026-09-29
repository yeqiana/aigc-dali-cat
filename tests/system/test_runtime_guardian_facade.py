from __future__ import annotations

import datetime as dt
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_guardian_facade as guardian
import episode_runner
import runtime_failure_classifier
import runtime_failure_strategy
import storyos_config


class RuntimeGuardianFacadeTests(unittest.TestCase):
    NOW = dt.datetime(2026, 9, 29, 12, 0, tzinfo=dt.timezone.utc)

    def snapshot_for(self, classification: str, **facts) -> dict:
        snapshot = {"failure": {"return_code": 21, "note": "injected technical failure"}}
        snapshot.update(facts)
        if classification == "NETWORK_TRANSIENT":
            snapshot["failure"] = {"return_code": 21, "error_kind": "network", "note": "connection reset"}
        elif classification == "MYSQL_TRANSIENT":
            snapshot["failure"] = {"return_code": 21, "error_kind": "mysql", "note": "deadlock"}
        elif classification == "JOB_TIMEOUT":
            snapshot["failure"] = {"return_code": 124, "note": "job timeout"}
        elif classification == "CONTENT_FAILURE":
            snapshot["failure"] = {"return_code": 1, "note": "content quality failure"}
        elif classification == "UNKNOWN":
            snapshot["failure"] = {"return_code": 1, "note": "opaque error"}
        return snapshot

    def finding(self, snapshot, expected):
        rows = guardian.detect(snapshot, now=self.NOW)
        self.assertTrue(any(row["classification"] == expected for row in rows), rows)
        return next(row for row in rows if row["classification"] == expected)

    def test_network_maps_to_existing_technical_recovery(self):
        row = guardian.classify(self.finding(self.snapshot_for("NETWORK_TRANSIENT"), "NETWORK_TRANSIENT"))
        self.assertEqual(row["existing_classifier_category"], "TECH_FAILED")
        self.assertEqual(row["existing_recovery_advice"], runtime_failure_strategy.resolve("technical_failure"))

    def test_mysql_transient_maps_to_existing_technical_recovery(self):
        row = guardian.classify(self.finding(self.snapshot_for("MYSQL_TRANSIENT"), "MYSQL_TRANSIENT"))
        self.assertEqual(row["existing_classifier_category"], "TECH_FAILED")
        self.assertEqual(row["proposed_action"], "EXISTING_PERSISTENCE_RECOVERY")

    def test_stale_running_job_is_detected(self):
        snapshot = {"running_job": {"status": "RUNNING", "started_at": "2026-09-29T11:00:00Z", "timeout_seconds": 60}}
        self.finding(snapshot, "JOB_TIMEOUT")

    def test_stale_runner_heartbeat_is_detected(self):
        snapshot = {"runner_state": {"status": "RUNNING", "heartbeat": "2026-09-29T11:50:00Z"}}
        self.finding(snapshot, "HEARTBEAT_STALE")

    def test_stuck_queue_is_detected(self):
        snapshot = {"queue": {"has_runnable_work": True, "last_progress_at": "2026-09-29T11:00:00Z", "stuck_after_seconds": 300}}
        self.finding(snapshot, "QUEUE_STUCK")

    def test_stale_lease_is_detected_without_mutation(self):
        snapshot = {"lease": {"active": True, "acquired_at": "2026-09-29T11:00:00Z", "max_age_seconds": 300}}
        result = guardian.observe(snapshot, now=self.NOW)
        self.assertIn("LEASE_STALE", {row["classification"] for row in result["findings"]})
        self.assertFalse(result["recovery_executed"])
        self.assertEqual(result["authority_writes"], 0)

    def test_stale_host_request_is_detected(self):
        snapshot = {"host_request": {"status": "HOST_WAIT", "created_at": "2026-09-29T11:00:00Z", "max_age_seconds": 300}}
        self.finding(snapshot, "HOST_REQUEST_STALE")

    def test_invalid_transition_never_force_transitions(self):
        result = guardian.observe({"transition": {"valid": False, "reason": "not adjacent"}}, now=self.NOW)
        row = result["findings"][0]
        self.assertEqual(row["classification"], "INVALID_TRANSITION")
        self.assertEqual(row["proposed_action"], "BLOCKED_NO_FORCE_TRANSITION")
        self.assertFalse(result["force_pass"])

    def test_stale_authority_is_blocked(self):
        self.finding({"authority": {"expected_sha256": "a", "actual_sha256": "b"}}, "STALE_AUTHORITY")

    def test_exhausted_retry_uses_terminal_strategy(self):
        row = self.finding({"failure": {"return_code": 21, "attempt": 3, "max_attempts": 3}},
                           "TECHNICAL_RETRY_EXHAUSTED")
        decision = guardian.classify(row)
        self.assertFalse(decision["retry_tech_allowed"])

    def test_content_failure_never_retries_technically(self):
        row = guardian.classify(self.finding(self.snapshot_for("CONTENT_FAILURE"), "CONTENT_FAILURE"))
        self.assertFalse(row["retry_tech_allowed"])
        self.assertEqual(row["existing_recovery_advice"], runtime_failure_strategy.resolve("quality_failure"))

    def test_existing_runner_content_classification_is_observed(self):
        result = guardian.observe_failure(1, note="content validation failed",
                                          existing_category="CONTENT_FAILED")
        row = result["findings"][0]
        self.assertEqual(row["classification"], "CONTENT_FAILURE")
        self.assertFalse(row["retry_tech_allowed"])
        self.assertFalse(row["recovery_executed"])

    def test_generic_runner_failure_keeps_existing_classifier_fact(self):
        result = guardian.observe_failure(21, note="recoverable execution failure",
                                          existing_category="TECH_FAILED")
        row = result["findings"][0]
        self.assertEqual(row["classification"], "UNKNOWN")
        self.assertEqual(row["existing_classifier_category"], "TECH_FAILED")
        self.assertEqual(row["proposed_action"], "DIAGNOSTIC_REQUIRED")

    def test_episode_runner_shadow_hook_compares_without_executing_recovery(self):
        decision = runtime_failure_classifier.classify(21)
        result = episode_runner.guardian_shadow_for_cycle(
            21, decision, attempt=1, max_attempts=3)
        row = result["findings"][0]
        self.assertEqual(row["existing_recovery_action"], "RETRY")
        self.assertFalse(row["matched_existing_recovery"])
        self.assertEqual(row["classification"], "UNKNOWN")
        self.assertEqual(row["proposed_action"], "DIAGNOSTIC_REQUIRED")
        self.assertFalse(row["recovery_executed"])
        self.assertEqual(result["authority_writes"], 0)
        self.assertEqual(result["episode_transitions"], 0)

    def test_episode_runner_shadow_hook_is_noop_on_success(self):
        result = episode_runner.guardian_shadow_for_cycle(
            0, runtime_failure_classifier.classify(0), attempt=1, max_attempts=3)
        self.assertIsNone(result)

    def test_unknown_requests_diagnostics_without_llm(self):
        row = guardian.classify(self.finding(self.snapshot_for("UNKNOWN"), "UNKNOWN"))
        self.assertEqual(row["proposed_action"], "DIAGNOSTIC_REQUIRED")
        result = guardian.observe_failure(1, note="opaque error")
        self.assertEqual(result["llm_calls"], 0)
        self.assertEqual(result["network_calls"], 0)

    def test_shadow_comparison_has_no_recovery_side_effect(self):
        existing = runtime_failure_strategy.resolve("technical_failure")
        result = guardian.observe(self.snapshot_for("NETWORK_TRANSIENT"), existing_recovery=existing, now=self.NOW)
        row = result["findings"][0]
        self.assertTrue(row["matched_existing_recovery"])
        self.assertFalse(row["recovery_executed"])
        self.assertEqual(result["episode_transitions"], 0)
        self.assertEqual(result["authority_writes"], 0)

    def test_config_is_shadow_on_and_production_off(self):
        self.assertEqual(guardian.config(), {"shadow_enabled": True, "production_enabled": False, "config_valid": True})
        cfg = storyos_config.load_config()
        self.assertEqual(storyos_config.get_path(cfg, "agent_runtime.guardian_facade.production_enabled"), False)

    def test_guardian_cannot_execute_recovery(self):
        with patch.object(runtime_failure_strategy, "resolve", wraps=runtime_failure_strategy.resolve) as resolve:
            result = guardian.observe(self.snapshot_for("NETWORK_TRANSIENT"), now=self.NOW)
        resolve.assert_called_once_with("technical_failure")
        self.assertFalse(result["recovery_executed"])
        self.assertEqual(result["llm_calls"], 0)


if __name__ == "__main__":
    unittest.main()
