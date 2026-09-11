#!/usr/bin/env python3
"""Phase 4.4 Visual Profile end-to-end validation.

The full governance chain, exercised through the real Episode creation entry
point rather than by hand-building locks:

    Story Intent
        -> Selector (visual_profile_selector)
        -> Selection Evidence
        -> Visual Lock DRAFT   (meta/visual-profile.json, Phase 4.1)
        -> confirm             (Phase 4.2 lifecycle)
        -> LOCKED
        -> freeze              (only once production assets exist)
        -> FROZEN
        -> production gate     (Phase 4.3, read-only)

  Case1: real daily life        -> M00 -> confirm -> production gate PASS
  Case2: ancient ordinary people -> M01 -> confirm -> PASS
  Case3: heaven workplace       -> M02 -> confirm -> PASS
  Case4: jiangnan immersive     -> M03 -> confirm -> PASS
  Case5: ancient + jiangnan     -> needs_confirmation -> gate FAIL -> confirm -> PASS
  Case6: FROZEN lock            -> any modification FAILs

Extra coverage: release stages additionally require FROZEN, the gate is
read-only, legacy Episodes are never blocked, and neither the lifecycle module
nor the gate touches Runtime or the repository episode-state.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import story_creator  # noqa: E402
import visual_profile_gate as gate  # noqa: E402
import visual_profile_lock  # noqa: E402
import visual_profile_lock_adapter as adapter  # noqa: E402
import visual_profile_lock_lifecycle as lifecycle  # noqa: E402
import visual_profile_registry as registry  # noqa: E402
import visual_profile_selector as selector  # noqa: E402

M00 = selector.M00
M01 = selector.M01
M02 = selector.M02
M03 = selector.M03

AT = "2026-09-12T09:00:00+08:00"
AT_FREEZE = "2026-09-12T18:00:00+08:00"

JIANNAN = "江南"

REAL_DAILY = {"story_intent": {"world": "real", "theme": "daily_life"}}
ANCIENT_ORDINARY = {"story_intent": {"world": "historical_real", "era": "ancient",
                                     "theme": "ordinary_people"}}
HEAVEN_WORKPLACE = {"story_intent": {"world": "fictional", "theme": "workplace"},
                    "audience_expectation": {"fantasy_level": "high"}}
JIANGNAN_IMMERSIVE = {"story_intent": {"world": "real", "location": JIANNAN,
                                       "experience_type": "immersive_first_person"}}
ANCIENT_JIANGNAN = {"story_intent": {"world": "historical_real", "era": "ancient",
                                     "location": JIANNAN,
                                     "experience_type": "immersive_first_person"}}


class EndToEndBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="visual-profile-e2e-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        shutil.copytree(ROOT / "standards/visual_profiles", self.root / "standards/visual_profiles")

    # ---- helpers --------------------------------------------------------
    def create(self, title: str, **kwargs) -> Path:
        return story_creator.create_episode(self.root, title, **kwargs)

    def lock(self, episode: Path) -> dict:
        return json.loads((episode / "meta/visual-profile.json").read_text(encoding="utf-8"))

    def lock_path(self, episode: Path) -> Path:
        return episode / "meta/visual-profile.json"

    def confirm(self, episode: Path, *, profile_id=None, by: str = "yeqian", at: str = AT):
        return lifecycle.confirm_visual_lock(
            episode, confirmed_by=by, confirmed_at=at, reason="reviewed",
            profile_id=profile_id, story_root=self.root)

    def freeze(self, episode: Path, *, by: str = "yeqian", at: str = AT_FREEZE):
        return lifecycle.freeze_visual_lock(
            episode, frozen_by=by, frozen_at=at, reason="production started", story_root=self.root)

    def production_gate(self, episode: Path, *, stage: str = gate.STAGE_PRODUCTION) -> dict:
        return gate.validate_visual_profile_for_production(
            episode=episode, story_root=self.root, stage=stage)

    def assert_selected_and_produced(self, payload: dict, profile_id: str) -> Path:
        """Create -> draft SELECTED -> gate blocks -> confirm -> gate PASS."""
        episode = self.create("e2e_" + profile_id, selector_input=payload)

        draft = self.lock(episode)
        self.assertEqual(draft["profile_id"], profile_id, draft)
        self.assertEqual(draft["lifecycle_state"], adapter.LIFECYCLE_SELECTED)
        self.assertEqual(draft["confirmation_mode"], adapter.CONFIRMATION_PENDING)

        blocked = self.production_gate(episode)
        self.assertEqual(blocked["status"], gate.STATUS_FAIL)
        self.assertEqual(blocked["code"], gate.ERROR_NOT_LOCKED)
        self.assertFalse(blocked["ok"])

        report = self.confirm(episode)
        self.assertEqual(report["from"], adapter.LIFECYCLE_SELECTED)
        self.assertEqual(report["to"], adapter.LIFECYCLE_LOCKED)
        self.assertTrue(report["written"])

        locked = self.lock(episode)
        self.assertEqual(locked["lifecycle_state"], adapter.LIFECYCLE_LOCKED)
        self.assertEqual(locked["profile_id"], profile_id)
        self.assertEqual(locked["confirmation"]["mode"], "human")
        self.assertEqual(locked["confirmation"]["confirmed_by"], "yeqian")
        self.assertTrue(lifecycle.is_confirmed(locked))

        result = self.production_gate(episode)
        self.assertEqual(result["status"], gate.STATUS_PASS, result)
        self.assertTrue(result["ok"])
        self.assertEqual(result["lifecycle_state"], adapter.LIFECYCLE_LOCKED)
        self.assertEqual(result["profile_id"], profile_id)

        # Phase 3.5 keeps agreeing with the Phase 4.3 gate.
        self.assertEqual(
            visual_profile_lock.validate_visual_profile_lock(
                episode=episode, story_root=self.root)["status"], "pass")
        return episode


class EndToEndCaseTest(EndToEndBase):
    """The six required cases."""

    def test_case1_real_daily_life(self) -> None:
        self.assert_selected_and_produced(REAL_DAILY, M00)

    def test_case2_ancient_ordinary_people(self) -> None:
        episode = self.assert_selected_and_produced(ANCIENT_ORDINARY, M01)
        self.assertIn("era=ancient", self.lock(episode)["selection_evidence"]["matched_rules"])

    def test_case3_heaven_workplace(self) -> None:
        self.assert_selected_and_produced(HEAVEN_WORKPLACE, M02)

    def test_case4_jiangnan_immersive(self) -> None:
        episode = self.assert_selected_and_produced(JIANGNAN_IMMERSIVE, M03)
        self.assertIn("experience_type=immersive_first_person",
                      self.lock(episode)["selection_evidence"]["matched_rules"])

    def test_case5_conflict_needs_confirmation_then_passes(self) -> None:
        episode = self.create("e2e_conflict", selector_input=ANCIENT_JIANGNAN)

        draft = self.lock(episode)
        self.assertEqual(draft["lifecycle_state"], adapter.LIFECYCLE_NEEDS_CONFIRMATION)
        self.assertEqual(draft["profile_id"], "")
        self.assertEqual(sorted(draft["selection"]["candidates"]), sorted([M01, M03]))

        # An unresolved conflict cannot enter production.
        blocked = self.production_gate(episode)
        self.assertEqual(blocked["status"], gate.STATUS_FAIL)
        self.assertEqual(blocked["code"], gate.ERROR_NOT_LOCKED)

        # The confirmation has to name one of the candidates; it is never guessed.
        with self.assertRaises(SystemExit) as ctx:
            self.confirm(episode)
        self.assertEqual(getattr(ctx.exception, "code", None), lifecycle.ERROR_PROFILE_REQUIRED)

        with self.assertRaises(SystemExit) as ctx:
            self.confirm(episode, profile_id=M02)
        self.assertEqual(getattr(ctx.exception, "code", None), lifecycle.ERROR_PROFILE_REQUIRED)

        report = self.confirm(episode, profile_id=M01)
        self.assertEqual(report["to"], adapter.LIFECYCLE_LOCKED)

        locked = self.lock(episode)
        self.assertEqual(locked["profile_id"], M01)
        self.assertEqual(locked["status"], "selected")
        self.assertEqual(locked["selection"]["adjudication"]["resolved_profile_id"], M01)

        result = self.production_gate(episode)
        self.assertEqual(result["status"], gate.STATUS_PASS, result)

    def test_case5_conflict_can_resolve_to_the_other_candidate(self) -> None:
        episode = self.create("e2e_conflict_m03", selector_input=ANCIENT_JIANGNAN)
        report = self.confirm(episode, profile_id=M03)
        self.assertEqual(report["to"], adapter.LIFECYCLE_LOCKED)
        self.assertEqual(self.lock(episode)["profile_id"], M03)
        self.assertEqual(self.production_gate(episode)["status"], gate.STATUS_PASS)

    def test_case6_frozen_lock_cannot_be_modified(self) -> None:
        episode = self.assert_selected_and_produced(REAL_DAILY, M00)
        frozen = self.freeze(episode)
        self.assertEqual(frozen["from"], adapter.LIFECYCLE_LOCKED)
        self.assertEqual(frozen["to"], adapter.LIFECYCLE_FROZEN)

        lock = self.lock(episode)
        self.assertEqual(lock["lifecycle_state"], adapter.LIFECYCLE_FROZEN)
        self.assertEqual(lock["confirmation"], {
            "mode": "human", "confirmed_by": "yeqian", "confirmed_at": AT, "reason": "reviewed"})
        self.assertEqual(lock["frozen"]["inherits_confirmation_by"], "yeqian")

        self.assertEqual(self.production_gate(episode)["status"], gate.STATUS_PASS)
        self.assertEqual(self.production_gate(episode, stage="release")["status"], gate.STATUS_PASS)

        before = self.lock_path(episode).read_bytes()
        for attempt in (
            lambda: self.freeze(episode),
            lambda: self.confirm(episode),
            lambda: lifecycle.transition_lock_state(episode, adapter.LIFECYCLE_LOCKED,
                                                    profile_id=M01, actor="x",
                                                    story_root=self.root),
        ):
            with self.assertRaises(SystemExit) as ctx:
                attempt()
            self.assertEqual(getattr(ctx.exception, "code", None), lifecycle.ERROR_ALREADY_FROZEN)
        self.assertEqual(self.lock_path(episode).read_bytes(), before,
                         "a frozen Visual Lock must not be rewritten")


class LifecycleRuleTest(EndToEndBase):
    """The Phase 4.2 state machine, independent of Episode creation."""

    def test_transition_table(self) -> None:
        allowed = [
            (adapter.LIFECYCLE_SELECTED, adapter.LIFECYCLE_LOCKED),
            (adapter.LIFECYCLE_NEEDS_CONFIRMATION, adapter.LIFECYCLE_LOCKED),
            (adapter.LIFECYCLE_LOCKED, adapter.LIFECYCLE_FROZEN),
        ]
        for current, target in allowed:
            self.assertTrue(lifecycle.validate_transition(current, target)["ok"], (current, target))

        forbidden = [
            (adapter.LIFECYCLE_DRAFT, adapter.LIFECYCLE_LOCKED),
            (adapter.LIFECYCLE_NEEDS_CONFIRMATION, adapter.LIFECYCLE_FROZEN),
            (adapter.LIFECYCLE_SELECTED, adapter.LIFECYCLE_FROZEN),
        ]
        for current, target in forbidden:
            verdict = lifecycle.validate_transition(current, target)
            self.assertFalse(verdict["ok"], (current, target))
            self.assertEqual(verdict["code"], lifecycle.ERROR_INVALID_TRANSITION, (current, target))

        for target in adapter.LIFECYCLE_STATES:
            verdict = lifecycle.validate_transition(adapter.LIFECYCLE_FROZEN, target)
            self.assertEqual(verdict["code"], lifecycle.ERROR_ALREADY_FROZEN, target)

    def test_release_stage_requires_frozen(self) -> None:
        episode = self.assert_selected_and_produced(REAL_DAILY, M00)
        blocked = self.production_gate(episode, stage="release")
        self.assertEqual(blocked["status"], gate.STATUS_FAIL)
        self.assertEqual(blocked["code"], gate.ERROR_NOT_FROZEN)

        self.freeze(episode)
        self.assertEqual(self.production_gate(episode, stage="release")["status"], gate.STATUS_PASS)
        self.assertEqual(self.production_gate(episode, stage="PUBLISH_READY")["status"],
                         gate.STATUS_PASS)

    def test_confirmation_requires_a_named_actor(self) -> None:
        episode = self.create("e2e_no_actor", selector_input=REAL_DAILY)
        with self.assertRaises(SystemExit) as ctx:
            lifecycle.confirm_visual_lock(episode, confirmed_by="", story_root=self.root)
        self.assertEqual(getattr(ctx.exception, "code", None),
                         lifecycle.ERROR_CONFIRMATION_INVALID)
        self.assertEqual(self.lock(episode)["lifecycle_state"], adapter.LIFECYCLE_SELECTED,
                         "a refused confirmation must not be written")

    def test_missing_lock_is_reported_not_invented(self) -> None:
        episode = self.root / "episodes" / "no_lock"
        (episode / "meta").mkdir(parents=True)
        with self.assertRaises(SystemExit) as ctx:
            lifecycle.confirm_visual_lock(episode, confirmed_by="yeqian", story_root=self.root)
        self.assertEqual(getattr(ctx.exception, "code", None), lifecycle.ERROR_NOT_FOUND)
        self.assertFalse(self.lock_path(episode).exists())


class GateBoundaryTest(EndToEndBase):
    """The gate is read-only, opt-in, and never retroactively fails history."""

    def test_legacy_episode_is_not_blocked(self) -> None:
        episode = self.root / "episodes" / "legacy_episode"
        (episode / "meta").mkdir(parents=True)
        result = self.production_gate(episode)
        self.assertEqual(result["status"], gate.STATUS_LEGACY)
        self.assertTrue(result["ok"])
        self.assertFalse(result["required"])
        self.assertEqual(gate.verify_visual_profile_for_production(
            episode, story_root=self.root), [])

        (episode / "meta/visual-profile.json").write_text(json.dumps({
            "profile_id": "M00", "profile_path": "standards/visual_profiles/profiles/M00.json",
            "tool_version": "2.2.4", "lock_status": "locked", "mode": "explicit_user_locked",
        }, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
        result = gate.validate_visual_profile_for_production(episode=episode, story_root=self.root)
        self.assertEqual(result["status"], gate.STATUS_LEGACY)
        self.assertTrue(result["ok"])

    def test_opted_in_episode_without_lock_is_a_failure(self) -> None:
        episode = self.root / "episodes" / "opted_in"
        (episode / "meta").mkdir(parents=True)
        (episode / "meta/runtime-request.json").write_text(json.dumps({
            "visual_profile_selection": {"source": "selector", "status": "selected"},
        }, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
        result = self.production_gate(episode)
        self.assertEqual(result["status"], gate.STATUS_FAIL)
        self.assertEqual(result["code"], gate.ERROR_LOCK_MISSING)

    def test_gate_is_read_only(self) -> None:
        episode = self.assert_selected_and_produced(ANCIENT_ORDINARY, M01)
        path = self.lock_path(episode)
        before = path.read_bytes()
        self.production_gate(episode)
        self.production_gate(episode, stage="release")
        gate.verify_visual_profile_for_production(episode, story_root=self.root)
        self.assertEqual(path.read_bytes(), before)

    def test_only_the_lock_file_is_ever_written(self) -> None:
        def snapshot() -> set:
            return {p.relative_to(self.root).as_posix() for p in self.root.rglob("*")}

        before = snapshot()
        episode = self.create("e2e_scoped", selector_input=REAL_DAILY)
        self.confirm(episode)
        self.freeze(episode)
        added = snapshot() - before
        self.assertEqual(added, {
            "episodes", "episodes/e2e_scoped", "episodes/e2e_scoped/meta",
            "episodes/e2e_scoped/meta/episode-state.json",
            "episodes/e2e_scoped/meta/visual-profile.json",
            "episodes/e2e_scoped/meta/runtime-request.json",
        })
        self.assertEqual(episode.parent, self.root / "episodes")
        self.assertFalse((self.root / "runtime").exists(), "no Runtime file may be touched")
        self.assertFalse((self.root / "meta").exists(), "the repository episode-state must not be touched")


if __name__ == "__main__":
    unittest.main()
