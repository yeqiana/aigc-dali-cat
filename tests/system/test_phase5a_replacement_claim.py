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

    def test_exactly_one_replacement_claim_is_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
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
