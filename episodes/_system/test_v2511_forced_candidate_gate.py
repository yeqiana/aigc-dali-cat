#!/usr/bin/env python3
from __future__ import annotations
import tempfile, unittest
from pathlib import Path
import raw_candidate_budget as budget

class T(unittest.TestCase):
    def test_idempotent_token_and_release(self):
        with tempfile.TemporaryDirectory() as td:
            ep=Path(td)
            ok1,r1=budget.claim(ep,1,"repair","first","queue-1")
            ok2,r2=budget.claim(ep,1,"repair","technical retry","queue-1")
            self.assertTrue(ok1 and ok2)
            self.assertEqual(r1["used"],1)
            self.assertEqual(r2["decision"],"REUSE_CLAIM")
            ok3,r3=budget.release(ep,"queue-1","tech failure")
            self.assertTrue(ok3);self.assertEqual(r3["used"],0)
    def test_budget_hard_stop(self):
        with tempfile.TemporaryDirectory() as td:
            ep=Path(td)
            self.assertTrue(budget.claim(ep,10,"repair","a","r1")[0])
            self.assertTrue(budget.claim(ep,10,"repair","b","r2")[0])
            ok,row=budget.claim(ep,10,"repair","c","r3")
            self.assertFalse(ok);self.assertEqual(row["decision"],"STOP_IMAGE_LOOP")
if __name__=="__main__":unittest.main()
