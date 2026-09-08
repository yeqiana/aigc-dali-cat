#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0 regression: validate --metadata-only on clean CI checkouts.

CI clean checkouts have no media/ by design (.gitignore). Before the fix,
visual_lock_v21 / final_candidate_snapshot / validate_episode interpreted
legacy-era placeholder fields with unconditional V2.6 semantics, so
validate_episode.py --all --metadata-only failed 3/6 registered episodes.
This suite pins the accepted boundary:

* metadata_only tolerates missing pixel files and legacy quality/gates
  envelopes with WARN only;
* full mode keeps failing on the same data (no weakened validation);
* metadata_only still catches pure-data drift (snapshot internal SHA).
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))

import final_candidate_snapshot  # noqa: E402
import story_json  # noqa: E402
import validate_episode as validator  # noqa: E402
import visual_lock_v21  # noqa: E402


def write_json(path: Path, data: dict) -> None:
    story_json.write_json(path, data)


class MetadataOnlyCiCompatibilityTests(unittest.TestCase):
    """Three behaviors fixed by the P0 clean-CI audit."""

    def base_legacy_state(self):
        return {
            "schema_version": 1,
            "tool_version": "2.2.1",
            "episode_id": "11-01",
            "series": "11_仲夏夜惊魂",
            "title": "仲夏夜惊魂 重制版",
            "current_state": "IDEA_LOCKED",
            "updated_at": "2026-08-31T12:00:00+08:00",
            "history": [{"state": "IDEA_LOCKED", "at": "2026-08-31T12:00:00+08:00", "mode": "migration", "note": "test"}],
        }

    def base_legacy_manifest(self):
        return {
            "schema_version": 1,
            "tool_version": "2.2.1",
            "episode": {"id": "11-01", "series": "11_仲夏夜惊魂", "title": "仲夏夜惊魂 重制版",
                        "format": "douyin_photo_carousel", "aspect_ratio": "9:16"},
            "release": {"body_frame_count": 20},
            "artifacts": {},
            "quality": {"production_gate": "not_ready", "propagation_score": None,
                        "publish_decision": "hold",
                        "decision_note": "PREPRODUCTION_ONLY: production not ready"},
            "publication": {},
            "data_review": {},
        }

    def base_legacy_gates(self):
        return {
            "schema_version": 1,
            "tool_version": "2.2.1",
            "episode_id": "11-01",
            "series": "11_仲夏夜惊魂",
            "title": "仲夏夜惊魂 重制版",
            "gates": {"story_lock": {"locked": False}, "production": "NOT_READY"},
            "story": {}, "visual": {}, "subtitles": {}, "machine_contract": {},
            "reviews": {"story": "passed", "authenticity": "passed", "continuity": "passed",
                        "visual_narrative": "passed", "visual_admission": "pending",
                        "production": "pending", "publish": "pending"},
        }

    def test_legacy_quality_and_gates_warn_in_metadata_but_fail_full(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            ep = repo / "episodes/11_仲夏夜惊魂/01_惊魂"
            write_json(ep / "meta/episode-state.json", self.base_legacy_state())
            write_json(ep / "meta/release-manifest.json", self.base_legacy_manifest())
            write_json(ep / "meta/story-gates.json", self.base_legacy_gates())

            meta = validator.validate_episode(ep, repo, True)
            self.assertFalse(any(f.level == "FAIL" for f in meta), meta)
            codes = {f.code for f in meta}
            self.assertIn("legacy_quality_placeholder", codes)
            self.assertIn("legacy_locks_pending", codes)

            full = validator.validate_episode(ep, repo, False)
            fail_codes = {f.code for f in full if f.level == "FAIL"}
            self.assertIn("production_gate", fail_codes, full)
            self.assertIn("propagation_decision", fail_codes, full)
            self.assertIn("locks", fail_codes, full)

    def test_visual_lock_calibration_metadata_only_skips_pixel_files(self):
        items = []
        frames = {"ordinary_baseline": 1, "worst_capture_condition": 7,
                  "first_major_anomaly": 13, "high_impact_admission": 20}
        for role in visual_lock_v21.ROLES:
            items.append({"id": "vb-" + role, "role": role, "frame": frames[role],
                          "asset_path": "media/visual_lock/" + role + ".png",
                          "sha256": "", "frame_contract_sha256": ""})
        gates = {"schema_version": 1, "tool_version": "2.1.0",
                 "visual": {"calibration": {"policy": "four_admission_v21", "items": items}}}
        with tempfile.TemporaryDirectory() as td:
            ep = Path(td) / "ep"
            write_json(ep / "meta/story-gates.json", gates)
            rows = visual_lock_v21.calibration_assets(ep, metadata_only=True)
            self.assertEqual([r["role"] for r in rows], list(visual_lock_v21.ROLES))
            # no media/ exists in this checkout; full mode must still refuse to hash it
            with self.assertRaises(Exception):
                visual_lock_v21.calibration_assets(ep, metadata_only=False)

    def test_snapshot_metadata_only_catches_internal_drift(self):
        lock = {"body": [], "text_artifacts": [], "evidence": [], "delivery_files": []}
        good_sha = final_candidate_snapshot.sha256_json(lock)
        with tempfile.TemporaryDirectory() as td:
            ep = Path(td) / "ep"
            saved = {"schema_version": 1, "lock": lock, "snapshot_sha256": "0" * 64}
            write_json(ep / "meta/final-candidate-snapshot.json", saved)
            errors = final_candidate_snapshot.verify(ep, metadata_only=True)
            self.assertIn("final candidate snapshot internal drift", errors)

            saved["snapshot_sha256"] = good_sha
            write_json(ep / "meta/final-candidate-snapshot.json", saved)
            self.assertEqual(final_candidate_snapshot.verify(ep, metadata_only=True), [])


if __name__ == "__main__":
    unittest.main()
