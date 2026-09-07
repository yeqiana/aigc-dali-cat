#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B7 S3.1 review schema compatibility: era selectors, delegated checks, divergence.

The Visual Profile Review payload has two era shapes on the same file
(meta/visual-profile-review.json): legacy three-slot schema_version=1 for
pre-V2.1 contracts and four-admission schema_version=2 for V2.1+ Visual Lock.
This suite pins the read-side adapter and proves that an old payload read under
a newer contract produces an explicit difference report instead of a silent
PASS. Check lists are never copied here: the adapter delegates to
visual_lock_v21.checks_for_version (11/15/18) and visual_review_legacy.CHECKS.
"""
from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"


def _load(name: str):
    sys.path.insert(0, str(SYSTEM))
    return importlib.import_module(name)


def _legacy_checks() -> tuple:
    return tuple(_load("visual_review_legacy").CHECKS)


def _v2_checks(version: str) -> tuple:
    return tuple(_load("visual_lock_v21").checks_for_version(version))


def _rows(ids, check_names, *, missing=None) -> list:
    missing = set(missing or [])
    rows = []
    for rid in ids:
        checks = {key: True for key in check_names if key not in missing}
        rows.append({"id": rid, "sha256": "a" * 64, "checks": checks, "issues": []})
    return rows


def _legacy_payload() -> dict:
    return {
        "schema_version": 1,
        "story_os_version": "2.0.3.4",
        "profile_id": "M00",
        "profile_sha256": "a" * 64,
        "critic_provenance": {},
        "calibration": _rows(("A", "B", "C"), _legacy_checks()),
        "issue_codes": [],
        "summary": {"passed": True},
    }


def _v2_payload(version: str, *, ids=("V-B", "V-W", "V-A", "V-H"), missing=None) -> dict:
    return {
        "schema_version": 2,
        "story_os_version": version,
        "profile_id": "M00",
        "profile_sha256": "a" * 64,
        "critic_provenance": {},
        "calibration": _rows(ids, _v2_checks(version), missing=missing),
        "issue_codes": [],
        "summary": {"passed": True},
    }


class VisualReviewSchemaCompatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = _load("visual_review_schema")

    def test_legacy_payload_aligned_with_legacy_contract_has_no_divergence(self):
        self.assertEqual(
            self.schema.era_divergence(_legacy_payload(), version="2.0.3.4"),
            [],
        )

    def test_v2_payloads_aligned_for_11_15_18_check_eras_have_no_divergence(self):
        for version in ("2.1.0", "2.2.0", "2.2.1"):
            self.assertEqual(
                self.schema.era_divergence(_v2_payload(version), version=version),
                [],
                version,
            )

    def test_v1_three_slot_payload_read_under_v2_contract_reports_explicit_differences(self):
        report = self.schema.era_divergence(_legacy_payload(), version="2.1.0")
        self.assertTrue(report)
        text = "\n".join(report)
        self.assertIn("schema_version: found 1, expected 2", text)
        self.assertIn("calibration rows: found 3, expected 4", text)
        self.assertIn("missing checks: environment_physics_fidelity", text)
        self.assertIn("scale_reference_fidelity", text)

    def test_v2_payload_with_missing_row_and_checks_is_explicitly_reported(self):
        payload = _v2_payload(
            "2.2.1",
            ids=("V-B", "V-W", "V-A"),
            missing=("world_identity_fidelity", "camera_defect_physics"),
        )
        report = self.schema.era_divergence(payload, version="2.2.1")
        self.assertTrue(report)
        text = "\n".join(report)
        self.assertIn("calibration rows: found 3, expected 4", text)
        self.assertIn("row 'V-B': missing checks: camera_defect_physics, world_identity_fidelity", text)

    def test_malformed_rows_never_pass_silently(self):
        payload = {
            "schema_version": 2,
            "calibration": [{"id": "V-B"}, "not-an-object", {"checks": []}],
        }
        report = self.schema.era_divergence(payload, version="2.1.0")
        self.assertTrue(report)
        text = "\n".join(report)
        self.assertIn("calibration row 2: not an object", text)

    def test_checks_are_delegated_not_copied(self):
        self.assertEqual(self.schema.checks_for_contract_version("2.1.8"), _v2_checks("2.1.8"))
        self.assertEqual(self.schema.checks_for_contract_version("2.2.0"), _v2_checks("2.2.0"))
        self.assertEqual(self.schema.checks_for_contract_version("2.2.1"), _v2_checks("2.2.1"))
        self.assertEqual(self.schema.checks_for_contract_version("2.0.3.4"), _legacy_checks())
        self.assertEqual(len(_v2_checks("2.1.8")), 11)
        self.assertEqual(len(_v2_checks("2.2.0")), 15)
        self.assertEqual(len(_v2_checks("2.2.1")), 18)
        self.assertTrue(set(_legacy_checks()) <= set(_v2_checks("2.1.8")))

    def test_era_selectors_and_tolerant_reads(self):
        s = self.schema
        self.assertEqual(s.schema_for_contract_version("2.0.3.4"), s.SCHEMA_VERSION_LEGACY)
        self.assertEqual(s.schema_for_contract_version("2.1.0"), s.SCHEMA_VERSION_V2)
        self.assertEqual(s.row_count_for_schema(1), 3)
        self.assertEqual(s.row_count_for_schema(2), 4)
        self.assertIsNone(s.row_count_for_schema(9))
        self.assertEqual(s.payload_schema_version(_legacy_payload()), 1)
        self.assertEqual(s.payload_schema_version(_v2_payload("2.2.1")), 2)
        self.assertIsNone(s.payload_schema_version(None))
        self.assertIsNone(s.payload_schema_version({"schema_version": "2"}))
        self.assertEqual(s.calibration_rows(_v2_payload("2.1.0")), _v2_payload("2.1.0")["calibration"])
        self.assertEqual(s.calibration_rows({"calibration": None}), [])


if __name__ == "__main__":
    unittest.main()
