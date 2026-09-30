from __future__ import annotations

import unittest
from unittest import mock

import runtime_dag


class IncrementalRuntimeDispatchPhase4Tests(unittest.TestCase):
    def test_noop_production_plan_selects_evidence_reuse(self):
        plan = {"frame_plan": {"action": "NOOP", "dirty_frames": []}}
        self.assertEqual(
            runtime_dag.incremental_runtime_strategy(
                plan, "PRODUCTION", "PRODUCTION_PASSED"),
            "REUSE_FRAME_EVIDENCE",
        )

    def test_clean_story_and_visual_evidence_do_not_bypass_unfinished_domain_steps(self):
        plan = {"story": "CLEAN", "visual": {"state": "CLEAN"}}
        self.assertEqual(
            "RUN_WORKER",
            runtime_dag.incremental_runtime_strategy(plan, "CREATIVE_STORY", "IDEA_LOCKED"),
        )
        self.assertEqual(
            "RUN_WORKER",
            runtime_dag.incremental_runtime_strategy(plan, "VISUAL_LOCK", "PRODUCTION_PASSED"),
        )
        self.assertEqual(
            "RUN_WORKER",
            runtime_dag.incremental_runtime_strategy(plan, "CREATIVE_STORY", "STORYBOARD_LOCKED"),
        )
        self.assertEqual(
            "RUN_WORKER",
            runtime_dag.incremental_runtime_strategy(plan, "VISUAL_LOCK", "VISUAL_CALIBRATED"),
        )

    def test_dirty_or_missing_story_and_visual_evidence_route_only_targeted_review(self):
        self.assertEqual(
            "VERIFY_STORY_EVIDENCE",
            runtime_dag.incremental_runtime_strategy(
                {"story": "DIRTY"}, "CREATIVE_STORY", "STORYBOARD_LOCKED"),
        )
        self.assertEqual(
            "VERIFY_VISUAL_EVIDENCE",
            runtime_dag.incremental_runtime_strategy(
                {"visual": {"state": "MISSING"}}, "VISUAL_LOCK", "VISUAL_CALIBRATED"),
        )
        self.assertEqual(
            "RUN_WORKER",
            runtime_dag.incremental_runtime_strategy(
                {"story": "DIRTY"}, "CREATIVE_STORY", "IDEA_LOCKED"),
        )

    def test_patch_plan_selects_scoped_incremental_verification(self):
        plan = {"frame_plan": {"action": "PATCH", "dirty_frames": ["03"],
                               "context_frames": ["02", "03", "04"]}}
        self.assertEqual(
            runtime_dag.incremental_runtime_strategy(
                plan, "PRODUCTION", "PRODUCTION_PASSED"),
            "VERIFY_INCREMENTALLY",
        )

    def test_transitional_production_state_keeps_scheduler_owner(self):
        plan = {"frame_plan": {"action": "PATCH", "dirty_frames": ["03"]}}
        self.assertEqual(
            runtime_dag.incremental_runtime_strategy(
                plan, "PRODUCTION", "VISUAL_CALIBRATED"),
            "RUN_WORKER",
        )

    def test_unhandled_missing_authority_fails_closed(self):
        self.assertIn(
            "missing production ledger",
            runtime_dag._unsupported_missing_evidence(
                {"missing": ["meta/production-ledger.json"]}),
        )
        self.assertIn(
            "unsupported missing evidence",
            runtime_dag._unsupported_missing_evidence(
                {"missing": ["meta/unregistered-evidence.json"]}),
        )
        self.assertIsNone(runtime_dag._unsupported_missing_evidence(
            {"missing": ["meta/story-semantic-review.json"]}))

    def test_structured_missing_and_dirty_plan_statuses_are_consumed(self):
        plan = {"story": {"state": "MISSING"}, "visual": {"status": "DIRTY"}}
        self.assertEqual(runtime_dag._plan_evidence_state(plan, "story"), "MISSING")
        self.assertEqual(runtime_dag._plan_evidence_state(plan, "visual"), "DIRTY")

    def test_noop_verification_uses_read_only_verify_command(self):
        fake_result = mock.Mock(returncode=0, stdout="INCREMENTAL FRAME REVIEW VERIFY PASS")
        with mock.patch.object(runtime_dag, "run", return_value=fake_result) as run, \
             mock.patch.object(runtime_dag.runtime_observability,
                               "safe_record_runtime_event", return_value=True):
            rc, note = runtime_dag._run_incremental_frame_verification(
                ".", attempt=2, codex=None, timeout=5, run_id="r", trace_id="t",
                command="verify")
        self.assertEqual(rc, 0)
        self.assertIn("VERIFY PASS", note)
        argv = run.call_args.args[0]
        self.assertEqual(argv[2], "verify")
        self.assertNotIn("review", argv)
        self.assertNotIn("--codex", argv)

    def test_dirty_verification_dispatches_incremental_review_command(self):
        fake_result = mock.Mock(returncode=0, stdout="INCREMENTAL FRAME REVIEW REUSE: 0 critic calls")
        with mock.patch.object(runtime_dag, "run", return_value=fake_result) as run, \
             mock.patch.object(runtime_dag.runtime_observability,
                               "safe_record_runtime_event", return_value=True):
            rc, _ = runtime_dag._run_incremental_frame_verification(
                ".", attempt=1, codex="codex.exe", timeout=9, run_id="r", trace_id="t",
                command="review")
        self.assertEqual(rc, 0)
        argv = run.call_args.args[0]
        self.assertEqual(argv[2], "review")
        self.assertIn("--attempt", argv)
        self.assertIn("--codex", argv)

    def test_plan_emits_reuse_invalidation_and_missing_telemetry(self):
        plan = {
            "story": "CLEAN",
            "visual": "DIRTY",
            "subtitle": "MISSING",
            "evidence_plan": {
                "story": {"state": "CLEAN", "action": "REUSE",
                          "evidence_ref": "meta/story-semantic-review.json",
                          "evidence_fingerprint": "story-fingerprint",
                          "source_artifact_sha": "story-source-sha",
                          "policy_sha256": "story-policy-sha",
                          "reason": "PASS_FINGERPRINT_MATCH"},
                "visual": {"state": "DIRTY", "action": "VERIFY",
                           "evidence_ref": "meta/visual-profile-review.json",
                           "fingerprint": "visual-fingerprint",
                           "old_fingerprint": "visual-old",
                           "new_fingerprint": "visual-new",
                           "source_sha256": "visual-source-sha",
                           "model_policy_sha256": "visual-policy-sha",
                           "reason": ["POLICY_SHA_CHANGED", "SCHEMA_VERSION_CHANGED"]},
                "subtitle": {"state": "MISSING", "action": "GENERATE_EVIDENCE",
                             "evidence_fingerprint": "subtitle-fingerprint",
                             "source": {"sha256": "subtitle-source-sha"},
                             "reason": "MISSING_EVIDENCE"},
            },
            "frame_plan": {"action": "PATCH", "dirty_frames": ["03"],
                           "context_frames": ["02", "03", "04"],
                           "reused_frames": ["01", "02", "04"],
                           "old_fingerprints": {"03": "old-frame-fingerprint"},
                           "new_fingerprints": {"03": "new-frame-fingerprint"},
                           "reasons": {"03": ["asset_sha_changed"]}},
        }
        with mock.patch.object(runtime_dag, "_incremental_plan_policy_sha", return_value="frozen"), \
             mock.patch.object(runtime_dag.runtime_observability,
                               "safe_record_runtime_event", return_value=True) as record:
            runtime_dag._record_incremental_plan_events(
                ".", plan, run_id="r", trace_id="t")
        names = [call.args[1] for call in record.call_args_list]
        self.assertIn("EVIDENCE_REUSED", names)
        self.assertIn("EVIDENCE_INVALIDATED", names)
        self.assertIn("EVIDENCE_MISSING", names)
        evidence_events = {
            call.kwargs["evidence_type"]: (call.args[1], call.kwargs)
            for call in record.call_args_list
            if call.args[1] in {"EVIDENCE_REUSED", "EVIDENCE_INVALIDATED", "EVIDENCE_MISSING"}
        }
        story_event, story = evidence_events["story-semantic-review"]
        self.assertEqual(story_event, "EVIDENCE_REUSED")
        self.assertEqual(story["evidence_ref"], "meta/story-semantic-review.json")
        self.assertEqual(story["evidence_fingerprint"], "story-fingerprint")
        self.assertEqual(story["source_sha"], "story-source-sha")
        self.assertEqual(story["policy_sha"], "story-policy-sha")
        self.assertEqual(story["reason"], "PASS_FINGERPRINT_MATCH")
        visual_event, visual = evidence_events["visual-profile-review"]
        self.assertEqual(visual_event, "EVIDENCE_INVALIDATED")
        self.assertEqual(visual["evidence_fingerprint"], "visual-fingerprint")
        self.assertEqual(visual["source_sha"], "visual-source-sha")
        self.assertEqual(visual["policy_sha"], "visual-policy-sha")
        self.assertEqual(visual["old_fingerprint"], "visual-old")
        self.assertEqual(visual["new_fingerprint"], "visual-new")
        self.assertEqual(visual["reason"], "POLICY_SHA_CHANGED,SCHEMA_VERSION_CHANGED")
        subtitle_event, subtitle = evidence_events["subtitle-layout-audit"]
        self.assertEqual(subtitle_event, "EVIDENCE_MISSING")
        self.assertEqual(subtitle["evidence_ref"], "meta/subtitle-layout-audit.json")
        self.assertEqual(subtitle["evidence_fingerprint"], "subtitle-fingerprint")
        self.assertEqual(subtitle["source_sha"], "subtitle-source-sha")
        self.assertEqual(subtitle["reason"], "MISSING_EVIDENCE")
        frame_recomputed = next(
            call for call in record.call_args_list
            if call.args[1] == "FRAME_REVIEW_RECOMPUTED")
        self.assertEqual(frame_recomputed.kwargs["dirty_frames"], ["03"])
        self.assertEqual(frame_recomputed.kwargs["context_frames"], ["02", "03", "04"])
        invalidated = next(
            call for call in record.call_args_list
            if call.args[1] == "EVIDENCE_INVALIDATED" and call.kwargs.get("frame_id") == "03")
        self.assertEqual(invalidated.kwargs["old_fingerprint"], "old-frame-fingerprint")
        self.assertEqual(invalidated.kwargs["new_fingerprint"], "new-frame-fingerprint")


if __name__ == "__main__":
    unittest.main()
