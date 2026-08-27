from __future__ import annotations

import hashlib
import struct
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

HERE = Path(__file__).resolve()
SCRIPTS = HERE.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_all
import validate_locked_edits
import validate_package


def fake_png(path: Path, width: int = 1080, height: int = 1920) -> None:
    # validators only need PNG signature + IHDR width/height; not intended as a displayable image.
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", width, height))


def manifest_data() -> dict:
    return {
        "schema_version": 1,
        "stage": "release_ready",
        "episode": {"id": "test-episode", "title": "测试故事", "series": "tests"},
        "format": {"publish_mode": "image_carousel", "ratio": "9:16", "width": 1080, "height": 1920, "frame_count": 4, "allowed_extensions": ["png"]},
        "paths": {"publish_dir": "publish", "subtitles_file": "docs/subtitles.yaml"},
        "story": {"hook_frames": [1,2], "visual_admission_frames": [1,2,3,4], "escalation_frames": [2,3], "climax_frame": 3, "payoff_frame": 4, "task_closed": True, "competing_explanations": 2},
        "anti_homogeneity": {"recent5_checked": True, "four_locks_diff_count": 2, "mechanism_skin_swap_veto": False},
        "continuity": {"anchors": {"protagonist": "p1", "location": "l1", "key_prop": "k1"}},
        "subtitles": {"required": True, "sound_card_completed": True, "max_lines": 2, "max_chars_per_line": None},
        "locks": {"edit_mode": "none", "assets": []},
        "review": {
            "authenticity":"passed","continuity":"passed","subtitle":"passed","story":"passed",
            "visual_admission":"passed","production":"passed","recommendation_fit":"passed","publish":"passed",
            "release_required":["authenticity","continuity","subtitle","story","visual_admission","production","recommendation_fit","publish"],
            "waivers": {}
        }
    }


def subtitle_data() -> dict:
    return {
        "voice_card": {
            "person":"我","age":"20多岁","role":"记录者","education_and_knowledge_boundary":"普通人",
            "usual_terms":"日常口语","recording_reason":"记录异常","knows_now":"只知道眼前发生的事",
            "does_not_know":"不知道异常来源","allowed_technical_terms":"手机",
            "forbidden_technical_terms":"无来源学术术语","stress_language":"句子变短","fear_language_change":"停顿和短句",
        },
        "frames": {1:"第一句",2:"第二句",3:"第三句",4:"最后一句"},
        "silent_frames": [],
        "clues": [],
    }


class ValidatorTests(unittest.TestCase):
    def make_episode(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        (root/"publish").mkdir()
        (root/"docs").mkdir()
        for i in range(1,5): fake_png(root/"publish"/f"{i:02d}.png")
        (root/"episode.yaml").write_text(yaml.safe_dump(manifest_data(), allow_unicode=True, sort_keys=False), encoding="utf-8")
        (root/"docs"/"subtitles.yaml").write_text(yaml.safe_dump(subtitle_data(), allow_unicode=True, sort_keys=False), encoding="utf-8")
        return td, root

    def test_release_ready_passes(self):
        td, root = self.make_episode()
        try:
            r = validate_all.validate(root/"episode.yaml", release=True)
            self.assertTrue(r.ok, r.errors)
        finally: td.cleanup()

    def test_missing_frame_fails(self):
        td, root = self.make_episode()
        try:
            (root/"publish"/"03.png").unlink()
            r = validate_package.validate(root/"episode.yaml", release=True)
            self.assertFalse(r.ok)
            self.assertTrue(any("缺失图号" in x for x in r.errors))
        finally: td.cleanup()

    def test_wrong_dimension_fails(self):
        td, root = self.make_episode()
        try:
            fake_png(root/"publish"/"02.png", 1024, 1792)
            r = validate_package.validate(root/"episode.yaml", release=True)
            self.assertFalse(r.ok)
            self.assertTrue(any("尺寸" in x for x in r.errors))
        finally: td.cleanup()

    def test_locked_asset_change_fails(self):
        td, root = self.make_episode()
        try:
            locked=root/"locked.png"; fake_png(locked)
            d=yaml.safe_load((root/"episode.yaml").read_text(encoding="utf-8"))
            h=hashlib.sha256(locked.read_bytes()).hexdigest()
            d["locks"]={"edit_mode":"subtitle_only","assets":[{"path":"locked.png","sha256":h,"reason":"只改字幕"}]}
            (root/"episode.yaml").write_text(yaml.safe_dump(d,allow_unicode=True,sort_keys=False),encoding="utf-8")
            locked.write_bytes(locked.read_bytes()+b"changed")
            r=validate_locked_edits.validate(root/"episode.yaml",release=True)
            self.assertFalse(r.ok)
            self.assertTrue(any("已变化" in x for x in r.errors))
        finally: td.cleanup()

if __name__ == "__main__": unittest.main()
