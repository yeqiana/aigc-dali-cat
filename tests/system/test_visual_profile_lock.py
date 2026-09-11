#!/usr/bin/env python3
"""Phase 3.5 Visual Profile Selection Evidence Gate tests.

Phase 3.3 let the Selector pick a Visual Profile and emit evidence; Phase 3.4
fixed the record shape. These tests lock the gate that verifies the record:

  Case1: legal M00 Visual Lock                                             -> PASS
  Case2: profile_id not registered                                         -> FAIL
  Case3: profile_path does not match the registry                          -> FAIL
  Case4: selection_evidence missing / malformed                            -> FAIL
  Case5: selection needs_confirmation (never adjudicated)                   -> FAIL
  Case6: historical Episode without a Visual Lock                          -> PASS legacy
  Case7: M02 fictional_world profile                                       -> PASS
  Case8: every result carries an explicit error code

The gate verifies that a selection fact exists and is self-consistent. It does
not re-run the Selector, does not re-pick a profile, does not repair a lock and
does not write anything.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import visual_profile_lock  # noqa: E402
import visual_profile_registry as registry  # noqa: E402

DIGEST = "sha256:" + "a" * 64
CODES = set(visual_profile_lock.ERROR_CODES)


def evidence(**overrides) -> dict:
    data = {
        "selector_version": "1.0",
        "inputs_digest": DIGEST,
        "matched_rules": ["world=real"],
        "reason": ["prio=semantic"],
        "source": "rule_engine",
    }
    data.update(overrides)
    return data


def lock_for(profile_id: str = "M00", **overrides) -> dict:
    declared = overrides.pop("profile_path", None)
    entry = registry.registry_entry(profile_id)
    if declared is None:
        declared = entry["path"] if entry else f"standards/visual_profiles/profiles/{profile_id}.json"
    lock = {
        "schema_version": 1,
        "profile_id": profile_id,
        "profile_path": declared,
        "selection": "selected",
        "selection_evidence": evidence(),
        "confirmed_by": "yeqian",
        "confirmed_at": "2026-09-11T00:00:00+08:00",
        "confirmation_mode": "human",
    }
    lock.update(overrides)
    return lock


def legacy_meta_lock(profile_id: str = "SPIRITED_AWAY_LIVE_ACTION_V1") -> dict:
    """Pre-governance V2.2.4 meta/visual-profile.json shape (see 12_qianxun)."""
    return {
        "schema_version": 1,
        "tool_version": "2.2.6",
        "episode_id": "99-01",
        "lock_status": "locked",
        "profile_id": profile_id,
        "profile_path": "standards/visual_profiles/SPIRITED_AWAY_LIVE_ACTION_V1.json",
        "mode": "explicit_user_locked",
        "override_reason": "episode explicit lock",
        "locked_at": "2026-09-01T22:01:58+08:00",
    }


class VisualProfileLockGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="visual-profile-lock-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    # ---- fixtures -------------------------------------------------------
    def episode(self, name: str = "99_lock_ep") -> Path:
        ep = self.tmp / "episodes" / name
        (ep / "meta").mkdir(parents=True, exist_ok=True)
        return ep

    def write_json(self, path: Path, data) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def temp_repo(self, profiles, files=(), with_registry: bool = True) -> Path:
        root = self.tmp / "repo"
        (root / "standards/visual_profiles/profiles").mkdir(parents=True, exist_ok=True)
        if with_registry:
            self.write_json(root / "standards/visual_profiles/index.json", {
                "schema_version": 2,
                "default_profile": profiles[0]["id"],
                "profiles": list(profiles),
            })
        for rel in files:
            self.write_json(root / rel, {})
        return root

    # ---- Case 1 --------------------------------------------------------
    def test_case1_legal_m00_lock_passes(self) -> None:
        result = visual_profile_lock.validate_visual_profile_lock(lock_for("M00"))
        self.assertEqual(result["status"], "pass", result)
        self.assertIsNone(result["code"])
        self.assertEqual(result["profile_id"], "M00")
        self.assertTrue(result["governed"])
        self.assertEqual({check["name"]: check["status"] for check in result["checks"]}, {
            "profile_registered": "pass",
            "profile_path_matches_registry": "pass",
            "selection_evidence_present": "pass",
            "selection_adjudicated": "pass",
            "confirmation_recorded": "pass",
            "lock_shape": "pass",
        })
        self.assertEqual(result["errors"], [])

    # ---- Case 2 --------------------------------------------------------
    def test_case2_unregistered_profile_id_fails(self) -> None:
        # A deprecated alias is recorded in the registry but is deliberately not
        # a registered profile id, so it must fail closed.
        self.assertIsNotNone(registry.alias_entry("M00_ANCIENT_DAILY_LIFE_V1"))
        self.assertIsNone(registry.registry_entry("M00_ANCIENT_DAILY_LIFE_V1"))
        lock = lock_for("M00_ANCIENT_DAILY_LIFE_V1",
                        profile_path="standards/visual_profiles/profiles/M01_ANCIENT_MUNDANE_LIFE_V1.json")
        result = visual_profile_lock.validate_visual_profile_lock(lock)
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["code"], "VISUAL_PROFILE_NOT_REGISTERED")

    # ---- Case 3 --------------------------------------------------------
    def test_case3_profile_path_drift_fails(self) -> None:
        lock = lock_for("M00", profile_path="standards/visual_profiles/M00_MP4_other.json")
        result = visual_profile_lock.validate_visual_profile_lock(lock)
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["code"], "VISUAL_PROFILE_PATH_MISMATCH")
        self.assertIn("does not match the registry path", result["errors"][0]["detail"])

    def test_registered_path_without_file_fails(self) -> None:
        root = self.temp_repo(
            profiles=[{"id": "M90", "path": "standards/visual_profiles/profiles/M90.json", "status": "active"}],
        )
        lock = {"schema_version": 1, "profile_id": "M90",
                "profile_path": "standards/visual_profiles/profiles/M90.json",
                "selection_evidence": evidence()}
        result = visual_profile_lock.validate_visual_profile_lock(lock, story_root=root)
        self.assertEqual(result["code"], "VISUAL_PROFILE_FILE_MISSING")

    def test_registered_but_inactive_profile_fails(self) -> None:
        root = self.temp_repo(
            profiles=[{"id": "M98", "path": "standards/visual_profiles/profiles/M98.json", "status": "deprecated"}],
            files=["standards/visual_profiles/profiles/M98.json"],
        )
        lock = {"schema_version": 1, "profile_id": "M98",
                "profile_path": "standards/visual_profiles/profiles/M98.json",
                "selection_evidence": evidence()}
        result = visual_profile_lock.validate_visual_profile_lock(lock, story_root=root)
        self.assertEqual(result["code"], "VISUAL_PROFILE_NOT_ACTIVE")

    def test_missing_registry_is_reported_with_its_own_code(self) -> None:
        root = self.temp_repo(profiles=[{"id": "M00", "path": "x.json", "status": "active"}],
                              with_registry=False)
        result = visual_profile_lock.validate_visual_profile_lock(lock_for("M00"), story_root=root)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(result["code"].startswith("VISUAL_PROFILE_REGISTRY_"))

    # ---- Case 4 --------------------------------------------------------
    def test_case4_selection_evidence_missing_fails(self) -> None:
        cases = {}
        cases["absent"] = lock_for("M00", selection_evidence=None)
        cases["empty"] = lock_for("M00", selection_evidence={})
        partial = lock_for("M00")
        partial["selection_evidence"].pop("inputs_digest")
        cases["field missing"] = partial
        cases["bad digest"] = lock_for("M00", selection_evidence=evidence(inputs_digest="0.87"))
        cases["empty reason"] = lock_for("M00", selection_evidence=evidence(reason=[]))
        cases["rules not strings"] = lock_for("M00", selection_evidence=evidence(matched_rules=[1, 2]))
        for name, lock in cases.items():
            result = visual_profile_lock.validate_visual_profile_lock(lock)
            self.assertEqual(result["status"], "fail", name)
            self.assertEqual(result["code"], "VISUAL_PROFILE_SELECTION_EVIDENCE_MISSING", name)

    def test_defaulted_selection_without_matched_rules_still_passes(self) -> None:
        # defaulted is a legal outcome: no rule matched, but the reason is recorded.
        lock = lock_for("M00", selection="defaulted",
                        selection_evidence=evidence(matched_rules=[], reason=["no_rule_matched"]))
        result = visual_profile_lock.validate_visual_profile_lock(lock)
        self.assertEqual(result["status"], "pass", result)

    # ---- Case 5 --------------------------------------------------------
    def test_case5_needs_confirmation_fails(self) -> None:
        variants = {
            "selection string": lock_for("M00", selection="needs_confirmation"),
            "status string": lock_for("M00", status="needs_confirmation"),
        }
        nested = lock_for("M00")
        nested["selection"] = {"status": "needs_confirmation", "candidates": ["M01", "M03"]}
        variants["nested selection"] = nested
        variants["rejected"] = lock_for("M00", selection="rejected")
        for name, lock in variants.items():
            result = visual_profile_lock.validate_visual_profile_lock(lock)
            self.assertEqual(result["status"], "fail", name)
            self.assertEqual(result["code"], "VISUAL_PROFILE_NOT_CONFIRMED", name)

    def test_unknown_selection_status_is_invalid(self) -> None:
        result = visual_profile_lock.validate_visual_profile_lock(lock_for("M00", selection="probably"))
        self.assertEqual(result["code"], "VISUAL_PROFILE_LOCK_INVALID")

    # ---- Case 6 --------------------------------------------------------
    def test_case6_history_without_governance_is_not_judged(self) -> None:
        bare = self.episode("99_history")
        result = visual_profile_lock.validate_visual_profile_lock(episode=bare)
        self.assertEqual(result["status"], "legacy_unmanaged")
        self.assertIsNone(result["code"])
        self.assertFalse(result["required"])
        self.assertFalse(result["judged"])
        self.assertEqual(result["errors"], [])

        # A pre-governance V2.2.4 episode meta lock is history, not evidence, and
        # is never failed retroactively - not even when its id is unknown today.
        for profile_id in ("SPIRITED_AWAY_LIVE_ACTION_V1", "NOT_A_REGISTERED_PROFILE"):
            ep = self.episode("99_history_" + profile_id[:6])
            self.write_json(ep / "meta/visual-profile.json", legacy_meta_lock(profile_id))
            result = visual_profile_lock.validate_visual_profile_lock(episode=ep)
            self.assertEqual(result["status"], "legacy_unmanaged", profile_id)
            self.assertIsNone(result["code"], profile_id)
        self.assertEqual(visual_profile_lock.verify(ROOT / "episodes/12_千寻/01_那条不存在的隧道"), [])

    # ---- Case 7 --------------------------------------------------------
    def test_case7_m02_fictional_world_lock_passes(self) -> None:
        document = registry.load_profile_document("M02_HEAVEN_MUNDANE_WORKER_V1")
        self.assertEqual(document.get("reality_basis"), "fictional_world_mundane")
        lock = lock_for("M02_HEAVEN_MUNDANE_WORKER_V1")
        self.assertIn("M02_HEAVEN_MUNDANE_WORKER_V1", lock["profile_path"])
        result = visual_profile_lock.validate_visual_profile_lock(lock)
        self.assertEqual(result["status"], "pass", result)
        self.assertIsNone(result["code"])

    # ---- Case 8 --------------------------------------------------------
    def test_case8_every_result_carries_an_explicit_code(self) -> None:
        root = self.temp_repo(
            profiles=[
                {"id": "M00", "path": "standards/visual_profiles/profiles/M00.json", "status": "active"},
                {"id": "M90", "path": "standards/visual_profiles/profiles/M90.json", "status": "active"},
                {"id": "M98", "path": "standards/visual_profiles/profiles/M98.json", "status": "deprecated"},
            ],
            files=["standards/visual_profiles/profiles/M00.json"],
        )
        temp_m00 = "standards/visual_profiles/profiles/M00.json"
        failing = [
            lock_for("M99", profile_path="standards/visual_profiles/profiles/M99.json"),
            lock_for("M98", profile_path="standards/visual_profiles/profiles/M98.json"),
            lock_for("M00", profile_path="standards/visual_profiles/elsewhere.json"),
            lock_for("M90", profile_path="standards/visual_profiles/profiles/M90.json"),
            lock_for("M00", profile_path=temp_m00, selection_evidence=None),
            lock_for("M00", profile_path=temp_m00, selection="needs_confirmation"),
            lock_for("M00", profile_path=temp_m00, confirmed_by=None),
            lock_for("M00", profile_path=temp_m00, confirmation_mode="bogus"),
        ]
        seen = set()
        for lock in failing:
            result = visual_profile_lock.validate_visual_profile_lock(lock, story_root=root)
            self.assertEqual(result["status"], "fail", lock)
            self.assertIn(result["code"], CODES, result)
            self.assertTrue(result["errors"])
            for error in result["errors"]:
                self.assertIn(error["code"], CODES)
                self.assertTrue(str(error["detail"]).strip())
            seen.add(result["code"])

        opted_in = self.episode("99_declared")
        self.write_json(opted_in / "meta/runtime-request.json", {"visual_profile_selection": evidence()})
        declared = visual_profile_lock.validate_visual_profile_lock(episode=opted_in)
        self.assertEqual(declared["code"], "VISUAL_PROFILE_LOCK_MISSING")
        self.assertTrue(declared["required"])
        seen.add(declared["code"])

        broken = self.episode("99_broken")
        (broken / "meta/visual-profile.json").write_text("{ not json", encoding="utf-8")
        unreadable = visual_profile_lock.validate_visual_profile_lock(episode=broken)
        self.assertEqual(unreadable["code"], "VISUAL_PROFILE_LOCK_UNREADABLE")
        seen.add(unreadable["code"])

        self.assertEqual(seen, CODES)

        for lock in (lock_for("M00"), None):
            result = visual_profile_lock.validate_visual_profile_lock(lock)
            self.assertIn(result["status"], ("pass", "legacy_unmanaged"))
            self.assertIsNone(result["code"])
            self.assertEqual(result["errors"], [])

    # ---- confirmation -------------------------------------------------- #
    def test_confirmation_record_required_for_human_review(self) -> None:
        for overrides in ({"confirmed_by": None}, {"confirmed_at": None},
                          {"confirmed_by": None, "confirmed_at": None},
                          {"confirmed_at": "yesterday"}):
            result = visual_profile_lock.validate_visual_profile_lock(lock_for("M00", **overrides))
            self.assertEqual(result["code"], "VISUAL_PROFILE_CONFIRMATION_MISSING", overrides)

        for overrides in ({"confirmation_mode": "system", "confirmed_by": None, "confirmed_at": None},
                          {"confirmation_mode": "direct_user"},
                          {"confirmation_mode": "delegated_auto"}):
            result = visual_profile_lock.validate_visual_profile_lock(lock_for("M00", **overrides))
            self.assertEqual(result["status"], "pass", (overrides, result))

        # An undeclared confirmation_mode is treated as human review, fail-closed.
        lock = lock_for("M00")
        lock.pop("confirmation_mode")
        self.assertEqual(visual_profile_lock.validate_visual_profile_lock(lock)["status"], "pass")
        lock.pop("confirmed_by")
        self.assertEqual(visual_profile_lock.validate_visual_profile_lock(lock)["code"],
                         "VISUAL_PROFILE_CONFIRMATION_MISSING")

    # ---- gate adapter -------------------------------------------------- #
    def test_verify_adapter_reports_failures_and_honours_metadata_only(self) -> None:
        failing = self.episode("99_verify_fail")
        self.write_json(failing / "meta/visual-profile.json",
                        lock_for("M99", profile_path="standards/visual_profiles/profiles/M99.json"))
        errors = visual_profile_lock.verify(failing)
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("VISUAL_PROFILE_NOT_REGISTERED:"))
        self.assertEqual(visual_profile_lock.verify(failing, metadata_only=True), [])

        passing = self.episode("99_verify_pass")
        self.write_json(passing / "meta/visual-profile.json", lock_for("M00"))
        self.assertEqual(visual_profile_lock.verify(passing), [])

        history = self.episode("99_verify_history")
        self.assertEqual(visual_profile_lock.verify(history), [])

    # ---- contract ------------------------------------------------------- #
    def test_schema_contract_matches_the_documented_lock(self) -> None:
        schema = visual_profile_lock.load_lock_schema()
        self.assertEqual(schema.get("title"), "Story OS Visual Lock")
        self.assertEqual(schema.get("required"),
                         ["schema_version", "profile_id", "profile_path", "selection_evidence"])
        self.assertEqual(registry.validate_json(lock_for("M00"), schema), [])
        incomplete = {"profile_id": "M00"}
        self.assertTrue(registry.validate_json(incomplete, schema))
        no_evidence = lock_for("M00")
        del no_evidence["selection_evidence"]
        self.assertTrue(registry.validate_json(no_evidence, schema))
        bad_digest = lock_for("M00")
        bad_digest["selection_evidence"] = evidence(inputs_digest="87")
        self.assertTrue(registry.validate_json(bad_digest, schema))

    def test_validation_is_read_only_and_deterministic(self) -> None:
        lock = lock_for("M00")
        before = json.dumps(lock, sort_keys=True)
        visual_profile_lock.validate_visual_profile_lock(lock)
        self.assertEqual(json.dumps(lock, sort_keys=True), before)
        first = visual_profile_lock.validate_visual_profile_lock(lock)
        second = visual_profile_lock.validate_visual_profile_lock(lock)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_cli_exit_codes(self) -> None:
        passing = self.episode("99_cli_pass")
        self.write_json(passing / "meta/visual-profile.json", lock_for("M00"))
        failing = self.episode("99_cli_fail")
        self.write_json(failing / "meta/visual-profile.json",
                        lock_for("M99", profile_path="standards/visual_profiles/profiles/M99.json"))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(visual_profile_lock.main(["validate", str(passing)]), 0)
            self.assertEqual(visual_profile_lock.main(["validate", str(failing)]), 1)

    def test_module_self_test(self) -> None:
        visual_profile_lock.self_test()


if __name__ == "__main__":
    unittest.main()
