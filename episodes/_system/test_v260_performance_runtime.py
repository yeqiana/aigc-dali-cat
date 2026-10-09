#!/usr/bin/env python3
from __future__ import annotations
import tempfile
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest.mock import patch

import generation_attempt_authority
import raw_candidate_budget
import runtime_atomic_store
import runtime_command
import runtime_circuit_breaker

ROOT = Path(__file__).resolve().parents[2]

class RuntimePerformanceV260Test(unittest.TestCase):
    def test_atomic_store_retries_transient_windows_replace_denial(self):
        with tempfile.TemporaryDirectory(prefix="Story OS atomic retry ") as td:
            path = Path(td) / "state.json"
            denied = PermissionError(5, "access denied")
            denied.winerror = 5
            real_replace = runtime_atomic_store.os.replace
            calls = {"n": 0}

            def flaky(src, dst):
                calls["n"] += 1
                if calls["n"] == 1:
                    raise denied
                return real_replace(src, dst)

            # Only override this module's OS facade; touching os.name globally
            # would make pathlib instantiate WindowsPath on Linux runners.
            fake_os = SimpleNamespace(
                name="nt", replace=flaky,
                fdopen=runtime_atomic_store.os.fdopen,
                fsync=runtime_atomic_store.os.fsync,
            )
            with patch.object(runtime_atomic_store, "os", fake_os), \
                    patch.object(runtime_atomic_store.time, "sleep", return_value=None):
                runtime_atomic_store.atomic_write_json(path, {"ok": True})
            self.assertEqual(runtime_atomic_store.read_json(path, {}), {"ok": True})
            self.assertGreaterEqual(calls["n"], 2)

    def test_candidate_commit_is_irreversible_by_review_failure(self):
        # A provider-success lease is already terminal before any independent review.
        # Use a simulated lease: CI must never reserve a real Generation Attempt.
        with tempfile.TemporaryDirectory(prefix="Story OS v260 ") as td:
            ep = Path(td)
            lease = {"_phase": "DISPATCH_COMMITTED", "attempt_index": 1,
                     "fencing_token": "fixture-only", "generation_key": "fixture-only"}
            with (patch("episode_lifecycle.assert_writable"),
                  patch.dict(raw_candidate_budget._ATTEMPT_LEASES, {"x": lease}, clear=True),
                  patch.object(generation_attempt_authority, "succeed", return_value={"status": "SUCCEEDED"}) as succeed):
                ok, row = raw_candidate_budget.commit(ep, "x")
                self.assertTrue(ok)
                self.assertEqual(row["decision"], "COMMITTED")
                ok, row = raw_candidate_budget.release(ep, "x", "later review failure")
                self.assertFalse(ok)
                self.assertEqual(row["decision"], "LEASE_NOT_FOUND")
                succeed.assert_called_once()
            self.assertEqual(list(ep.iterdir()), [])

    def test_cross_shell_policy(self):
        with self.assertRaises(ValueError):
            runtime_command.validate_argv(["powershell", "-Command", "Write-Host x"])
        with self.assertRaises(ValueError):
            runtime_command.validate_argv(["bash", "-c", "cat <<EOF"])

    def test_visual_review_no_longer_dirties_on_caption_sha(self):
        src = (ROOT / "episodes/_system/incremental_frame_review.py").read_text(encoding="utf-8-sig")
        self.assertNotIn('reasons.append("caption_changed_or_unbound")', src)

    def test_generation_commit_precedes_separate_review_lane(self):
        src = (ROOT / "episodes/_system/image_worker_pool.py").read_text(encoding="utf-8-sig")
        self.assertIn("raw_candidate_budget.commit", src)
        self.assertIn("scout=None", src)
        self.assertLess(src.index("raw_candidate_budget.commit"), src.index("scout=None"))
        self.assertNotIn("frame_scout.evaluate_candidate", src)

    def test_release_uses_visual_freeze_and_caption_audit(self):
        src = (ROOT / "episodes/_system/release_preflight.py").read_text(encoding="utf-8-sig")
        self.assertIn("visual_final_freeze", src)
        self.assertIn("caption_image_audit", src)

    def test_release_does_not_attach_every_body_frame_to_final_critic(self):
        release_src = (ROOT / "episodes/_system/release_preflight.py").read_text(encoding="utf-8-sig")
        review_src = (ROOT / "episodes/_system/release_preflight_review.py").read_text(encoding="utf-8-sig")
        caption_src = (ROOT / "episodes/_system/caption_image_audit.py").read_text(encoding="utf-8-sig")
        # B4 split moved the release-review row filter into release_preflight_review;
        # the facade re-exports it, so guard both source layers against regressions
        # that would attach every body frame to the final release critic.
        review_layers = release_src + review_src
        self.assertIn("release_review_rows(rows)", review_layers)
        self.assertNotIn('ROOT / row["path"] for row in rows.values()', review_layers)
        self.assertIn("final_publish_with_subtitle", caption_src)
        self.assertIn("subtitle_unobstructed", caption_src)
        self.assertIn("CHUNK = 5", caption_src)

if __name__ == "__main__":
    unittest.main()
