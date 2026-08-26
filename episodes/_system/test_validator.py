#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate_episode as validator


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class ValidatorTests(unittest.TestCase):
    def base_state(self, current="IDEA_LOCKED"):
        return {
            "schema_version": 1,
            "episode_id": "09-02",
            "series": "09_旧物怪谈",
            "title": "测试故事",
            "current_state": current,
            "updated_at": "2026-08-26T12:00:00+08:00",
            "history": [{"state": current, "at": "2026-08-26T12:00:00+08:00", "note": "test"}],
        }

    def base_manifest(self):
        return {
            "schema_version": 1,
            "episode": {"id": "09-02", "series": "09_旧物怪谈", "title": "测试故事", "format": "douyin_photo_carousel", "aspect_ratio": "9:16"},
            "release": {"version": None, "body_frame_count": 20, "publish_dir": None, "body_glob": "[0-9][0-9].png", "cover_path": None, "contact_sheet_path": None},
            "artifacts": {"story": None, "storyboard": None, "visual_spec": None, "captions": None, "publish_copy": None, "production_review": None, "propagation_card": None},
            "quality": {"production_gate": "pending", "propagation_score": None, "propagation_decision": "pending", "publish_decision": "hold", "decision_note": None},
            "publication": {"platform": "douyin", "actual_title": None, "description": None, "topics": [], "pinned_comment": None, "published_at": None, "post_url": None},
            "data_review": {"report_path": "reports/数据验收报告.md", "completed_checkpoints": []},
        }

    def test_idea_locked_minimal_passes(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            ep = repo / "episodes/09/02"
            write_json(ep / "meta/episode-state.json", self.base_state())
            write_json(ep / "meta/release-manifest.json", self.base_manifest())
            findings = validator.validate_episode(ep, repo, metadata_only=True)
            self.assertFalse(any(f.level == "FAIL" for f in findings), findings)

    def test_publish_ready_requires_gate_and_copy(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            ep = repo / "episodes/09/02"
            write_json(ep / "meta/episode-state.json", self.base_state("PUBLISH_READY"))
            write_json(ep / "meta/release-manifest.json", self.base_manifest())
            findings = validator.validate_episode(ep, repo, metadata_only=True)
            codes = {f.code for f in findings if f.level == "FAIL"}
            self.assertIn("production_not_passed", codes)
            self.assertIn("publish_hold", codes)
            self.assertIn("propagation_score", codes)

    def test_state_manifest_id_drift_fails(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            ep = repo / "episodes/09/02"
            state = self.base_state()
            manifest = self.base_manifest()
            manifest["episode"]["id"] = "09-99"
            write_json(ep / "meta/episode-state.json", state)
            write_json(ep / "meta/release-manifest.json", manifest)
            findings = validator.validate_episode(ep, repo, metadata_only=True)
            self.assertIn("id_drift", {f.code for f in findings})


if __name__ == "__main__":
    unittest.main()
