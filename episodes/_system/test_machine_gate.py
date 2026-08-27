#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import machine_gate


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_asset(root: Path, rel: str, payload: bytes) -> dict:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {"path": rel, "sha256": hashlib.sha256(payload).hexdigest()}


class MachineGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.ep = self.root / "episodes/99_test"
        (self.ep / "meta").mkdir(parents=True)
        self.original_repo_root = machine_gate.repo_root_from_script
        machine_gate.repo_root_from_script = lambda: self.root

    def tearDown(self) -> None:
        machine_gate.repo_root_from_script = self.original_repo_root
        self.tmp.cleanup()

    def manifest(self, total: int = 3) -> dict:
        return {
            "episode": {"aspect_ratio": "4:5"},
            "release": {"body_frame_count": total},
        }

    def gates(self, strict: bool = True) -> dict:
        return {
            "machine_contract": {"version": 1, "strict": strict},
            "visual": {
                "admission_frames": [1, 2, 3, 4],
                "authenticity_card": {
                    "story_era": "2004",
                    "location": "西北县城",
                    "photographer": "第一人称主角",
                    "shooting_reason": "记录返乡过程",
                    "primary_capture": {"id": "phone-main", "device": "普通手机"},
                    "secondary_captures": [],
                    "secondary_source_explanation": None,
                    "aspect_ratio": "4:5",
                    "capture_states": {
                        "stable": "正常站立随手拍",
                        "restricted": "车内受限机位",
                        "lost_control": "奔跑时方向性拖影",
                    },
                    "camera_rules": {
                        "current_device_may_be_fully_visible": False,
                        "current_device_visibility_explanation": None,
                        "photographer_may_be_fully_visible": False,
                        "photographer_visibility_explanation": None,
                    },
                },
                "calibration": {},
                "calibration_contact_sheet": {},
                "references": {"required": False, "required_anchors": [], "items": []},
            },
            "production_evidence": {
                "frame_review_dir": "meta/frame-reviews",
                "review_schema_version": 1,
                "require_all_frames": True,
            },
        }

    def populate_calibration(self, gates: dict) -> None:
        for n, role in enumerate(machine_gate.CALIBRATION_ROLES, 1):
            asset = write_asset(self.root, f"episodes/99_test/production/cal-{n}.png", f"cal-{n}".encode())
            gates["visual"]["calibration"][role] = {
                "frame": n,
                "asset_path": asset["path"],
                "sha256": asset["sha256"],
                "decision": "passed",
                "note": "ok",
            }
        sheet = write_asset(self.root, "episodes/99_test/production/contact-sheets/calibration.jpg", b"sheet")
        gates["visual"]["calibration_contact_sheet"] = sheet

    def review(self, key: str, *, bad: bool = False) -> dict:
        return {
            "schema_version": 1,
            "frame": key,
            "viewpoint_physics": "fail" if bad else "pass",
            "unplanned_recorder_absent": "pass",
            "capture_profile_match": "pass",
            "not_cinematic": "pass",
            "identity_match": "na",
            "key_prop_match": "pass",
            "location_match": "pass",
            "continuity_match": "pass",
            "defects_are_causal": "pass",
            "album_test": "pass",
            "hard_failures_detected": [],
            "red_flags_detected": [],
            "red_flags_exempted": [],
            "intentional_exception": {"enabled": False, "reason": ""},
            "decision": "pass",
            "notes": "ok",
        }

    def populate_production(self, total: int = 3, *, bad_review: int | None = None) -> None:
        frames = {}
        for n in range(1, total + 1):
            key = f"{n:02d}"
            asset = write_asset(self.root, f"episodes/99_test/production/approved/{key}.png", f"approved-{key}".encode())
            frames[key] = {
                "status": "LOCKED",
                "content_repairs_used": 0,
                "approved_asset": asset,
                "lock": {"sha256": asset["sha256"]},
            }
            write_json(self.ep / f"meta/frame-reviews/{key}.json", self.review(key, bad=(n == bad_review)))
        write_json(self.ep / "meta/production-ledger.json", {"frames": frames})

    def test_legacy_contract_is_compatible(self) -> None:
        write_json(self.ep / "meta/release-manifest.json", self.manifest())
        write_json(self.ep / "meta/story-gates.json", self.gates(strict=False))
        findings = machine_gate.validate(self.ep, "PRODUCTION_PASSED")
        self.assertFalse(any(x.level == "FAIL" for x in findings))
        self.assertTrue(any(x.code == "machine_gate_legacy" for x in findings))

    def test_visual_gate_requires_calibration(self) -> None:
        write_json(self.ep / "meta/release-manifest.json", self.manifest())
        write_json(self.ep / "meta/story-gates.json", self.gates())
        findings = machine_gate.validate(self.ep, "VISUAL_CALIBRATED")
        self.assertTrue(any(x.code == "calibration_role" for x in findings))

    def test_visual_gate_passes_with_hashed_calibration(self) -> None:
        gates = self.gates()
        self.populate_calibration(gates)
        write_json(self.ep / "meta/release-manifest.json", self.manifest())
        write_json(self.ep / "meta/story-gates.json", gates)
        findings = machine_gate.validate(self.ep, "VISUAL_CALIBRATED")
        self.assertFalse(any(x.level == "FAIL" for x in findings), [str(x) for x in findings])

    def test_production_gate_rejects_hard_frame_failure(self) -> None:
        gates = self.gates()
        self.populate_calibration(gates)
        write_json(self.ep / "meta/release-manifest.json", self.manifest())
        write_json(self.ep / "meta/story-gates.json", gates)
        self.populate_production(bad_review=2)
        findings = machine_gate.validate(self.ep, "PRODUCTION_PASSED")
        self.assertTrue(any(x.code == "frame_review_hard_fail" for x in findings))

    def test_production_gate_passes_complete_evidence(self) -> None:
        gates = self.gates()
        self.populate_calibration(gates)
        write_json(self.ep / "meta/release-manifest.json", self.manifest())
        write_json(self.ep / "meta/story-gates.json", gates)
        self.populate_production()
        findings = machine_gate.validate(self.ep, "PRODUCTION_PASSED")
        self.assertFalse(any(x.level == "FAIL" for x in findings), [str(x) for x in findings])


if __name__ == "__main__":
    unittest.main()
