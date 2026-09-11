#!/usr/bin/env python3
"""Visual Profile Selector tests (Visual Profile Governance Phase 3.3).

The selector turns Story Intent + Episode Context + Audience Expectation into a
registered Visual Profile id plus traceable Selection Evidence, without touching
Runtime, episode state or the machine gate.

Cases locked here:

  Case1: real daily life            -> M00
  Case2: ancient ordinary people    -> M01
  Case3: heaven workplace           -> M02
  Case4: jiangnan immersive         -> M03
  Case5: ancient + jiangnan         -> needs_confirmation
  Case6: unknown forced profile     -> FAIL (rejected)
  Case7: forced registered profile  -> selected
  Case8: every decision emits Evidence
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import visual_profile_registry as registry  # noqa: E402
import visual_profile_selector as selector  # noqa: E402

M00 = selector.M00
M01 = selector.M01
M02 = selector.M02
M03 = selector.M03
DEPRECATED = "M00_ANCIENT_DAILY_LIFE_V1"

EVIDENCE_REQUIRED = (
    "selector_version",
    "source",
    "registry",
    "inputs_digest",
    "inputs_summary",
    "matched_rules",
    "rejected",
    "reason",
)


def run(payload, **kwargs):
    return selector.select(payload, story_root=ROOT, **kwargs)


class SelectorCaseTest(unittest.TestCase):
    """The eight required cases against the real checkout registry."""

    def test_case1_real_daily_life_selects_m00(self) -> None:
        out = run({"story_intent": {"world": "real", "theme": "daily_life"}})
        self.assertEqual(out["status"], "selected")
        self.assertEqual(out["selected_profile"], M00)

    def test_case2_ancient_ordinary_people_selects_m01(self) -> None:
        out = run({"story_intent": {"world": "historical_real", "era": "ancient",
                                    "theme": "ordinary_people"}})
        self.assertEqual(out["status"], "selected")
        self.assertEqual(out["selected_profile"], M01)

    def test_case3_heaven_workplace_selects_m02(self) -> None:
        out = run({"story_intent": {"world": "fictional", "theme": "workplace"},
                   "audience_expectation": {"fantasy_level": "high"}})
        self.assertEqual(out["status"], "selected")
        self.assertEqual(out["selected_profile"], M02)

    def test_case4_jiangnan_immersive_selects_m03(self) -> None:
        out = run({"story_intent": {"world": "real", "location": "江南",
                                    "experience_type": "immersive_first_person"}})
        self.assertEqual(out["status"], "selected")
        self.assertEqual(out["selected_profile"], M03)

    def test_case5_ancient_plus_jiangnan_needs_confirmation(self) -> None:
        out = run({"story_intent": {"world": "historical_real", "era": "ancient",
                                    "theme": "ordinary_people", "location": "江南",
                                    "experience_type": "immersive_first_person"}})
        self.assertEqual(out["status"], "needs_confirmation")
        self.assertIsNone(out["selected_profile"])
        profiles = sorted(c["profile"] for c in out["candidates"])
        self.assertEqual(profiles, sorted([M01, M03]))
        for candidate in out["candidates"]:
            self.assertTrue(candidate["matched_rules"], candidate)

    def test_case6_forced_unknown_profile_fails(self) -> None:
        with self.assertRaises(selector.VisualProfileSelectionError) as ctx:
            run({"user_override": {"forced_profile_id": DEPRECATED}})
        self.assertEqual(ctx.exception.code, selector.ERROR_SELECTION_REJECTED)
        self.assertIn(DEPRECATED, str(ctx.exception))

    def test_case6_forced_unknown_profile_rejected_in_soft_mode(self) -> None:
        out = run({"user_override": {"forced_profile_id": DEPRECATED}}, strict=False)
        self.assertEqual(out["status"], "rejected")
        self.assertIsNone(out["selected_profile"])

    def test_case7_forced_registered_profile_is_selected(self) -> None:
        out = run({"story_intent": {"world": "real", "theme": "daily_life"},
                   "user_override": {"forced_profile_id": M03}})
        self.assertEqual(out["status"], "selected")
        self.assertEqual(out["selected_profile"], M03)
        self.assertIn(f"user_override={M03}", out["evidence"]["matched_rules"])


class SelectorEvidenceContractTest(unittest.TestCase):
    """Case 8: no decision is accepted without traceable evidence."""

    PAYLOADS = (
        {"story_intent": {"world": "real", "theme": "daily_life"}},
        {"story_intent": {"world": "historical_real", "era": "ancient"}},
        {"story_intent": {"world": "fictional"}, "audience_expectation": {"fantasy_level": "high"}},
        {"story_intent": {"world": "real", "location": "江南",
                          "experience_type": "immersive_first_person"}},
        {"story_intent": {"world": "historical_real", "era": "ancient", "location": "江南",
                          "experience_type": "immersive_first_person"}},
        {"story_intent": {"world": ""}},
        {"story_intent": {"world": "real"}, "user_override": {"forced_profile_id": M01}},
    )

    def test_case8_every_decision_emits_evidence(self) -> None:
        for payload in self.PAYLOADS:
            out = run(payload)
            with self.subTest(payload=payload):
                self.assertIn(out["status"], selector.STATUSES)
                evidence = out["evidence"]
                for key in EVIDENCE_REQUIRED:
                    self.assertIn(key, evidence)
                self.assertEqual(evidence["source"], "rule_engine")
                self.assertEqual(evidence["selector_version"], selector.SELECTOR_VERSION)
                self.assertTrue(evidence["inputs_digest"].startswith("sha256:"))
                self.assertTrue(evidence["reason"], "a decision must explain itself")
                self.assertEqual(selector.validate_selector_output(out, ROOT), [])

    def test_evidence_digest_tracks_inputs(self) -> None:
        first = run({"story_intent": {"world": "real"}})
        second = run({"story_intent": {"world": "historical_real", "era": "ancient"}})
        self.assertNotEqual(
            first["evidence"]["inputs_digest"], second["evidence"]["inputs_digest"]
        )

    def test_selector_is_deterministic(self) -> None:
        payload = {"story_intent": {"world": "historical_real", "era": "ancient",
                                    "location": "江南", "experience_type": "immersive_first_person"}}
        self.assertEqual(run(payload), run(payload))

    def test_selector_output_and_evidence_schemas_load(self) -> None:
        for kind in ("input", "output", "evidence"):
            schema = selector.load_selector_schema(kind, ROOT)
            self.assertIsInstance(schema, dict)
            self.assertTrue(schema.get("title"))


class SelectorGovernanceTest(unittest.TestCase):
    """Fail-closed, drift and boundary checks."""

    def test_defaulted_when_no_rule_matches(self) -> None:
        out = run({"story_intent": {"world": ""}})
        self.assertEqual(out["status"], "defaulted")
        self.assertEqual(out["selected_profile"], registry.default_profile_id(ROOT))

    def test_invalid_input_fails_closed(self) -> None:
        with self.assertRaises(selector.VisualProfileSelectionError) as ctx:
            run({"story_intent": {"world": "not-a-world"}})
        self.assertEqual(ctx.exception.code, selector.ERROR_SELECTION_INVALID)
        soft = run({"story_intent": {"world": "not-a-world"}}, strict=False)
        self.assertEqual(soft["status"], "rejected")

    def test_series_lock_beats_semantic_match(self) -> None:
        out = run({"story_intent": {"world": "real", "theme": "daily_life"},
                   "episode_context": {"previous_profile": M01}})
        self.assertEqual(out["status"], "selected")
        self.assertEqual(out["selected_profile"], M01)
        self.assertIn(f"series_lock={M01}", out["evidence"]["matched_rules"])

    def test_unregistered_series_hint_is_ignored_not_fatal(self) -> None:
        out = run({"story_intent": {"world": "real"},
                   "episode_context": {"previous_profile": DEPRECATED}})
        self.assertEqual(out["status"], "selected")
        self.assertEqual(out["selected_profile"], M00)
        self.assertIn(DEPRECATED, " ".join(out["evidence"]["notes"]))

    def test_every_rule_target_is_registered(self) -> None:
        coverage = selector.rule_coverage(ROOT)
        self.assertEqual(coverage["unregistered"], [])
        self.assertEqual(sorted(coverage["registered"]), sorted([M00, M01, M02, M03]))

    def test_selector_never_returns_an_unregistered_profile(self) -> None:
        registered = set(registry.registry_ids(ROOT))
        payloads = list(SelectorEvidenceContractTest.PAYLOADS) + [
            {"story_intent": {"world": "fictional"}, "audience_expectation": {"fantasy_level": "low"}},
            {"story_intent": {"world": "historical_real", "era": "modern"}},
            {"story_intent": {"world": "real", "location": "上海"}},
        ]
        for payload in payloads:
            out = run(payload)
            with self.subTest(payload=payload):
                if out["selected_profile"] is not None:
                    self.assertIn(out["selected_profile"], registered)
                for candidate in out["candidates"]:
                    self.assertIn(candidate["profile"], registered)

    def test_selector_does_not_write_repository_files(self) -> None:
        tracked = [
            ROOT / "standards/visual_profiles/index.json",
            ROOT / "meta/episode-state.json",
            ROOT / "meta/story-gates.json",
        ]
        before = {p: (p.stat().st_mtime_ns if p.is_file() else None) for p in tracked}
        run({"story_intent": {"world": "real", "theme": "daily_life"}})
        run({"story_intent": {"world": "historical_real", "era": "ancient"}})
        after = {p: (p.stat().st_mtime_ns if p.is_file() else None) for p in tracked}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
