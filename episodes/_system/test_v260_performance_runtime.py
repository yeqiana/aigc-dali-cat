#!/usr/bin/env python3
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

import raw_candidate_budget
import runtime_atomic_store
import runtime_command
import runtime_circuit_breaker

ROOT = Path(__file__).resolve().parents[2]

class RuntimePerformanceV260Test(unittest.TestCase):
    def test_candidate_commit_is_irreversible_by_review_failure(self):
        with tempfile.TemporaryDirectory(prefix="Story OS v260 ") as td:
            ep = Path(td)
            ok, _ = raw_candidate_budget.claim(ep, 1, "repair", token="x")
            self.assertTrue(ok)
            ok, row = raw_candidate_budget.commit(ep, "x")
            self.assertTrue(ok)
            ok, row = raw_candidate_budget.release(ep, "x", "scout failure")
            self.assertFalse(ok)
            self.assertEqual(row["decision"], "COMMITTED_NOT_RELEASED")

    def test_cross_shell_policy(self):
        with self.assertRaises(ValueError):
            runtime_command.validate_argv(["powershell", "-Command", "Write-Host x"])
        with self.assertRaises(ValueError):
            runtime_command.validate_argv(["bash", "-c", "cat <<EOF"])

    def test_visual_review_no_longer_dirties_on_caption_sha(self):
        src = (ROOT / "episodes/_system/incremental_frame_review.py").read_text(encoding="utf-8-sig")
        self.assertNotIn('reasons.append("caption_changed_or_unbound")', src)

    def test_generation_commit_precedes_scout(self):
        src = (ROOT / "episodes/_system/image_worker_pool.py").read_text(encoding="utf-8-sig")
        self.assertIn("raw_candidate_budget.commit", src)
        self.assertLess(src.index("raw_candidate_budget.commit"), src.index("frame_scout.evaluate_candidate"))

    def test_release_uses_visual_freeze_and_caption_audit(self):
        src = (ROOT / "episodes/_system/release_preflight.py").read_text(encoding="utf-8-sig")
        self.assertIn("visual_final_freeze", src)
        self.assertIn("caption_image_audit", src)

    def test_release_does_not_attach_every_body_frame_to_final_critic(self):
        release_src = (ROOT / "episodes/_system/release_preflight.py").read_text(encoding="utf-8-sig")
        caption_src = (ROOT / "episodes/_system/caption_image_audit.py").read_text(encoding="utf-8-sig")
        self.assertIn("release_review_rows(rows)", release_src)
        self.assertNotIn('ROOT / row["path"] for row in rows.values()', release_src)
        self.assertIn("final_publish_with_subtitle", caption_src)
        self.assertIn("subtitle_unobstructed", caption_src)
        self.assertIn("CHUNK = 5", caption_src)

if __name__ == "__main__":
    unittest.main()
