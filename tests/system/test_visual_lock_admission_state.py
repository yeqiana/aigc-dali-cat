#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))

import visual_lock_admission_state as admission_state  # noqa: E402
import visual_lock_candidate_pool as candidate_pool  # noqa: E402
import visual_lock_v21  # noqa: E402


CHECKS = ("visual_profile_match", "reality_first")


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _asset(sha: str = "a" * 64, fc: str = "b" * 64) -> dict:
    return {
        "id": "V-A",
        "role": "first_major_anomaly",
        "frame": 5,
        "sha256": sha,
        "frame_contract_sha256": fc,
    }


def _pass_row() -> dict:
    return {
        "id": "V-A",
        "frame": 5,
        "role": "first_major_anomaly",
        "checks": {key: True for key in CHECKS},
        "issues": [],
        "notes": "actual pixel pass",
    }


class VisualLockAdmissionStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ep = Path(self.tmp.name)
        (self.ep / "meta").mkdir(parents=True, exist_ok=True)
        self.profile_path = self.ep / "profile.json"
        self.profile_path.write_text('{"profile":"test"}', encoding="utf-8")
        self.profile_sha = hashlib.sha256(self.profile_path.read_bytes()).hexdigest()
        _write(self.ep / "meta/visual-profile.json", {"profile_path": str(self.profile_path)})
        _write(self.ep / "meta/episode-state.json", {"tool_version": "2.6.1"})

    def tearDown(self):
        self.tmp.cleanup()

    def test_sha_bound_pass_is_reused_until_binding_changes(self):
        asset = _asset()
        admission_state.record_rows(
            self.ep,
            rows=[_pass_row()],
            assets=[asset],
            profile_sha256=self.profile_sha,
            story_os_version="2.6.1",
            required_checks=CHECKS,
            provenance={"log": "critic.jsonl"},
            attempt=5,
        )
        self.assertEqual(
            admission_state.dirty_assets(
                self.ep, [asset], profile_sha256=self.profile_sha, story_os_version="2.6.1"
            ),
            [],
        )
        changed = _asset(sha="d" * 64)
        self.assertEqual(
            admission_state.dirty_assets(
                self.ep, [changed], profile_sha256=self.profile_sha, story_os_version="2.6.1"
            ),
            [changed],
        )

    def test_candidate_pool_ignores_latest_stochastic_fail_when_bound_pass_is_valid(self):
        asset = _asset()
        admission_state.record_rows(
            self.ep,
            rows=[_pass_row()],
            assets=[asset],
            profile_sha256=self.profile_sha,
            story_os_version="2.6.1",
            required_checks=CHECKS,
            provenance={"log": "critic.jsonl"},
            attempt=5,
        )
        _write(self.ep / "meta/story-gates.json", {
            "visual": {"calibration": {"items": [{
                "id": "V-A", "role": "first_major_anomaly", "frame": 5,
                "sha256": asset["sha256"],
                "frame_contract_sha256": asset["frame_contract_sha256"],
                "decision": "failed",
            }]}}
        })
        _write(self.ep / "meta/visual-profile-review.json", {
            "calibration": [{
                "id": "V-A", "frame": 5, "role": "first_major_anomaly",
                "checks": {"visual_profile_match": False},
                "issues": ["STOCHASTIC_REREVIEW_FAIL"],
            }]
        })
        self.assertEqual(candidate_pool.failed_rows(self.ep), [])
        self.profile_path.write_text('{"profile":"changed"}', encoding="utf-8")
        self.assertEqual([row["frame"] for row in candidate_pool.failed_rows(self.ep)], [5])

    def test_dirty_detection_treats_stale_frame_contract_as_dirty_instead_of_crashing(self):
        metadata = [_asset(fc="old-contract")]
        with patch.object(
            visual_lock_v21,
            "calibration_assets",
            side_effect=[ValueError("first_major_anomaly frame contract stale"), metadata],
        ), patch.object(
            visual_lock_v21.frame_contract,
            "compile_frame",
            return_value={"contract_sha256": "new-contract"},
        ):
            rows = visual_lock_v21._dirty_detection_assets(self.ep)
        self.assertEqual(rows[0]["frame_contract_sha256"], "new-contract")
        self.assertTrue(rows[0]["binding_stale_for_review"])

    def test_stale_generation_binding_targets_only_candidate_generated_under_old_contract(self):
        _write(self.ep / "meta/story-gates.json", {
            "visual": {"calibration": {"items": [
                {"id": "V-A", "role": "first_major_anomaly", "frame": 5},
                {"id": "V-B", "role": "worst_capture_condition", "frame": 16},
            ]}}
        })
        _write(self.ep / "meta/production-ledger.json", {"frames": {
            "05": {
                "current_candidate": {"sha256": "5" * 64, "path": "five.png"},
                "attempts": [{"candidate": {"sha256": "5" * 64}, "request": {"frame_contract": {"contract_sha256": "current-05"}}}],
            },
            "16": {
                "current_candidate": {"sha256": "6" * 64, "path": "sixteen.png"},
                "attempts": [{"candidate": {"sha256": "6" * 64}, "request": {"frame_contract": {"contract_sha256": "old-16"}}}],
            },
        }})

        def verify(_ep, frame, recorded):
            return ["frame 16 generation frame_contract_sha256 stale"] if int(frame) == 16 else []

        with patch.object(visual_lock_v21.frame_contract, "required", return_value=True), \
                patch.object(visual_lock_v21.frame_contract, "verify_recorded_provenance", side_effect=verify), \
                patch.object(visual_lock_v21.frame_contract, "compile_frame", return_value={"contract_sha256": "current-16"}):
            rows = visual_lock_v21.stale_generation_bindings(self.ep)
        self.assertEqual([row["frame"] for row in rows], [16])
        self.assertEqual(rows[0]["recorded_frame_contract_sha256"], "old-16")
        self.assertEqual(rows[0]["current_frame_contract_sha256"], "current-16")

    def test_candidate_prompt_keeps_first_major_anomaly_readable(self):
        row = {
            "frame": 5,
            "role": "first_major_anomaly",
            "checks": {"anomaly_scale_delivery": False},
            "issues": ["ANOMALY_NOT_READABLE"],
        }
        with patch.object(candidate_pool, "_row_for_frame", return_value=row):
            prompt = candidate_pool.candidate_prompt(self.ep, 5, 1)
        self.assertIn("异常必须", prompt)
        self.assertIn("清楚", prompt)
        self.assertNotIn("远景被屋檐/行人/水汽遮挡", prompt)
        self.assertLessEqual(len(prompt), 245)
        self.assertLessEqual(len(prompt.encode("utf-8")), 850)

    def test_first_major_anomaly_prefers_locked_story_semantics_over_preimage_hint(self):
        rows = [
            {"frame": 3, "mode": "anomaly_reveal", "impact": 2, "anomaly_logic_stage": "ordinary"},
            {"frame": 6, "mode": "normal_record", "impact": 1, "anomaly_logic_stage": "discovery"},
            {"frame": 7, "mode": "anomaly_reveal", "impact": 2, "anomaly_logic_stage": "confirmation"},
        ]
        selected = visual_lock_v21._semantic_first_anomaly_candidates(rows)
        self.assertEqual([row["frame"] for row in selected], [6, 7])

    def test_reprepare_preserves_same_contract_baseline_but_resets_changed_role(self):
        old = {"visual": {"calibration": {"items": [
            {"id": "V-B", "role": "ordinary_baseline", "frame": 1, "asset_path": "old.png", "sha256": "pixel", "decision": "passed", "frame_contract_sha256": "same", "note": "keep"},
            {"id": "V-A", "role": "first_major_anomaly", "frame": 3, "asset_path": "bad.png", "sha256": "bad", "decision": "failed", "frame_contract_sha256": "old", "note": "old"},
        ]}}}
        plan = {"items": [
            {"id": "V-B", "role": "ordinary_baseline", "frame": 1, "contract_sha256": "same"},
            {"id": "V-A", "role": "first_major_anomaly", "frame": 6, "contract_sha256": "new"},
        ]}
        with tempfile.TemporaryDirectory() as td:
            ep = Path(td)
            (ep / "meta").mkdir(parents=True)
            (ep / "meta/story-gates.json").write_text(json.dumps(old), encoding="utf-8")
            with patch.object(visual_lock_v21, "choose_plan", return_value=plan):
                visual_lock_v21.prepare(ep)
            items = json.loads((ep / "meta/story-gates.json").read_text(encoding="utf-8"))["visual"]["calibration"]["items"]
        self.assertEqual(items[0]["decision"], "passed")
        self.assertEqual(items[0]["asset_path"], "old.png")
        self.assertEqual(items[1]["frame"], 6)
        self.assertEqual(items[1]["decision"], "pending")
        self.assertIsNone(items[1]["asset_path"])

    def test_candidate_prompt_carries_concrete_frame_contract_pixel_evidence(self):
        row = {
            "frame": 5,
            "role": "first_major_anomaly",
            "checks": {"anomaly_scale_delivery": False},
            "issues": ["ANOMALY_NOT_READABLE"],
        }
        contract = {
            "hash_material": {
                "frame_directive": {
                    "required_visual_cues": [
                        "dust-covered furniture",
                        "clean enamel tea mug containing fresh water",
                    ]
                },
                "capture_event": {
                    "retained_reason": "家具全盖着布，只有茶缸是干净有水的"
                },
            }
        }
        with patch.object(candidate_pool, "_row_for_frame", return_value=row), \
                patch.object(candidate_pool.frame_contract, "compile_frame", return_value=contract):
            prompt = candidate_pool.candidate_prompt(self.ep, 5, 1)
        self.assertIn("dust-covered furniture", prompt)
        self.assertIn("clean enamel tea mug", prompt)
        self.assertIn("茶缸是干净有水", prompt)
        self.assertLessEqual(len(prompt), 245)
        self.assertLessEqual(len(prompt.encode("utf-8")), 850)

    def test_candidate_prompt_slot2_hard_fits_local_prompt_budget(self):
        row = {
            "frame": 5,
            "role": "first_major_anomaly",
            "checks": {"anomaly_scale_delivery": False, "reality_first": False},
            "issues": ["ANOMALY_NOT_READABLE", "MOMENT_CAPTURE_CREDIBILITY"],
        }
        contract = {
            "hash_material": {
                "frame_directive": {
                    "required_visual_cues": [
                        "dust-covered furniture across the entire abandoned room",
                        "clean enamel tea mug containing visibly fresh water",
                    ]
                },
                "capture_event": {
                    "retained_reason": "家具全部积灰，只有搪瓷茶缸干净且装着新鲜水，这个反差必须在同一画面直接可读"
                },
            }
        }
        with patch.object(candidate_pool, "_row_for_frame", return_value=row), \
                patch.object(candidate_pool.frame_contract, "compile_frame", return_value=contract):
            prompt = candidate_pool.candidate_prompt(self.ep, 5, 2)
        self.assertLessEqual(len(prompt), 245)
        self.assertLessEqual(len(prompt.encode("utf-8")), 850)
        self.assertIn("dust-covered furniture", prompt)
        self.assertIn("clean enamel tea mug", prompt)

    def test_prompt_budget_begin_rejection_is_recompilable_only_for_current_policy_candidate(self):
        item = {
            "kind": "baseline_candidate",
            "status": "blocked",
            "capture_id": f"visual-lock-candidate-{candidate_pool.CANDIDATE_POLICY_REVISION}-03-02",
            "attempts": 0,
            "output_path": None,
            "last_error": "prompt budget exceeded: 268 chars/560 bytes; limit=260 chars/900 bytes",
            "execution": {"phase": "BEGIN_REJECTED"},
        }
        self.assertTrue(candidate_pool.recompilable_prompt_blocked_item(item))
        self.assertFalse(candidate_pool.recompilable_prompt_blocked_item({**item, "attempts": 1}))
        self.assertFalse(candidate_pool.recompilable_prompt_blocked_item({**item, "capture_id": "visual-lock-candidate-v1-03-02"}))

    def test_candidate_capacity_is_bounded_per_explicit_policy_revision(self):
        frame = 5
        legacy = {
            "frame": frame,
            "kind": "baseline_candidate",
            "capture_id": "visual-lock-candidate-05-01",
            "status": "superseded",
            "output_path": "legacy.png",
        }
        current = {
            "frame": frame,
            "kind": "baseline_candidate",
            "capture_id": f"visual-lock-candidate-{candidate_pool.CANDIDATE_POLICY_REVISION}-05-01",
            "status": "generated",
            "output_path": "current.png",
        }
        _write(self.ep / "meta/production-queue.json", {"items": [legacy, current]})
        self.assertEqual(candidate_pool.historical_successful_slots(self.ep, frame), 2)
        self.assertEqual(candidate_pool.successful_slots(self.ep, frame), 1)

    def test_weak_pass_counts_only_successful_content_outputs_not_technical_failures(self):
        frame = 5
        sha = "c" * 64
        fc = "d" * 64
        _write(self.ep / "meta/production-ledger.json", {"frames": {"05": {
            "status": "NEEDS_USER",
            "current_candidate": {"sha256": sha},
            "attempts": [
                {"result": "success"},
                {"result": "technical_failure"},
                {"result": "success"},
                {"result": "technical_failure"},
                {"result": "success"},
                {"result": "success"},
            ],
        }}})
        _write(self.ep / "meta/visual-profile-review.json", {"calibration": [{
            "id": "V-A", "frame": frame, "role": "first_major_anomaly",
            "sha256": sha, "frame_contract_sha256": fc,
            "checks": {"anomaly_scale_delivery": False},
            "issues": ["ANOMALY_NOT_READABLE"],
        }]})
        result = candidate_pool.weak_pass_eligibility(self.ep, frame)
        self.assertTrue(result["eligible"])
        self.assertEqual(result["content_attempts"], 4)
        self.assertEqual(result["technical_attempts"], 2)

    def test_weak_pass_never_overrides_hard_identity_failure(self):
        frame = 5
        _write(self.ep / "meta/production-ledger.json", {"frames": {"05": {
            "status": "NEEDS_USER",
            "current_candidate": {"sha256": "c" * 64},
            "attempts": [{"result": "success"}] * 4,
        }}})
        _write(self.ep / "meta/visual-profile-review.json", {"calibration": [{
            "id": "V-A", "frame": frame, "role": "first_major_anomaly",
            "checks": {"character_appearance_anchor_fidelity": False},
            "issues": ["CHARACTER_IDENTITY_MISMATCH"],
        }]})
        result = candidate_pool.weak_pass_eligibility(self.ep, frame)
        self.assertFalse(result["eligible"])
        self.assertIn("character_appearance_anchor_fidelity", result["hard_failed_checks"])

    def test_apply_weak_pass_preserves_failed_review_and_marks_ledger_and_gate(self):
        frame = 5
        sha = "c" * 64
        fc = "d" * 64
        _write(self.ep / "meta/production-ledger.json", {"frames": {"05": {
            "status": "NEEDS_USER",
            "current_candidate": {"sha256": sha},
            "attempts": [{"result": "success"}] * 4 + [{"result": "technical_failure"}],
            "reviews": [],
        }}})
        _write(self.ep / "meta/story-gates.json", {"visual": {"calibration": {"items": [{
            "id": "V-A", "frame": frame, "role": "first_major_anomaly",
            "sha256": sha, "frame_contract_sha256": fc, "decision": "failed",
        }]}}, "reviews": {"visual_admission": "failed"}})
        failed = {
            "id": "V-A", "frame": frame, "role": "first_major_anomaly",
            "sha256": sha, "frame_contract_sha256": fc,
            "checks": {"anomaly_scale_delivery": False},
            "issues": ["ANOMALY_NOT_READABLE"],
        }
        _write(self.ep / "meta/visual-profile-review.json", {
            "story_os_version": "2.6.1", "profile_sha256": self.profile_sha,
            "calibration": [failed],
        })
        result = candidate_pool.apply_weak_passes(self.ep, frames=[frame])
        self.assertEqual(result["status"], "PASS")
        ledger = json.loads((self.ep / "meta/production-ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(ledger["frames"]["05"]["status"], "WEAK_PASS")
        self.assertEqual(ledger["frames"]["05"]["weak_pass"]["approved_by_policy"], "attempt_over_3_auto_release")
        registry = admission_state.load(self.ep)
        self.assertEqual(registry["items"]["V-A"]["status"], "WEAK_PASS")
        self.assertEqual(registry["items"]["V-A"]["review_row"]["checks"]["anomaly_scale_delivery"], False)
        gates = json.loads((self.ep / "meta/story-gates.json").read_text(encoding="utf-8"))
        self.assertEqual(gates["visual"]["calibration"]["items"][0]["decision"], "passed")
        self.assertTrue(gates["visual"]["calibration"]["items"][0]["weak_pass"])

    def test_weak_pass_finalization_locks_existing_provisional_pixel_master_after_all_admissions_accept(self):
        projection = {"all_passed": True, "passed_frames": [1, 5, 8, 16]}
        _write(self.ep / "meta/story-gates.json", {"visual": {"calibration": {"items": [{
            "id": "V-B", "role": "ordinary_baseline", "frame": 1,
            "asset_path": "episode/baseline.png", "sha256": "a" * 64,
            "frame_contract_sha256": "b" * 64, "decision": "passed",
        }]}}})
        locked = {"status": "LOCKED", "sha256": "a" * 64}
        with patch.object(candidate_pool.character_visual_contract, "pixel_master_required", return_value=True), \
                patch.object(candidate_pool.character_visual_contract, "lock_pixel_master", return_value=locked) as lock:
            result = candidate_pool._lock_pixel_master_after_accepted_visual_gate(self.ep, projection)
        self.assertEqual(result["status"], "LOCKED")
        self.assertEqual(result["frame"], 1)
        self.assertEqual(lock.call_args.kwargs["asset_path"], "episode/baseline.png")

    def test_technical_failure_without_output_never_consumes_current_policy_slot(self):
        frame = 5
        failed = {
            "frame": frame,
            "kind": "baseline_candidate",
            "capture_id": f"visual-lock-candidate-{candidate_pool.CANDIDATE_POLICY_REVISION}-05-01",
            "status": "tech_failed",
            "output_path": None,
        }
        _write(self.ep / "meta/production-queue.json", {"items": [failed]})
        self.assertEqual(candidate_pool.successful_slots(self.ep, frame), 0)

    def test_restore_ledger_pass_requires_exact_current_candidate_sha(self):
        asset = _asset()
        _write(self.ep / "meta/production-ledger.json", {
            "frames": {"05": {
                "status": "NEEDS_USER",
                "current_candidate": {"sha256": asset["sha256"]},
                "reviews": [],
            }}
        })
        self.assertTrue(admission_state.restore_ledger_pass(
            self.ep, asset=asset, evidence_note="historical bound pass"
        ))
        ledger = json.loads((self.ep / "meta/production-ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(ledger["frames"]["05"]["status"], "PASSED")
        bad = _asset(sha="e" * 64)
        ledger["frames"]["05"]["status"] = "NEEDS_USER"
        _write(self.ep / "meta/production-ledger.json", ledger)
        self.assertFalse(admission_state.restore_ledger_pass(
            self.ep, asset=bad, evidence_note="must not restore"
        ))


if __name__ == "__main__":
    unittest.main()
