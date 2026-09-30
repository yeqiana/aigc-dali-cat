from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import machine_gate
import phase5a_collaborative_canary


class Phase5AVisualLockPreservationTest(unittest.TestCase):
    def test_formal_visual_lock_still_rejects_a_one_asset_calibration(self) -> None:
        """The Phase 5A subpath canary must not weaken the canonical stage gate."""
        with tempfile.TemporaryDirectory() as tmp:
            findings: list[machine_gate.Finding] = []
            visual = {
                "calibration": {
                    "policy": "four_admission_v21",
                    "items": [
                        {
                            "role": machine_gate.FOUR_ADMISSION_ROLES[0],
                            "frame": 1,
                            "asset_path": "episodes/canary/frame-01.png",
                            "sha256": "a" * 64,
                            "frame_contract_sha256": "b" * 64,
                            "decision": "passed",
                        }
                    ],
                }
            }

            machine_gate.check_four_admission(
                Path(tmp), visual, {"release": {"body_frame_count": 1}}, findings,
                metadata_only=True,
            )

        self.assertEqual(len(machine_gate.FOUR_ADMISSION_ROLES), 4)
        self.assertTrue(
            any(f.level == "FAIL" and f.code == "visual_lock_items" for f in findings),
            [str(f) for f in findings],
        )

    def test_ordinary_runtime_cannot_opt_into_canary_scope(self) -> None:
        request = {
            "runtime": {"canary_scope": "PRODUCTION_SUBPATH"},
            "skip_visual_lock": True,
        }
        with self.assertRaises(phase5a_collaborative_canary.CanaryContractError) as raised:
            phase5a_collaborative_canary.authorize_entry(
                entrypoint="runtime_dag",
                runtime_request=request,
            )
        self.assertEqual(str(raised.exception), "CANARY_ENTRYPOINT_REQUIRED")


if __name__ == "__main__":
    unittest.main()
