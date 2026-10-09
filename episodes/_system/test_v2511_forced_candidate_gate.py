#!/usr/bin/env python3
"""Legacy candidate facade regressions with fake leases only.

Real attempt-limit enforcement belongs to generation_attempt_authority and its
separate authority tests. These tests never contact MySQL or reserve Attempts.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import generation_attempt_authority as authority
import raw_candidate_budget as budget


def fake_lease(index: int) -> dict:
    return {
        "attempt_index": index,
        "generation_key": f"fixture-generation-{index}",
        "fencing_token": f"fixture-fence-{index}",
        "_phase": "RESERVED",
    }


class T(unittest.TestCase):
    def test_idempotent_token_and_pre_dispatch_release(self):
        with tempfile.TemporaryDirectory() as td:
            ep = Path(td)
            with (
                patch("episode_lifecycle.assert_writable"),
                patch.object(budget.production_ledger, "load_authority", return_value={}),
                patch.object(authority, "reserve", return_value=fake_lease(1)) as reserve,
                patch.object(authority, "release_pre_dispatch", return_value={"status": "RELEASED"}) as release,
                patch.dict(budget._ATTEMPT_LEASES, {}, clear=True),
            ):
                ok1, first = budget.claim(ep, 1, "repair", "first", "queue-1")
                ok2, second = budget.claim(ep, 1, "repair", "same token", "queue-1")
                ok3, released = budget.release(ep, "queue-1", "pre-dispatch stop")
            self.assertTrue(ok1 and ok2 and ok3)
            self.assertEqual(first["used"], 1)
            self.assertEqual(second["decision"], "REUSE_CLAIM")
            self.assertEqual(released["decision"], "RELEASED_PRE_DISPATCH")
            reserve.assert_called_once()
            release.assert_called_once()
            self.assertEqual(list(ep.iterdir()), [])

    def test_authority_budget_denial_is_not_retried(self):
        with tempfile.TemporaryDirectory() as td:
            ep = Path(td)
            with (
                patch("episode_lifecycle.assert_writable"),
                patch.object(budget.production_ledger, "load_authority", return_value={}),
                patch.object(authority, "reserve", side_effect=[
                    fake_lease(1), fake_lease(2),
                    authority.AttemptDenied("GENERATION_ATTEMPT_LIMIT_EXHAUSTED"),
                ]) as reserve,
                patch.dict(budget._ATTEMPT_LEASES, {}, clear=True),
            ):
                ok1, _ = budget.claim(ep, 10, "repair", "a", "r1")
                ok2, _ = budget.claim(ep, 10, "repair", "b", "r2")
                ok3, result = budget.claim(ep, 10, "repair", "c", "r3")
            self.assertTrue(ok1 and ok2)
            self.assertFalse(ok3)
            self.assertEqual(result["decision"], "GENERATION_ATTEMPT_LIMIT_EXHAUSTED")
            self.assertEqual(reserve.call_count, 3)
            self.assertEqual(list(ep.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
