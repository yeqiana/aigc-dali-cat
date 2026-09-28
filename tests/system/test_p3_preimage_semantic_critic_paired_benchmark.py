from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))
sys.path.insert(0, str(ROOT / "episodes/_system/agents"))
sys.path.insert(0, str(ROOT))

from scripts import p3_preimage_semantic_critic_paired_benchmark as benchmark
import preimage_semantic_critic_adapter as critic


class PreimageSemanticCriticPairedBenchmarkTests(unittest.TestCase):
    def test_fixture_set_has_five_distinct_balanced_ground_truth_cases(self):
        path = ROOT / "tests/fixtures/p3_preimage_semantic_critic/cases.json"
        cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
        self.assertGreaterEqual(len(cases), 5)
        self.assertGreaterEqual(sum(row["reference_label"] == "PASS" for row in cases), 2)
        self.assertGreaterEqual(sum(row["reference_label"] == "FAIL" for row in cases), 2)
        self.assertEqual(len({row["sample_id"] for row in cases}), len(cases))

    def test_five_fixture_candidate_sets_are_distinct_and_pass_canonical_verifiers(self):
        path = ROOT / "tests/fixtures/p3_preimage_semantic_critic/cases.json"
        cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
        with tempfile.TemporaryDirectory(prefix="p3-preimage-bench-", dir=ROOT / ".storyos") as raw:
            root = Path(raw)
            hashes = []
            for index, case in enumerate(cases):
                episode = root / f"case-{index}"
                snapshot, tasks = benchmark._fixture_episode(episode, case)
                capsule = critic.build_frozen_candidate_set(episode, snapshot, tasks)
                self.assertEqual(capsule["canonical_checks"]["all_task_contract_verifiers_pass"], True)
                hashes.append(capsule["candidate_set_sha256"])
            self.assertEqual(len(set(hashes)), len(cases))

    def test_reference_issue_fixture_flags_are_deterministic(self):
        path = ROOT / "tests/fixtures/p3_preimage_semantic_critic/cases.json"
        cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
        self.assertEqual(sum(bool(case["reference_issue_codes"]) for case in cases), 3)
        self.assertTrue(all(case.get("repair_scope") is not None for case in cases))


if __name__ == "__main__":
    unittest.main()
