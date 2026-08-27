#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import struct
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


def fake_png(path: Path, width=1080, height=1920) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", width, height))


class ValidatorTests(unittest.TestCase):
    def base_state(self, current="IDEA_LOCKED", version="1.3"):
        return {
            "schema_version":1,"tool_version":version,"episode_id":"09-02","series":"09_旧物怪谈",
            "title":"测试故事","current_state":current,"updated_at":"2026-08-27T12:00:00+08:00",
            "history":[{"state":current,"at":"2026-08-27T12:00:00+08:00","mode":"migration","note":"test"}],
        }

    def base_manifest(self, version="1.3"):
        return {
            "schema_version":1,"tool_version":version,
            "episode":{"id":"09-02","series":"09_旧物怪谈","title":"测试故事","format":"douyin_photo_carousel","aspect_ratio":"9:16"},
            "release":{"version":None,"body_frame_count":20,"publish_dir":None,"body_glob":"[0-9][0-9].png","cover_path":None,"contact_sheet_path":None},
            "artifacts":{"story":None,"storyboard":None,"visual_spec":None,"captions":None,"publish_copy":None,"production_review":None,"propagation_card":None},
            "quality":{"production_gate":"pending","propagation_score":None,"s_min_score":None,"propagation_decision":"pending","publish_decision":"hold","decision_note":None},
            "publication":{"platform":"douyin","actual_title":None,"description":None,"topics":[],"pinned_comment":None,"published_at":None,"timing_window":None,"post_url":None},
            "data_review":{"report_path":"reports/数据验收报告.md","completed_checkpoints":[]},
        }

    def base_gates(self):
        return {
            "schema_version":1,"tool_version":"1.3","episode_id":"09-02",
            "story":{"recent5_checked":True,"four_locks_diff_count":2,"mechanism_skin_swap_veto":False,"task_closed":True,"competing_explanations":2,
                     "hook_frames":[1,2,3],"escalation_frames":[7,13],"climax_frame":17,"payoff_frame":20},
            "visual":{"admission_frames":[1,7,13,20],
                      "continuity":{"required":["location","key_prop","weather_time"],
                                    "anchors":{"protagonist":"主角A","location":"西北农村老屋","key_prop":"黑色MP4","wardrobe":"黑T","weather_time":"暑假阴天"}}},
            "subtitles":{"required":True,"sound_card_completed":True},
            "locks":{"edit_mode":"none","assets":[]},
            "reviews":{"story":"passed","authenticity":"passed","continuity":"passed","visual_admission":"passed","subtitle":"passed",
                       "production":"passed","recommendation_fit":"passed","publish":"passed"},
        }

    def setup_episode(self, repo: Path, state=None, manifest=None, gates=None):
        ep = repo / "episodes/09/02"
        write_json(ep / "meta/episode-state.json", state or self.base_state())
        write_json(ep / "meta/release-manifest.json", manifest or self.base_manifest())
        if gates is not False:
            write_json(ep / "meta/story-gates.json", gates or self.base_gates())
        return ep

    def make_stage_docs(self, repo: Path, manifest: dict):
        for rel in ["docs/storyboard.md","docs/visual.md","docs/production.md","docs/captions.md","docs/publish.md","docs/propagation.md"]:
            p=repo/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text("ok",encoding="utf-8")
        manifest["artifacts"].update({
            "storyboard":"docs/storyboard.md","visual_spec":"docs/visual.md","production_review":"docs/production.md",
            "captions":"docs/captions.md","publish_copy":"docs/publish.md","propagation_card":"docs/propagation.md",
        })

    def test_legacy_without_gates_is_compatible(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td)
            ep=self.setup_episode(repo,self.base_state(version="1.2"),self.base_manifest(version="1.2"),False)
            findings=validator.validate_episode(ep,repo,True)
            self.assertFalse(any(f.level=="FAIL" for f in findings),findings)
            self.assertIn("legacy_without_story_gates",{f.code for f in findings})

    def test_new_episode_requires_gates(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td)
            ep=self.setup_episode(repo,gates=False)
            self.assertIn("missing_story_gates",{f.code for f in validator.validate_episode(ep,repo,True) if f.level=="FAIL"})

    def test_story_gate_blocks_unchecked_recent5(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); state=self.base_state("STORYBOARD_LOCKED"); manifest=self.base_manifest(); gates=self.base_gates()
            p=repo/"docs/storyboard.md"; p.parent.mkdir(parents=True); p.write_text("ok",encoding="utf-8"); manifest["artifacts"]["storyboard"]="docs/storyboard.md"
            gates["story"]["recent5_checked"]=False
            ep=self.setup_episode(repo,state,manifest,gates)
            self.assertIn("recent5_not_checked",{f.code for f in validator.validate_episode(ep,repo,True) if f.level=="FAIL"})

    def test_visual_gate_requires_real_anchors(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); state=self.base_state("VISUAL_CALIBRATED"); manifest=self.base_manifest(); gates=self.base_gates()
            for rel,key in [("docs/storyboard.md","storyboard"),("docs/visual.md","visual_spec")]:
                p=repo/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text("ok",encoding="utf-8"); manifest["artifacts"][key]=rel
            gates["visual"]["continuity"]["anchors"]["key_prop"]=""
            ep=self.setup_episode(repo,state,manifest,gates)
            self.assertIn("continuity_anchor_missing",{f.code for f in validator.validate_episode(ep,repo,True) if f.level=="FAIL"})

    def test_production_requires_sound_card(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); state=self.base_state("PRODUCTION_PASSED"); manifest=self.base_manifest(); gates=self.base_gates()
            self.make_stage_docs(repo,manifest); manifest["quality"]["production_gate"]="pass"; gates["subtitles"]["sound_card_completed"]=False
            ep=self.setup_episode(repo,state,manifest,gates)
            self.assertIn("sound_card",{f.code for f in validator.validate_episode(ep,repo,True) if f.level=="FAIL"})

    def test_subtitle_only_hash_change_fails(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); gates=self.base_gates()
            locked=repo/"episodes/09/02/locked.png"; fake_png(locked)
            h=hashlib.sha256(locked.read_bytes()).hexdigest()
            gates["locks"]={"edit_mode":"subtitle_only","assets":[{"path":"episodes/09/02/locked.png","sha256":h,"reason":"只改字幕"}]}
            ep=self.setup_episode(repo,gates=gates)
            locked.write_bytes(locked.read_bytes()+b"x")
            self.assertIn("locked_asset_changed",{f.code for f in validator.validate_episode(ep,repo,False) if f.level=="FAIL"})

    def test_metadata_only_skips_locked_binary_hash(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); gates=self.base_gates()
            gates["locks"]={"edit_mode":"subtitle_only","assets":[{"path":"episodes/09/02/not-in-git.png","sha256":"0"*64,"reason":"只改字幕"}]}
            ep=self.setup_episode(repo,gates=gates)
            self.assertNotIn("locked_asset_missing",{f.code for f in validator.validate_episode(ep,repo,True) if f.level=="FAIL"})

    def test_publish_ready_wrong_dimensions_fail(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); state=self.base_state("PUBLISH_READY"); manifest=self.base_manifest(); gates=self.base_gates()
            self.make_stage_docs(repo,manifest); manifest["quality"].update({"production_gate":"pass","propagation_score":9.2,"s_min_score":8.5,"propagation_decision":"strong","publish_decision":"go"})
            manifest["publication"].update({"actual_title":"标题","description":"简介","topics":["怪谈"]})
            pub=repo/"episodes/09/02/publish"; pub.mkdir(parents=True)
            for i in range(1,21): fake_png(pub/f"{i:02d}.png",1024 if i==2 else 1080,1920)
            cover=repo/"episodes/09/02/cover.png"; fake_png(cover)
            manifest["release"].update({"version":"V1","publish_dir":"episodes/09/02/publish","cover_path":"episodes/09/02/cover.png"})
            ep=self.setup_episode(repo,state,manifest,gates)
            self.assertIn("image_size",{f.code for f in validator.validate_episode(ep,repo,False) if f.level=="FAIL"})

    def test_propagation_thresholds_preserved(self):
        self.assertEqual(validator.derive_propagation_decision(9.2,8.5),"strong")
        self.assertEqual(validator.derive_propagation_decision(8.7,7.5),"publishable")
        self.assertEqual(validator.derive_propagation_decision(8.3,7.0),"conditional")
        self.assertEqual(validator.derive_propagation_decision(8.29,10),"not_recommended")

    def test_legacy_forward_target_requires_gate_migration(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td)
            ep=self.setup_episode(repo,self.base_state(version="1.2"),self.base_manifest(version="1.2"),False)
            findings=validator.validate_episode(ep,repo,True,"STORYBOARD_LOCKED")
            self.assertIn("legacy_story_gates_required",{f.code for f in findings if f.level=="FAIL"})


if __name__ == "__main__":
    unittest.main()
