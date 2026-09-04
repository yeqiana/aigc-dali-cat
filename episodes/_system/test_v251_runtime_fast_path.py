#!/usr/bin/env python3
from __future__ import annotations
import json, tempfile, unittest
from pathlib import Path
import raw_candidate_budget, runtime_capability_cache, runtime_resume_capsule
class T(unittest.TestCase):
    def test_vision_guard_semantics(self):
        self.assertFalse(runtime_capability_cache.vision_verified({"vision_review":"unverified"}))
        self.assertTrue(runtime_capability_cache.vision_verified({"vision_review":"verified"}))
    def test_resume_summary(self):
        x=runtime_resume_capsule._ledger_summary({"frames":{"01":{"status":"PASSED"},"02":{"status":"TECH_FAILED"},"03":{"status":"NEEDS_USER"}}})
        self.assertEqual(x["tech_retry_frames"],["02"]);self.assertEqual(x["blocking_frames"],["03"])
    def test_budget_limit(self):
        with tempfile.TemporaryDirectory() as td:
            ep=Path(td)
            ok1,_=raw_candidate_budget.claim(ep,1,"repair","a");ok2,_=raw_candidate_budget.claim(ep,1,"repair","b");ok3,row=raw_candidate_budget.claim(ep,1,"repair","c")
            self.assertTrue(ok1 and ok2);self.assertFalse(ok3);self.assertEqual(row["decision"],"STOP_IMAGE_LOOP")
if __name__=="__main__":unittest.main()
