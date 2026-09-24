"""Focused regression checks for source identity, timing, and forced continuity."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import content_fingerprint
import production_ledger  # bootstrap the facade before its implementation module
import production_ledger_manage as ledger
import frame_semantic_review as semantic
import runtime_node_execution


class ContinuityPolicyTest(unittest.TestCase):
    def test_line_endings_do_not_change_text_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "story.md"
            path.write_bytes("一行\n二行\n".encode())
            expected = content_fingerprint.sha256_file(path)
            path.write_bytes("一行\r\n二行\r\n".encode())
            self.assertEqual(content_fingerprint.sha256_file(path), expected)
            path.write_bytes("一行\r\n三行\r\n".encode())
            self.assertNotEqual(content_fingerprint.sha256_file(path), expected)

    def test_node_records_duration(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = runtime_node_execution.record(Path(tmp), node_id="TEST",
                start_time="2026-09-24T01:00:00.000+00:00",
                end_time="2026-09-24T01:00:01.250+00:00", status="PASS")
            self.assertEqual(row["duration_seconds"], 1.25)

    def test_force_pass_requires_exhausted_budget_and_real_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "candidate.png"
            image.write_bytes(b"real candidate bytes")
            sha = hashlib.sha256(image.read_bytes()).hexdigest()
            frame = {"status": "NEEDS_USER", "content_repairs_used": 0,
                     "current_candidate": {"path": str(image), "sha256": sha},
                     "attempts": [{"result": "success", "candidate": {"sha256": sha}}]}
            data = {"policy": {"max_content_repairs_per_frame": 1}, "frames": {"01": frame}}
            with (mock.patch.object(ledger, "get_ledger", return_value=(root / "ledger.json", data)),
                  mock.patch.object(ledger, "save_json") as save,
                  mock.patch.object(ledger, "verify_attempt_frame_contract_provenance"),
                  mock.patch.object(ledger, "verify_attempt_visual_provenance")):
                with self.assertRaises(ValueError):
                    ledger.force_pass_content_exhaustion(root, "01", "review failed")
                self.assertFalse(save.called)
                frame["content_repairs_used"] = 1
                marker = ledger.force_pass_content_exhaustion(root, "01", "review failed")
                self.assertTrue(marker["forced_pass"])
                self.assertEqual(frame["status"], "PASSED")
                self.assertEqual(frame["reviews"][-1]["decision"], "pass")
                self.assertFalse(marker["visual_quality_reviewed"])

    def test_failed_critic_stays_visible_under_forced_pass(self):
        checks = {name: True for name in semantic.checks_for_version("2.0.3.6", False)}
        first = next(iter(checks))
        checks[first] = False
        row = {"frame": "01", "checks": checks, "issue_codes": [], "decision": "fail"}
        frame = [{"frame": "01"}]
        self.assertTrue(semantic.validate_candidate_rows([row], frame, forced_frames=set()))
        self.assertEqual(semantic.validate_candidate_rows([row], frame, forced_frames={"01"}), [])
        self.assertEqual(row["decision"], "fail")
        self.assertFalse(row["checks"][first])


if __name__ == "__main__":
    unittest.main()
