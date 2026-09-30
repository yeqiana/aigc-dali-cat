from __future__ import annotations

import unittest
import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
import evidence_reuse


class EvidenceReuseContractTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            "evidence_type": "STORY_SEMANTIC",
            "source_artifact_sha": "story-a",
            "source_contract_sha": "board-a",
            "relevant_context_sha": "context-a",
            "bound_model_policy_sha": "policy-a",
            "review_schema_version": 1,
        }
        self.evidence = {
            "schema_version": 1,
            "source_artifact_sha": "story-a",
            "source_contract_sha": "board-a",
            "relevant_context_sha": "context-a",
            "model_policy_sha256": "policy-a",
            "summary": {"passed": True},
            "issue_codes": [],
            "critic_provenance": {"reviewed_at": "2026-01-01T00:00:00Z", "worker_id": "w1"},
        }

    def test_pass_evidence_with_exact_bound_identity_is_reusable(self):
        result = evidence_reuse.validate_reusable(self.evidence, expected=self.expected)
        self.assertTrue(result["reusable"])
        self.assertEqual([], result["reasons"])
        self.assertEqual(64, len(result["fingerprint"]))

    def test_runtime_metadata_does_not_change_fingerprint(self):
        first = evidence_reuse.compute_fingerprint(**self.expected)
        changed = dict(self.expected)
        changed["worker_id"] = "w2"
        changed["timestamp"] = "later"
        second = evidence_reuse.compute_fingerprint(
            **{key: value for key, value in changed.items() if key in self.expected}
        )
        self.assertEqual(first, second)

    def test_policy_drift_fails_closed(self):
        changed = dict(self.expected, bound_model_policy_sha="policy-b")
        result = evidence_reuse.validate_reusable(self.evidence, expected=changed)
        self.assertFalse(result["reusable"])
        self.assertIn("POLICY_SHA_CHANGED", result["reasons"])

    def test_missing_policy_or_invalid_pass_fails_closed(self):
        evidence = dict(self.evidence)
        evidence.pop("model_policy_sha256")
        evidence["issue_codes"] = ["ISSUE"]
        result = evidence_reuse.validate_reusable(evidence, expected=self.expected)
        self.assertFalse(result["reusable"])
        self.assertIn("POLICY_SHA_MISSING", result["reasons"])
        self.assertIn("EVIDENCE_HAS_ISSUES", result["reasons"])

    def test_invalid_verifier_result_fails_closed(self):
        result = evidence_reuse.validate_reusable(
            self.evidence, expected=self.expected, verify_errors=["source mismatch"]
        )
        self.assertFalse(result["reusable"])
        self.assertIn("INVALID_EVIDENCE", result["reasons"])

    def test_missing_issue_codes_or_conflicting_policy_bindings_fail_closed(self):
        missing = dict(self.evidence)
        missing.pop("issue_codes")
        result = evidence_reuse.validate_reusable(missing, expected=self.expected)
        self.assertFalse(result["reusable"])
        self.assertIn("ISSUE_CODES_MISSING_OR_INVALID", result["reasons"])

        conflict = dict(self.evidence)
        conflict["critic_provenance"] = {"model_policy_sha256": "policy-b"}
        result = evidence_reuse.validate_reusable(conflict, expected=self.expected)
        self.assertFalse(result["reusable"])
        self.assertIn("POLICY_SHA_CONFLICT", result["reasons"])


if __name__ == "__main__":
    unittest.main()
