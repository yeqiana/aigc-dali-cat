#!/usr/bin/env python3
from __future__ import annotations
import json, tempfile, unittest
from unittest.mock import patch
from pathlib import Path
import raw_candidate_budget, runtime_capability_cache, runtime_resume_capsule
import generation_attempt_authority
class T(unittest.TestCase):
    def test_vision_guard_semantics(self):
        self.assertFalse(runtime_capability_cache.vision_verified({"vision_review":"unverified"}))
        self.assertTrue(runtime_capability_cache.vision_verified({"vision_review":"verified"}))
    def test_resume_summary(self):
        x=runtime_resume_capsule._ledger_summary({"frames":{"01":{"status":"PASSED"},"02":{"status":"TECH_FAILED"},"03":{"status":"NEEDS_USER"}}})
        self.assertEqual(x["tech_retry_frames"],["02"]);self.assertEqual(x["blocking_frames"],["03"])
    def test_budget_limit_is_owned_by_generation_attempt_authority(self):
        # Never reserve real attempts just to test a historical JSON budget.
        self.assertEqual(raw_candidate_budget.limits()['repair'], 2)
        self.assertEqual(generation_attempt_authority.MAX_REAL_IMAGE_GENERATION_ATTEMPTS_PER_ASSET, 2)

    def test_authority_denial_fails_closed_without_mysql_or_dispatch(self):
        with tempfile.TemporaryDirectory() as td:
            ep = Path(td)
            with (patch('episode_lifecycle.assert_writable'),
                  patch.object(raw_candidate_budget.production_ledger, 'load_authority', return_value={}),
                  patch.object(generation_attempt_authority, 'reserve',
                      side_effect=generation_attempt_authority.AttemptDenied('TEST_AUTHORITY_DENIED')) as reserve):
                permitted, row = raw_candidate_budget.claim(ep, 1, 'repair', 'fixture-only', token='v251-fixture-denied')
            self.assertFalse(permitted)
            self.assertEqual(row['decision'], 'TEST_AUTHORITY_DENIED')
            reserve.assert_called_once()
            self.assertEqual(list(ep.iterdir()), [])
if __name__=="__main__":unittest.main()
