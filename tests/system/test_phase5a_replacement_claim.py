#!/usr/bin/env python3
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import phase5a_collaborative_canary as canary


class Phase5AReplacementClaimTests(unittest.TestCase):
    def test_replacement_validator_accepts_terminal_unknown_without_result(self):
        canary.validate_replacement_attempt_state(
            {"attempts_consumed": 1, "active_attempt_index": None},
            {"attempt_index": 1, "status": "OUTCOME_UNKNOWN", "result_ref": None},
        )

    def test_replacement_validator_rejects_success_or_result(self):
        with self.assertRaisesRegex(canary.CanaryContractError, "NOT_OUTCOME_UNKNOWN"):
            canary.validate_replacement_attempt_state(
                {"attempts_consumed": 1, "active_attempt_index": None},
                {"attempt_index": 1, "status": "SUCCEEDED", "result_ref": "x"},
            )
        with self.assertRaisesRegex(canary.CanaryContractError, "HAS_RESULT"):
            canary.validate_replacement_attempt_state(
                {"attempts_consumed": 1, "active_attempt_index": None},
                {"attempt_index": 1, "status": "OUTCOME_UNKNOWN", "result_ref": "artifact.png"},
            )

    def test_explicit_validation_epoch_is_append_only_after_exhausted_replacement(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve()
            with patch.object(canary, "ROOT", root):
                first_id="phase5a-first"
                first=canary.initialize_workspace(first_id)
                canary.claim_global_canary(first, first_id)

                second_id="phase5a-replacement"
                second=canary.initialize_workspace(second_id)
                with patch.object(canary, "_replacement_source_evidence", return_value={
                    "generation_key":"ga-old","failure_class":"provider_environment",
                }):
                    canary.claim_global_canary(second, second_id)

                third_id="phase5a-validation-2"
                third=canary.initialize_workspace(third_id)
                with patch.object(canary, "_validation_epoch_source_evidence", return_value={
                    "logical_asset_key":"old/frame-01",
                    "attempts_consumed":2,
                    "remaining_attempts":0,
                    "attempt2_generation_key":"ga-a2",
                    "attempt2_status":"OUTCOME_UNKNOWN",
                    "attempt2_failure_class":"generation_failed_before_candidate_commit",
                    "queue_status":"external_blocked",
                    "external_block_reason":"shared_generation_attempt_budget_exhausted",
                }):
                    row=canary.claim_global_canary(
                        third, third_id, allow_validation_epoch=True)
                self.assertEqual(row["validation_epoch"],2)
                self.assertFalse(row["resumed"])
                self.assertFalse(row["replacement"])

                resumed=canary.claim_global_canary(third, third_id)
                self.assertTrue(resumed["resumed"])
                self.assertEqual(resumed["validation_epoch"],2)

                epoch_path=root/canary.VALIDATION_EPOCH_DIR_REL/"epoch-0002.json"
                self.assertTrue(epoch_path.is_file())
                payload=__import__("json").loads(epoch_path.read_text(encoding="utf-8"))
                self.assertEqual(payload["previous_canary_id"],second_id)
                self.assertEqual(payload["previous_attempts_consumed"],2)

    def test_new_validation_epoch_still_requires_explicit_authorization(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve()
            with patch.object(canary, "ROOT", root):
                first=canary.initialize_workspace("phase5a-first")
                canary.claim_global_canary(first,"phase5a-first")
                second=canary.initialize_workspace("phase5a-replacement")
                with patch.object(canary, "_replacement_source_evidence", return_value={
                    "generation_key":"ga-old","failure_class":"provider_environment",
                }):
                    canary.claim_global_canary(second,"phase5a-replacement")
                third=canary.initialize_workspace("phase5a-third")
                with self.assertRaisesRegex(canary.CanaryContractError,"REPLACEMENT_ALREADY_CLAIMED"):
                    canary.claim_global_canary(third,"phase5a-third")

    def test_exactly_one_replacement_claim_is_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve()
            with patch.object(canary, "ROOT", root):
                first_id="phase5a-first"
                first=canary.initialize_workspace(first_id)
                initial=canary.claim_global_canary(first, first_id)
                self.assertFalse(initial["replacement"])

                second_id="phase5a-replacement"
                second=canary.initialize_workspace(second_id)
                with patch.object(canary, "_replacement_source_evidence", return_value={
                    "generation_key":"ga-old","failure_class":"provider_environment",
                }):
                    replacement=canary.claim_global_canary(second, second_id)
                self.assertTrue(replacement["replacement"])
                self.assertFalse(replacement["resumed"])

                resumed=canary.claim_global_canary(second, second_id)
                self.assertTrue(resumed["replacement"])
                self.assertTrue(resumed["resumed"])

                third_id="phase5a-third"
                third=canary.initialize_workspace(third_id)
                with self.assertRaisesRegex(canary.CanaryContractError, "REPLACEMENT_ALREADY_CLAIMED"):
                    canary.claim_global_canary(third, third_id)


if __name__ == "__main__":
    unittest.main()
