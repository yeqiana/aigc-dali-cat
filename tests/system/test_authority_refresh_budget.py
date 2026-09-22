#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import raw_candidate_budget


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class AuthorityRefreshBudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ep = Path(self.tmp.name)
        self.contract_a = "a" * 64
        self.contract_b = "b" * 64
        self._authorize(self.contract_a)

    def tearDown(self):
        self.tmp.cleanup()

    def _authorize(self, contract_sha: str) -> None:
        _write(self.ep / "meta/production-ledger.json", {
            "canvas": {"width": 1080, "height": 1350, "aspect_ratio": "4:5"},
            "frames": {"17": {
                "status": "AUTHORITY_REFRESH_AUTHORIZED",
                "authority_refresh_authorization": {
                    "frame_contract_sha256": contract_sha,
                    "approval_text": "direct user approved authority refresh",
                    "approval_basis": "direct_user_authority_contract_refresh",
                },
            }},
        })

    def _authorize_continuation(self, index: int) -> None:
        _write(self.ep / "meta/production-ledger.json", {
            "canvas": {"width": 1080, "height": 1350, "aspect_ratio": "4:5"},
            "frames": {"17": {
                "status": "USER_CONTINUATION_REPAIR_AUTHORIZED",
                "user_continuation_authorizations": [{
                    "approval_text": "continue processing frame 17",
                    "approval_basis": "direct_user_continuation_after_exhaustion",
                    "continuation_index": index,
                }],
            }},
        })

    def test_queue_item_uses_contract_scoped_authority_refresh_kind(self):
        item = {"kind": "repair", "capture_id": "authority-refresh-17", "frame_contract": {"contract_sha256": self.contract_a}}
        self.assertEqual(raw_candidate_budget.kind_for_queue_item(item), "authority_refresh")
        self.assertEqual(raw_candidate_budget.semantic_key_for_queue_item(item), self.contract_a)

    def test_authority_refresh_does_not_borrow_ordinary_repair_slots(self):
        self.assertTrue(raw_candidate_budget.claim(self.ep, 17, "repair", token="r1")[0])
        self.assertTrue(raw_candidate_budget.claim(self.ep, 17, "repair", token="r2")[0])
        self.assertFalse(raw_candidate_budget.claim(self.ep, 17, "repair", token="r3")[0])

        ok, row = raw_candidate_budget.claim(
            self.ep, 17, "authority_refresh", token="a1", semantic_key=self.contract_a,
            reason="new authority contract",
        )
        self.assertTrue(ok)
        self.assertEqual(row["kind"], "authority_refresh")
        self.assertEqual(row["semantic_key"], self.contract_a)

    def test_same_contract_can_commit_only_one_retained_authority_refresh_candidate(self):
        ok, _ = raw_candidate_budget.claim(self.ep, 17, "authority_refresh", token="a1", semantic_key=self.contract_a)
        self.assertTrue(ok)
        self.assertTrue(raw_candidate_budget.commit(self.ep, "a1")[0])
        ok, row = raw_candidate_budget.claim(self.ep, 17, "authority_refresh", token="a2", semantic_key=self.contract_a)
        self.assertFalse(ok)
        self.assertEqual(row["decision"], "AUTHORITY_REFRESH_CONTRACT_ALREADY_CLAIMED")

    def test_new_authorized_contract_gets_one_new_slot_without_manual_override(self):
        ok, _ = raw_candidate_budget.claim(self.ep, 17, "authority_refresh", token="a1", semantic_key=self.contract_a)
        self.assertTrue(ok)
        self.assertTrue(raw_candidate_budget.commit(self.ep, "a1")[0])
        self._authorize(self.contract_b)
        ok, row = raw_candidate_budget.claim(self.ep, 17, "authority_refresh", token="b1", semantic_key=self.contract_b)
        self.assertTrue(ok)
        self.assertEqual(row["semantic_key"], self.contract_b)

    def test_contract_without_matching_direct_user_authorization_is_refused(self):
        ok, row = raw_candidate_budget.claim(self.ep, 17, "authority_refresh", token="x", semantic_key=self.contract_b)
        self.assertFalse(ok)
        self.assertEqual(row["decision"], "AUTHORITY_REFRESH_NOT_AUTHORIZED")

    def test_machine_verified_stale_contract_can_claim_without_fake_user_approval(self):
        candidate_sha = "c" * 64
        _write(self.ep / "meta/production-ledger.json", {
            "frames": {"17": {
                "status": "AUTHORITY_REFRESH_AUTHORIZED",
                "current_candidate": {"sha256": candidate_sha},
                "attempts": [{
                    "candidate": {"sha256": candidate_sha},
                    "request": {"frame_contract": {"contract_sha256": self.contract_a}},
                }],
                "authority_refresh_authorization": {
                    "frame_contract_sha256": self.contract_b,
                    "previous_frame_contract_sha256": self.contract_a,
                    "candidate_sha256": candidate_sha,
                    "approval_basis": "machine_verified_frame_contract_drift",
                    "reason": "canonical authority changed",
                },
            }},
        })
        with patch.object(raw_candidate_budget.frame_contract, "verify_recorded_provenance",
                          return_value=["frame 17 generation frame_contract_sha256 stale"]):
            ok, row = raw_candidate_budget.claim(
                self.ep, 17, "authority_refresh", token="machine-1", semantic_key=self.contract_b)
        self.assertTrue(ok)
        self.assertEqual(row["semantic_key"], self.contract_b)

    def test_machine_refresh_is_refused_when_stale_proof_disappears(self):
        candidate_sha = "c" * 64
        _write(self.ep / "meta/production-ledger.json", {
            "frames": {"17": {
                "status": "AUTHORITY_REFRESH_AUTHORIZED",
                "current_candidate": {"sha256": candidate_sha},
                "attempts": [{
                    "candidate": {"sha256": candidate_sha},
                    "request": {"frame_contract": {"contract_sha256": self.contract_b}},
                }],
                "authority_refresh_authorization": {
                    "frame_contract_sha256": self.contract_b,
                    "previous_frame_contract_sha256": self.contract_a,
                    "candidate_sha256": candidate_sha,
                    "approval_basis": "machine_verified_frame_contract_drift",
                    "reason": "canonical authority changed",
                },
            }},
        })
        with patch.object(raw_candidate_budget.frame_contract, "verify_recorded_provenance", return_value=[]):
            ok, row = raw_candidate_budget.claim(
                self.ep, 17, "authority_refresh", token="machine-no-stale", semantic_key=self.contract_b)
        self.assertFalse(ok)
        self.assertEqual(row["decision"], "AUTHORITY_REFRESH_NOT_AUTHORIZED")

    def test_user_continuation_uses_its_own_semantic_budget_lane(self):
        self._authorize_continuation(1)
        item = {"kind": "repair", "capture_id": "user-continuation-VISUAL_LOCK-17-01"}
        self.assertEqual(raw_candidate_budget.kind_for_queue_item(item), "user_continuation")
        semantic = raw_candidate_budget.semantic_key_for_queue_item(item)
        ok, row = raw_candidate_budget.claim(self.ep, 17, "user_continuation", token="c1", semantic_key=semantic)
        self.assertTrue(ok)
        self.assertEqual(row["kind"], "user_continuation")
        self.assertTrue(raw_candidate_budget.commit(self.ep, "c1")[0])
        ok, row = raw_candidate_budget.claim(self.ep, 17, "user_continuation", token="c1b", semantic_key=semantic)
        self.assertFalse(ok)
        self.assertEqual(row["decision"], "USER_CONTINUATION_AUTHORIZATION_ALREADY_CLAIMED")

    def test_new_explicit_continue_authorization_gets_one_new_slot_without_override(self):
        self._authorize_continuation(1)
        first = "user-continuation-VISUAL_LOCK-17-01"
        self.assertTrue(raw_candidate_budget.claim(self.ep, 17, "user_continuation", token="c1", semantic_key=first)[0])
        self.assertTrue(raw_candidate_budget.commit(self.ep, "c1")[0])
        self._authorize_continuation(2)
        second = "user-continuation-VISUAL_LOCK-17-02"
        ok, row = raw_candidate_budget.claim(self.ep, 17, "user_continuation", token="c2", semantic_key=second)
        self.assertTrue(ok)
        self.assertEqual(row["semantic_key"], second.lower())


if __name__ == "__main__":
    unittest.main()
