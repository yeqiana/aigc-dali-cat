#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

import frame_semantic_review as fsr


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FrameSemanticEnforcementTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.ep = self.root / "episodes/99_test/01_frame_semantic"
        (self.ep / "meta/frame-reviews").mkdir(parents=True)
        self.old_root = fsr.ROOT
        fsr.ROOT = self.root

        story = self.ep / "docs/story.md"
        board = self.ep / "docs/storyboard.md"
        story.parent.mkdir(parents=True)
        story.write_text("story", encoding="utf-8")
        board.write_text("storyboard", encoding="utf-8")
        write_json(self.ep / "meta/release-manifest.json", {
            "tool_version": "2.0.3.3",
            "artifacts": {
                "story": story.relative_to(self.root).as_posix(),
                "storyboard": board.relative_to(self.root).as_posix(),
            },
            "release": {"body_frame_count": 2},
        })
        write_json(self.ep / "meta/episode-state.json", {"tool_version": "2.0.3.3", "current_state": "PRODUCTION_PASSED"})
        write_json(self.ep / "meta/story-gates.json", {
            "tool_version": "2.0.3.3",
            "visual_profile": {"profile_id": "M00"},
            "visual": {
                "authenticity_card": {"photographer": "第一人称"},
                "continuity": {"anchors": {"wardrobe": "深蓝外套"}},
                "references": {},
            },
        })

    def tearDown(self) -> None:
        fsr.ROOT = self.old_root
        self.tmp.cleanup()

    def make_image(self, key: str, value: int) -> Path:
        p = self.ep / f"production/approved/{key}.png"
        p.parent.mkdir(parents=True, exist_ok=True)
        im = Image.new("L", (64, 64), value)
        # asymmetry keeps perceptual hashes meaningful
        for x in range(8, 24):
            for y in range(8, 40):
                im.putpixel((x, y), min(255, value + 30))
        im.convert("RGB").save(p)
        return p

    def populate(self, same: bool = False) -> list[dict]:
        p1 = self.make_image("01", 40)
        if same:
            p2 = self.ep / "production/approved/02.png"
            p2.write_bytes(p1.read_bytes())
        else:
            p2 = self.make_image("02", 180)
        frames = {}
        for key, path in [("01", p1), ("02", p2)]:
            rel = path.relative_to(self.root).as_posix()
            frames[key] = {
                "status": "LOCKED",
                "approved_asset": {"path": rel, "sha256": sha(path)},
                "lock": {"sha256": sha(path)},
                "content_repairs_used": 0,
            }
        write_json(self.ep / "meta/production-ledger.json", {"frames": frames})
        return fsr.frame_records(self.ep, require_files=True)

    def write_pass_reviews(self, frames: list[dict]) -> None:
        contexts = fsr.context_hashes(self.ep)
        provenance = {"runtime": "CODEX_ISOLATED", "isolated_session": True, "review_scope": "FULL_FRAME_SET", "attempt": 1}
        version = "2.0.3.3"
        for frame in frames:
            write_json(self.ep / f"meta/frame-reviews/{frame['frame']}.json", {
                "schema_version": 2,
                "story_os_version": version,
                "frame": frame["frame"],
                "asset_path": frame["path_rel"],
                "asset_sha256": frame["sha256"],
                **contexts,
                "critic_provenance": provenance,
                "checks": {k: True for k in fsr.CHECKS},
                "issue_codes": [],
                "decision": "pass",
            })
        write_json(self.ep / "meta/frame-semantic-review.json", {
            "schema_version": 2,
            "story_os_version": version,
            **contexts,
            "critic_provenance": provenance,
            "frames": [{"frame": x["frame"], "asset_sha256": x["sha256"]} for x in frames],
            "issue_codes": [],
            "summary": {"passed": True},
        })

    def test_sha_bound_review_passes_metadata(self) -> None:
        frames = self.populate()
        self.write_pass_reviews(frames)
        with mock.patch.object(fsr, "story_os_version", return_value="2.0.3.3"):
            self.assertEqual(fsr.verify_episode(self.ep, metadata_only=True), [])

    def test_sha_drift_is_rejected(self) -> None:
        frames = self.populate()
        self.write_pass_reviews(frames)
        p = self.ep / "meta/frame-reviews/01.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        d["asset_sha256"] = "0" * 64
        write_json(p, d)
        with mock.patch.object(fsr, "story_os_version", return_value="2.0.3.3"):
            errors = fsr.verify_episode(self.ep, metadata_only=True)
        self.assertTrue(any("asset_sha256" in x for x in errors), errors)

    def test_missing_review_is_rejected(self) -> None:
        frames = self.populate()
        self.write_pass_reviews(frames)
        (self.ep / "meta/frame-reviews/02.json").unlink()
        with mock.patch.object(fsr, "story_os_version", return_value="2.0.3.3"):
            errors = fsr.verify_episode(self.ep, metadata_only=True)
        self.assertTrue(any("missing frame semantic review" in x for x in errors), errors)

    def test_actual_duplicate_is_rejected(self) -> None:
        frames = self.populate(same=True)
        self.write_pass_reviews(frames)
        with mock.patch.object(fsr, "story_os_version", return_value="2.0.3.3"):
            errors = fsr.verify_episode(self.ep, metadata_only=False)
        self.assertTrue(any("near-duplicate actual frames" in x for x in errors), errors)

    def test_v2032_episode_does_not_require_new_review(self) -> None:
        write_json(self.ep / "meta/episode-state.json", {"tool_version": "2.0.3.2"})
        write_json(self.ep / "meta/release-manifest.json", {"tool_version": "2.0.3.2"})
        write_json(self.ep / "meta/story-gates.json", {"tool_version": "2.0.3.2"})
        self.assertFalse(fsr.review_required(self.ep))


if __name__ == "__main__":
    unittest.main()
