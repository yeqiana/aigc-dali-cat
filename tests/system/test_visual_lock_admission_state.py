#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))

import visual_lock_admission_state as admission_state  # noqa: E402
import visual_lock_candidate_pool as candidate_pool  # noqa: E402
import visual_lock_v21  # noqa: E402


CHECKS = ("visual_profile_match", "reality_first")


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _asset(sha: str = "a" * 64, fc: str = "b" * 64) -> dict:
    return {
        "id": "V-A",
        "role": "first_major_anomaly",
        "frame": 5,
        "sha256": sha,
        "frame_contract_sha256": fc,
    }


def _pass_row() -> dict:
    return {
        "id": "V-A",
        "frame": 5,
        "role": "first_major_anomaly",
        "checks": {key: True for key in CHECKS},
        "issues": [],
        "notes": "actual pixel pass",
    }


class VisualLockAdmissionStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ep = Path(self.tmp.name)
        (self.ep / "meta").mkdir(parents=True, exist_ok=True)
        self.profile_path = self.ep / "profile.json"
        self.profile_path.write_text('{"profile":"test"}', encoding="utf-8")
        self.profile_sha = hashlib.sha256(self.profile_path.read_bytes()).hexdigest()
        _write(self.ep / "meta/visual-profile.json", {"profile_path": str(self.profile_path)})
        _write(self.ep / "meta/episode-state.json", {"tool_version": "2.6.1"})

    def tearDown(self):
        self.tmp.cleanup()

    def test_sha_bound_pass_is_reused_until_binding_changes(self):
        asset = _asset()
        admission_state.record_rows(
            self.ep,
            rows=[_pass_row()],
            assets=[asset],
            profile_sha256=self.profile_sha,
            story_os_version="2.6.1",
            required_checks=CHECKS,
            provenance={"log": "critic.jsonl"},
            attempt=5,
        )
        self.assertEqual(
            admission_state.dirty_assets(
                self.ep, [asset], profile_sha256=self.profile_sha, story_os_version="2.6.1"
            ),
            [],
        )
        changed = _asset(sha="d" * 64)
        self.assertEqual(
            admission_state.dirty_assets(
                self.ep, [changed], profile_sha256=self.profile_sha, story_os_version="2.6.1"
            ),
            [changed],
        )

    def test_candidate_pool_ignores_latest_stochastic_fail_when_bound_pass_is_valid(self):
        asset = _asset()
        admission_state.record_rows(
            self.ep,
            rows=[_pass_row()],
            assets=[asset],
            profile_sha256=self.profile_sha,
            story_os_version="2.6.1",
            required_checks=CHECKS,
            provenance={"log": "critic.jsonl"},
            attempt=5,
        )
        _write(self.ep / "meta/story-gates.json", {
            "visual": {"calibration": {"items": [{
                "id": "V-A", "role": "first_major_anomaly", "frame": 5,
                "sha256": asset["sha256"],
                "frame_contract_sha256": asset["frame_contract_sha256"],
                "decision": "failed",
            }]}}
        })
        _write(self.ep / "meta/visual-profile-review.json", {
            "calibration": [{
                "id": "V-A", "frame": 5, "role": "first_major_anomaly",
                "checks": {"visual_profile_match": False},
                "issues": ["STOCHASTIC_REREVIEW_FAIL"],
            }]
        })
        self.assertEqual(candidate_pool.failed_rows(self.ep), [])
        self.profile_path.write_text('{"profile":"changed"}', encoding="utf-8")
        self.assertEqual([row["frame"] for row in candidate_pool.failed_rows(self.ep)], [5])

    def test_dirty_detection_treats_stale_frame_contract_as_dirty_instead_of_crashing(self):
        metadata = [_asset(fc="old-contract")]
        with patch.object(
            visual_lock_v21,
            "calibration_assets",
            side_effect=[ValueError("first_major_anomaly frame contract stale"), metadata],
        ), patch.object(
            visual_lock_v21.frame_contract,
            "compile_frame",
            return_value={"contract_sha256": "new-contract"},
        ):
            rows = visual_lock_v21._dirty_detection_assets(self.ep)
        self.assertEqual(rows[0]["frame_contract_sha256"], "new-contract")
        self.assertTrue(rows[0]["binding_stale_for_review"])

    def test_restore_ledger_pass_requires_exact_current_candidate_sha(self):
        asset = _asset()
        _write(self.ep / "meta/production-ledger.json", {
            "frames": {"05": {
                "status": "NEEDS_USER",
                "current_candidate": {"sha256": asset["sha256"]},
                "reviews": [],
            }}
        })
        self.assertTrue(admission_state.restore_ledger_pass(
            self.ep, asset=asset, evidence_note="historical bound pass"
        ))
        ledger = json.loads((self.ep / "meta/production-ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(ledger["frames"]["05"]["status"], "PASSED")
        bad = _asset(sha="e" * 64)
        ledger["frames"]["05"]["status"] = "NEEDS_USER"
        _write(self.ep / "meta/production-ledger.json", ledger)
        self.assertFalse(admission_state.restore_ledger_pass(
            self.ep, asset=bad, evidence_note="must not restore"
        ))


if __name__ == "__main__":
    unittest.main()
