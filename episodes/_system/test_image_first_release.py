#!/usr/bin/env python3
"""Regression: canonical Story OS release is image-first and has no video dependency."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import release_package  # noqa: E402


class ImageFirstReleaseTests(unittest.TestCase):
    def test_release_package_builds_without_video_or_ffmpeg_dependency(self) -> None:
        release_source = (HERE / "release_package.py").read_text(encoding="utf-8")
        self.assertNotIn("ffmpeg", release_source.lower())
        self.assertNotIn("final_video", release_source)

        with tempfile.TemporaryDirectory(prefix="storyos-image-release-", dir=ROOT) as raw:
            ep = Path(raw)
            meta = ep / "meta"
            publish = ep / "media" / "publish"
            artifacts = ep / "artifacts"
            meta.mkdir(parents=True)
            publish.mkdir(parents=True)
            artifacts.mkdir(parents=True)

            cover = publish / "cover.png"
            body = publish / "01.png"
            captions = artifacts / "captions.yaml"
            publish_copy = artifacts / "publish-copy.md"
            propagation = artifacts / "propagation-card.json"
            for path, content in (
                (cover, b"cover"),
                (body, b"body"),
                (captions, b"captions: {}\n"),
                (publish_copy, b"title\n"),
                (propagation, b"{}\n"),
            ):
                path.write_bytes(content)

            rel = lambda p: p.relative_to(ROOT).as_posix()
            manifest = {
                "episode": {"id": "T-01", "series": "test", "title": "image-first", "aspect_ratio": "4:5"},
                "publication": {"platform": "image-platform", "actual_title": "image-first"},
                "release": {
                    "version": "test",
                    "publish_dir": rel(publish),
                    "body_glob": "[0-9][0-9].png",
                    "body_frame_count": 1,
                    "cover_path": rel(cover),
                },
                "artifacts": {
                    "captions": rel(captions),
                    "publish_copy": rel(publish_copy),
                    "propagation_card": rel(propagation),
                },
            }
            (meta / "release-manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
            )

            with mock.patch.object(release_package.final_snapshot, "required", return_value=False), \
                 mock.patch.object(release_package, "frame_semantic_required", return_value=False):
                payload = release_package.build_payload(ep)

            self.assertEqual([row["role"] for row in payload["body"]], ["body:01"])
            self.assertNotIn("video", payload)
            self.assertTrue(payload["package_sha256"])

    def test_core_spec_explicitly_forbids_video_generation(self) -> None:
        spec = (ROOT / "standards" / "制作规范_正式版.md").read_text(encoding="utf-8")
        self.assertIn("### 8.0 媒介边界：只做图文，不引入视频生成", spec)
        self.assertIn("正式生产链禁止引入视频生成或图片转视频", spec)
        self.assertIn("不得以“平台兼容、单文件交付、字幕烧录、方便预览”等理由自动派生视频", spec)
        self.assertIn("禁止先在代码中引入，再反向修改规范追认", spec)

    def test_release_dag_contains_no_video_step(self) -> None:
        dag = json.loads((ROOT / "runtimes" / "runtime-dag.json").read_text(encoding="utf-8"))
        release = next(step for step in dag["steps"] if step["id"] == "RELEASE")
        self.assertEqual(
            release["covers"],
            ["TEXT_RELEASE", "FINAL_CANDIDATE_SNAPSHOT", "PUBLISH_READY_GATE"],
        )


if __name__ == "__main__":
    unittest.main()
