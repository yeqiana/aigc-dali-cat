"""Read-only audit must never classify risky worktrees as removable."""
from __future__ import annotations

import unittest

from scripts.storyos_worktree_audit_readonly import classify, parse_worktrees


class WorktreeAuditContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.entry = {
            "path": "/repo/.worktrees/old-completed-feature",
            "branch": "feature/old-completed",
            "head": "a" * 40,
        }

    def classify(self, **overrides):
        return classify(
            overrides.pop("entry", self.entry),
            primary_path=overrides.pop("primary_path", "/repo"),
            tracked_or_untracked=overrides.pop("status", []),
            ignored=overrides.pop("ignored", []),
            merged=overrides.pop("merged", True),
        )

    def test_parse_preserves_detached_locked_and_branch(self):
        raw = (
            "worktree /repo\nHEAD " + "a" * 40 + "\nbranch refs/heads/main\n\n"
            "worktree /repo/.worktrees/old\nHEAD " + "b" * 40
            + "\ndetached\nlocked in use\n"
        )
        entries = parse_worktrees(raw)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["branch"], "main")
        self.assertTrue(entries[1]["detached"])
        self.assertTrue(entries[1]["locked"])
        self.assertNotIn("branch", entries[1])

    def test_final_porcelain_record_without_trailing_blank_line(self):
        raw = "worktree /repo/.worktrees/wt\\nHEAD " + "a" * 40 + "\\nbranch refs/heads/feature\\n"
        self.assertEqual(len(parse_worktrees(raw)), 1)

    def test_primary_path_normalization_cannot_bypass_protection(self):
        import os
        if os.name != "nt":
            self.skipTest("Windows mixed-separator protection")
        entry = {**self.entry, "path": "D:/StoryOS/worktree"}
        protected = self.classify(entry=entry, primary_path=r"D:\\StoryOS\\worktree")
        self.assertEqual(protected["classification"], "PROTECTED")
        self.assertFalse(protected["safe_to_delete"])

    def test_only_clean_merged_named_worktree_is_manual_review_candidate(self):
        record = self.classify()
        self.assertEqual(record["classification"], "MANUAL_REVIEW_CANDIDATE")
        self.assertFalse(record["safe_to_delete"])
        self.assertIn("manual_process_ownership_check_required", record["reasons"])

    def test_ignored_runtime_or_model_artifacts_block_removal(self):
        record = self.classify(ignored=[".storyos/runtime/", "episodes/_canary/"])
        self.assertEqual(record["classification"], "PROTECTED")
        self.assertIn("ignored_files_may_contain_production_data", record["reasons"])

    def test_any_untracked_or_tracked_changes_block_removal(self):
        self.assertEqual(self.classify(status=["?? episodes/new-image.png"])["classification"], "PROTECTED")
        self.assertEqual(self.classify(status=[" M web-console/App.tsx"])["classification"], "PROTECTED")

    def test_unmerged_detached_or_locked_block_removal(self):
        self.assertEqual(self.classify(merged=False)["classification"], "PROTECTED")
        self.assertEqual(self.classify(entry={**self.entry, "detached": True})["classification"], "PROTECTED")
        self.assertEqual(self.classify(entry={**self.entry, "locked": True})["classification"], "PROTECTED")

    def test_primary_and_failed_probe_are_always_protected(self):
        self.assertEqual(self.classify(primary_path=self.entry["path"])["classification"], "PROTECTED")
        self.assertEqual(self.classify(status=None)["classification"], "PROTECTED")
        self.assertEqual(self.classify(ignored=None)["classification"], "PROTECTED")
        self.assertEqual(self.classify(merged=None)["classification"], "PROTECTED")


if __name__ == "__main__":
    unittest.main()
