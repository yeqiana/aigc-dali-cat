#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_critic_runner as runner
import runtime_router
import fast_frame_scout
import visual_review_legacy
import visual_lock_v21
import frame_semantic_review
import incremental_frame_review


class CriticRunnerMigrationTests(unittest.TestCase):
    """B2 guard: critic consumers share codex_critic_runner launch primitives."""

    def source(self, module) -> str:
        return Path(module.__file__).read_text(encoding="utf-8-sig")

    def test_lane_aliases_point_to_single_runner(self):
        self.assertIs(fast_frame_scout.resolve_codex, runner.resolve_codex)
        self.assertIs(fast_frame_scout.prefix, runner.prefix)
        self.assertIs(visual_review_legacy.resolve_codex, runner.resolve_codex)
        self.assertIs(visual_review_legacy.prefix, runner.prefix)
        self.assertIs(visual_lock_v21.resolve_codex, runner.resolve_codex)
        self.assertIs(visual_lock_v21.prefix, runner.prefix)
        self.assertIs(frame_semantic_review.resolve_codex, runner.resolve_codex)
        self.assertIs(frame_semantic_review.command_prefix, runner.prefix)

    def test_no_local_duplicate_definitions(self):
        for module in (
            fast_frame_scout,
            visual_review_legacy,
            visual_lock_v21,
            frame_semantic_review,
            incremental_frame_review,
        ):
            src = self.source(module)
            self.assertNotIn("def resolve_codex(", src)
            self.assertNotIn("def command_prefix(", src)
        for module in (fast_frame_scout, visual_review_legacy, visual_lock_v21):
            self.assertNotIn("def prefix(", self.source(module))
        self.assertNotIn("_resolve_codex", self.source(incremental_frame_review))
        self.assertNotIn("_command_prefix", self.source(incremental_frame_review))

    def test_consumers_delegate_launch_to_single_runner(self):
        for module in (
            fast_frame_scout,
            visual_review_legacy,
            visual_lock_v21,
            frame_semantic_review,
            incremental_frame_review,
        ):
            self.assertIn("critic_runner.launch(", self.source(module))

    def test_lane_effort_and_attachment_contracts_preserved(self):
        # W-88: reasoning effort is no longer a per-lane source literal. Every vision lane
        # reads it through runtime_router.vision_review_effort(kind), so the values live in
        # config/storyos.yaml (runtime.review.vision.reasoning_effort_*) instead of drifting
        # apart across five modules.
        for module, kind in (
            (fast_frame_scout, "fast"),
            (frame_semantic_review, "final"),
            (incremental_frame_review, "default"),
            (visual_lock_v21, "final"),
        ):
            self.assertIn(f'runtime_router.vision_review_effort("{kind}")', self.source(module))
        # visual_review_legacy is the only lane still declaring an effort literal directly.
        self.assertIn('reasoning_effort_literal=\'model_reasoning_effort="high"\'',
                      self.source(visual_review_legacy))
        for kind in ("fast", "final", "default"):
            self.assertIn(runtime_router.vision_review_effort(kind), {"low", "medium", "high"})
        visual_lock_src = self.source(visual_lock_v21)
        self.assertIn("attachments=staged_assets", visual_lock_src)
        self.assertIn("output_path=candidate", visual_lock_src)
        self.assertIn('extra=["--ignore-rules"]', visual_lock_src)


if __name__ == "__main__":
    unittest.main()
