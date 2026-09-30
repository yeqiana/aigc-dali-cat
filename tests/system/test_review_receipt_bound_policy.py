from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import review_policy_binding
import story_review
import visual_profile_review_persistence
import frame_semantic_review
import incremental_closure


POLICY_SHA = "a" * 64


class BoundReviewPolicyTests(unittest.TestCase):
    def setUp(self):
        self.ep = Path(tempfile.gettempdir()) / "storyos-bound-review-policy-test"
        self.payload = {
            "schema_version": 1,
            "summary": {"passed": True},
            "issue_codes": [],
            "critic_provenance": {"runtime": "WORK_ISOLATED", "attempt": 1},
        }

    def test_receipt_uses_episode_frozen_sha(self):
        with mock.patch("model_policy_persistence.load", return_value={"policy_sha256": POLICY_SHA}):
            result = review_policy_binding.attach_bound_policy_sha(self.ep, self.payload)
        self.assertEqual(POLICY_SHA, result["model_policy_sha256"])
        self.assertEqual(POLICY_SHA, result["critic_provenance"]["model_policy_sha256"])

    def test_unbound_episode_does_not_inherit_caller_or_global_policy(self):
        supplied = dict(self.payload, model_policy_sha256=POLICY_SHA)
        with mock.patch("model_policy_persistence.load", return_value=None):
            result = review_policy_binding.attach_bound_policy_sha(self.ep, supplied)
        self.assertNotIn("model_policy_sha256", result)
        self.assertNotIn("model_policy_sha256", result["critic_provenance"])

    def test_frozen_episode_policy_survives_global_config_drift(self):
        bound_policy = {"policy_sha256": POLICY_SHA, "policy": {
            "policy_sha256": POLICY_SHA,
            "role_aliases": {"critic.story": "semantic_critic"},
            "profiles": {"semantic_critic": {"model": "gpt-6-luna", "reasoning_effort": "high"}},
        }}
        with mock.patch("model_policy_persistence.load", return_value=bound_policy), \
             mock.patch("model_policy.resolve", side_effect=AssertionError("global policy must not resolve")):
            self.assertEqual(POLICY_SHA, incremental_closure._bound_policy_sha(self.ep, "critic.story"))
            self.assertEqual(POLICY_SHA, frame_semantic_review.bound_review_policy_sha256(self.ep))

    def test_conflicting_supplied_sha_is_rejected(self):
        supplied = dict(self.payload, model_policy_sha256="b" * 64)
        with mock.patch("model_policy_persistence.load", return_value={"policy_sha256": POLICY_SHA}):
            with self.assertRaisesRegex(ValueError, "MODEL_POLICY_SHA_MISMATCH"):
                review_policy_binding.attach_bound_policy_sha(self.ep, supplied)

    def test_story_and_visual_write_bound_sha_at_persistence_boundary(self):
        with mock.patch("model_policy_persistence.load", return_value={"policy_sha256": POLICY_SHA}), \
             mock.patch("review_record_persistence.save", return_value={"decision": "PASS"}) as persist:
            story_review.save_review(self.ep, self.payload, decision="PASS")
            story_payload = persist.call_args.args[3]
            self.assertEqual(POLICY_SHA, story_payload["model_policy_sha256"])

            visual_profile_review_persistence.save(self.ep, self.payload, decision="PASS")
            visual_payload = persist.call_args.args[3]
            self.assertEqual(POLICY_SHA, visual_payload["model_policy_sha256"])


if __name__ == "__main__":
    unittest.main()
