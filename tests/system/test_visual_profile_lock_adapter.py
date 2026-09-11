#!/usr/bin/env python3
"""Phase 4.1 Visual Lock Runtime Adapter tests.

Phase 3.3 selects a Visual Profile and emits evidence; Phase 3.5 verifies a
Visual Lock. These tests lock the step in between: Episode creation now sends
Story Intent through the Selector and writes a Visual Lock *draft* to
meta/visual-profile.json, without ever confirming it and without overwriting an
existing lock.

  Case1: create_episode + real daily life        -> M00 SELECTED
  Case2: create_episode + ancient ordinary people -> M01 SELECTED
  Case3: create_episode + heaven workplace       -> M02 SELECTED
  Case4: create_episode + jiangnan immersive     -> M03 SELECTED
  Case5: ancient + jiangnan                      -> NEEDS_CONFIRMATION
  Case6: selector rejected                       -> creation fails, nothing written
  Case7: existing LOCKED visual-profile.json     -> never overwritten
  Case8: every generated lock carries selection evidence

Extra coverage: a draft is explicitly not a lock (it fails the Phase 3.5 gate and
passes it only once a confirmation is recorded), the adapter refuses to write a
LOCKED/FROZEN document, and creation touches nothing outside its own Episode.
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
import visual_profile_lock  # noqa: E402
import visual_profile_lock_adapter as adapter  # noqa: E402
import visual_profile_registry as registry  # noqa: E402
import visual_profile_selector as selector  # noqa: E402

M00 = selector.M00
M01 = selector.M01
M02 = selector.M02
M03 = selector.M03
LEGACY_M00 = "M00"
SPIRITED = "SPIRITED_AWAY_LIVE_ACTION_V1"
DEPRECATED = "M00_ANCIENT_DAILY_LIFE_V1"

JIANNAN = "\u6c5f\u5357"

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

EVIDENCE_REQUIRED = ("selector_version", "source", "inputs_digest", "matched_rules", "reason")


class AdapterBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="visual-lock-adapter-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        shutil.copytree(ROOT / "standards/visual_profiles", self.root / "standards/visual_profiles")

    def create(self, title: str, **kwargs) -> Path:
        return story_creator.create_episode(self.root, title, **kwargs)

    def lock_of(self, episode: Path) -> dict:
        return json.loads((episode / "meta/visual-profile.json").read_text(encoding="utf-8"))

    def request_of(self, episode: Path) -> dict:
        return json.loads((episode / "meta/runtime-request.json").read_text(encoding="utf-8"))

    def profile_path(self, profile_id: str) -> str:
        return registry.registry_entry(profile_id, self.root)["path"]

    def assert_selected(self, intent: dict, profile_id: str, message: str = "") -> dict:
        episode = self.create("选集用例" + profile_id, selector_input=intent)
        lock = self.lock_of(episode)
        self.assertEqual(lock["profile_id"], profile_id, message or lock)
        self.assertEqual(lock["lifecycle_state"], adapter.LIFECYCLE_SELECTED)
        self.assertEqual(lock["profile_path"], self.profile_path(profile_id))
        self.assertIsNone(lock["confirmed_by"])
        self.assertIsNone(lock["confirmed_at"])
        self.assertEqual(lock["confirmation_mode"], adapter.CONFIRMATION_PENDING)
        return lock


class VisualLockAdapterCaseTest(AdapterBase):
    """The eight required cases."""

    # ---- Case 1..4 ------------------------------------------------------
    def test_case1_real_daily_life_selects_m00(self) -> None:
        lock = self.assert_selected(REAL_DAILY, M00)
        self.assertEqual(lock["status"], "selected")
        self.assertEqual(lock["selection"]["source"], "rule_engine")

    def test_case2_ancient_ordinary_selects_m01(self) -> None:
        lock = self.assert_selected(ANCIENT_ORDINARY, M01)
        self.assertIn("era=ancient", lock["selection_evidence"]["matched_rules"])

    def test_case3_heaven_workplace_selects_m02(self) -> None:
        self.assert_selected(HEAVEN_WORKPLACE, M02)

    def test_case4_jiangnan_immersive_selects_m03(self) -> None:
        lock = self.assert_selected(JIANGNAN_IMMERSIVE, M03)
        self.assertIn("experience_type=immersive_first_person",
                      lock["selection_evidence"]["matched_rules"])

    # ---- Case 5 ---------------------------------------------------------
    def test_case5_ancient_plus_jiangnan_needs_confirmation(self) -> None:
        episode = self.create("ambiguous_episode", selector_input=ANCIENT_JIANGNAN)

        # The Episode is still created (bootstrap assets exist)...
        self.assertTrue((episode / "meta/episode-state.json").is_file())
        # ...but no profile may be named without a human decision.
        lock = self.lock_of(episode)
        self.assertEqual(lock["lifecycle_state"], adapter.LIFECYCLE_NEEDS_CONFIRMATION)
        self.assertEqual(lock["status"], "needs_confirmation")
        self.assertEqual(lock["profile_id"], "")
        self.assertEqual(lock["profile_path"], "")
        self.assertEqual(sorted(lock["selection"]["candidates"]), sorted([M01, M03]))
        self.assertEqual(lock["confirmation_mode"], adapter.CONFIRMATION_PENDING)

        request = self.request_of(episode)
        self.assertEqual(request["visual_profile"], "")
        self.assertEqual(request["visual_profile_resolution"]["resolution"], "needs_confirmation")
        self.assertIsNone(request["visual_profile_resolution"]["resolved_profile_id"])
        self.assertEqual(request["visual_profile_selection"]["lifecycle_state"],
                         adapter.LIFECYCLE_NEEDS_CONFIRMATION)

    # ---- Case 6 ---------------------------------------------------------
    def test_case6_rejected_selection_fails_creation(self) -> None:
        with self.assertRaises(SystemExit):
            self.create("rejected_episode", visual_profile=DEPRECATED)
        self.assertFalse((self.root / "episodes").exists(),
                         "a rejected selection must not create an Episode")

    def test_case6_rejected_draft_builder_fails_closed(self) -> None:
        output = selector.select({"user_override": {"forced_profile_id": DEPRECATED}},
                                 story_root=self.root, strict=False)
        self.assertEqual(output["status"], "rejected")
        with self.assertRaises(adapter.VisualProfileLockAdapterError) as ctx:
            adapter.create_visual_lock_draft({}, output, story_root=self.root)
        self.assertEqual(ctx.exception.code, selector.ERROR_SELECTION_REJECTED)

    # ---- Case 7 ---------------------------------------------------------
    def test_case7_existing_locked_lock_is_never_overwritten(self) -> None:
        episode = self.create("locked_episode", selector_input=REAL_DAILY)
        lock_path = episode / "meta/visual-profile.json"
        locked = {
            "schema_version": 1,
            "profile_id": M02,
            "profile_path": self.profile_path(M02),
            "status": "selected",
            "lifecycle_state": adapter.LIFECYCLE_LOCKED,
            "selection_evidence": {
                "selector_version": selector.SELECTOR_VERSION,
                "source": "rule_engine",
                "inputs_digest": "sha256:" + "b" * 64,
                "matched_rules": ["world=fictional", "fantasy_level=high"],
                "reason": ["prio=semantic"],
            },
            "confirmation_mode": "human",
            "confirmed_by": "yeqian",
            "confirmed_at": "2026-09-12T00:00:00+08:00",
        }
        lock_path.write_text(json.dumps(locked, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        before = lock_path.read_bytes()

        again = self.create("locked_episode", selector_input=REAL_DAILY)
        self.assertEqual(again, episode)
        self.assertEqual(lock_path.read_bytes(), before, "an existing Visual Lock must not be rewritten")

        report = adapter.ensure_visual_lock(episode, selector_input=REAL_DAILY, story_root=self.root)
        self.assertEqual(report["source"], "existing")
        self.assertFalse(report["written"])
        self.assertEqual(report["lifecycle_state"], adapter.LIFECYCLE_LOCKED)
        self.assertEqual(report["profile_id"], M02)

        request = self.request_of(episode)
        self.assertEqual(request["visual_profile"], M02)
        self.assertNotIn("visual_profile_selection", request,
                         "an Episode that already has a lock declares no new selection")

    def test_write_refuses_to_overwrite(self) -> None:
        episode = self.create("no_overwrite", selector_input=REAL_DAILY)
        with self.assertRaises(adapter.VisualProfileLockAdapterError) as ctx:
            adapter.write_visual_lock_draft(episode, self.lock_of(episode))
        self.assertEqual(ctx.exception.code, adapter.ERROR_LOCK_EXISTS)

    # ---- Case 8 ---------------------------------------------------------
    def test_case8_every_generated_lock_carries_selection_evidence(self) -> None:
        payloads = [REAL_DAILY, ANCIENT_ORDINARY, HEAVEN_WORKPLACE, JIANGNAN_IMMERSIVE,
                    ANCIENT_JIANGNAN, {}, {"story_intent": {"world": "real"}},
                    {"story_intent": {"world": "fictional"}, "user_override": {"forced_profile_id": M01}}]
        for index, payload in enumerate(payloads):
            with self.subTest(payload=payload):
                episode = self.create(f"evidence_episode_{index}", selector_input=payload)
                lock = self.lock_of(episode)
                evidence = lock["selection_evidence"]
                for key in EVIDENCE_REQUIRED:
                    self.assertIn(key, evidence)
                self.assertEqual(selector.validate_selector_evidence(evidence, self.root), [])
                self.assertTrue(evidence["inputs_digest"].startswith("sha256:"))
                self.assertTrue(evidence["reason"], "a lock must record why the profile was chosen")
                self.assertEqual(lock["status"], lock["selection"]["status"])
                request = self.request_of(episode)
                self.assertEqual(request["visual_profile_selection"]["selection_evidence"], evidence)
                self.assertEqual(request["visual_profile_selection"]["adapter_version"],
                                 adapter.ADAPTER_VERSION)


class VisualLockAdapterBoundaryTest(AdapterBase):
    """A draft is not a lock, and creation stays inside its own Episode."""

    def test_draft_is_not_a_lock_for_the_phase_35_gate(self) -> None:
        episode = self.create("draft_not_lock", selector_input=ANCIENT_ORDINARY)
        result = visual_profile_lock.validate_visual_profile_lock(story_root=self.root, episode=episode)
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["code"], "VISUAL_PROFILE_LOCK_INVALID")
        self.assertIn("pending", result["errors"][0]["detail"])

    def test_confirmed_draft_passes_the_phase_35_gate(self) -> None:
        # Same document, plus the Phase 4.2 confirmation: everything else in the
        # adapter output already satisfies the Visual Lock contract.
        episode = self.create("confirmable", selector_input=ANCIENT_ORDINARY)
        lock_path = episode / "meta/visual-profile.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        lock["confirmation_mode"] = "human"
        lock["confirmed_by"] = "yeqian"
        lock["confirmed_at"] = "2026-09-12T00:00:00+08:00"
        lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        result = visual_profile_lock.validate_visual_profile_lock(story_root=self.root, episode=episode)
        self.assertEqual(result["status"], "pass", result)

    def test_unspecified_intent_defaults_to_registry_default(self) -> None:
        episode = self.create("plain_episode")
        lock = self.lock_of(episode)
        self.assertEqual(lock["profile_id"], registry.default_profile_id(self.root))
        self.assertEqual(lock["profile_id"], LEGACY_M00)
        self.assertEqual(lock["status"], "defaulted")
        self.assertEqual(lock["lifecycle_state"], adapter.LIFECYCLE_SELECTED)
        self.assertEqual(self.request_of(episode)["visual_profile"], LEGACY_M00)

    def test_explicit_registered_profile_is_still_honoured(self) -> None:
        episode = self.create("manual_profile", visual_profile=SPIRITED)
        request = self.request_of(episode)
        self.assertEqual(request["visual_profile"], SPIRITED)
        self.assertEqual(request["visual_profile_resolution"]["registered"], True)
        self.assertEqual(request["visual_profile_resolution"]["fallback"], False)
        lock = self.lock_of(episode)
        self.assertEqual(lock["profile_id"], SPIRITED)
        self.assertEqual(lock["profile_path"], self.profile_path(SPIRITED))

    def test_explicit_legacy_default_records_no_fallback(self) -> None:
        episode = self.create("legacy_default", visual_profile=LEGACY_M00)
        request = self.request_of(episode)
        self.assertEqual(request["visual_profile"], LEGACY_M00)
        resolution = request["visual_profile_resolution"]
        self.assertEqual(resolution["resolved_profile_id"], LEGACY_M00)
        self.assertEqual(resolution["requested_profile_id"], LEGACY_M00)
        self.assertIs(resolution["fallback"], False)

    def test_adapter_refuses_non_writable_lifecycle(self) -> None:
        episode = self.root / "episodes" / "frozen"
        (episode / "meta").mkdir(parents=True)
        for lifecycle in (adapter.LIFECYCLE_DRAFT, adapter.LIFECYCLE_LOCKED, adapter.LIFECYCLE_FROZEN):
            draft = {"schema_version": 1, "lifecycle_state": lifecycle,
                     "selection_evidence": {"selector_version": "1.0"}}
            with self.assertRaises(adapter.VisualProfileLockAdapterError) as ctx:
                adapter.write_visual_lock_draft(episode, draft)
            self.assertEqual(ctx.exception.code, adapter.ERROR_LIFECYCLE_INVALID)

    def test_lifecycle_mapping(self) -> None:
        self.assertEqual(adapter.lifecycle_for_status(selector.STATUS_SELECTED),
                         adapter.LIFECYCLE_SELECTED)
        self.assertEqual(adapter.lifecycle_for_status(selector.STATUS_DEFAULTED),
                         adapter.LIFECYCLE_SELECTED)
        self.assertEqual(adapter.lifecycle_for_status(selector.STATUS_NEEDS_CONFIRMATION),
                         adapter.LIFECYCLE_NEEDS_CONFIRMATION)
        self.assertEqual(adapter.lifecycle_of_lock({"lock_status": "locked"}),
                         adapter.LIFECYCLE_LOCKED)
        self.assertIsNone(adapter.lifecycle_of_lock({"profile_id": "M00", "mode": "x"}))
        self.assertEqual(adapter.LIFECYCLE_STATES,
                         ("DRAFT", "SELECTED", "NEEDS_CONFIRMATION", "LOCKED", "FROZEN"))

    def test_creation_writes_only_inside_its_episode(self) -> None:
        def snapshot() -> set:
            return {p.relative_to(self.root).as_posix() for p in self.root.rglob("*")}

        expected_extra = {
            "episodes", "episodes/scoped_episode", "episodes/scoped_episode/meta",
            "episodes/scoped_episode/meta/episode-state.json",
            "episodes/scoped_episode/meta/visual-profile.json",
            "episodes/scoped_episode/meta/runtime-request.json",
        }
        before = snapshot()
        self.create("scoped_episode", selector_input=REAL_DAILY)
        added = snapshot() - before
        self.assertEqual(added, expected_extra)
        self.assertFalse((self.root / "runtime").exists(), "no Runtime file may be touched")
        self.assertFalse((self.root / "meta").exists(), "the repository episode-state must not be touched")

    def test_runtime_request_keeps_profile_as_a_string(self) -> None:
        episode = self.create("string_field", selector_input=REAL_DAILY)
        request = self.request_of(episode)
        self.assertIsInstance(request["visual_profile"], str)
        self.assertEqual(request["visual_profile"], M00)
        self.assertEqual(request["visual_profile_selection"]["selected_profile"], M00)


if __name__ == "__main__":
    unittest.main()
