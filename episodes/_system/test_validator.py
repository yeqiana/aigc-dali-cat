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
        return {"schema_version":1,"tool_version":"1.1","episode_id":"09-02","series":"09_旧物怪谈","title":"测试故事","current_state":current,"updated_at":"2026-08-26T12:00:00+08:00","history":[{"state":current,"at":"2026-08-26T12:00:00+08:00","mode":"migration","note":"test"}]}

    def base_manifest(self):
        return {"schema_version":1,"tool_version":"1.1","episode":{"id":"09-02","series":"09_旧物怪谈","title":"测试故事","format":"douyin_photo_carousel","aspect_ratio":"9:16"},"release":{"version":None,"body_frame_count":20,"publish_dir":None,"body_glob":"[0-9][0-9].png","cover_path":None,"contact_sheet_path":None},"artifacts":{"story":None,"storyboard":None,"visual_spec":None,"captions":None,"publish_copy":None,"production_review":None,"propagation_card":None},"quality":{"production_gate":"pending","propagation_score":None,"s_min_score":None,"propagation_decision":"pending","publish_decision":"hold","decision_note":None},"publication":{"platform":"douyin","actual_title":None,"description":None,"topics":[],"pinned_comment":None,"published_at":None,"post_url":None},"data_review":{"report_path":"reports/数据验收报告.md","completed_checkpoints":[]}}

    def test_idea_locked_minimal_passes(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); ep=repo/'episodes/09/02'; write_json(ep/'meta/episode-state.json',self.base_state()); write_json(ep/'meta/release-manifest.json',self.base_manifest())
            self.assertFalse(any(f.level=='FAIL' for f in validator.validate_episode(ep,repo,True)))

    def test_publish_ready_requires_gate_and_copy(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); ep=repo/'episodes/09/02'; write_json(ep/'meta/episode-state.json',self.base_state('PUBLISH_READY')); write_json(ep/'meta/release-manifest.json',self.base_manifest())
            codes={f.code for f in validator.validate_episode(ep,repo,True) if f.level=='FAIL'}
            self.assertIn('production_not_passed',codes); self.assertIn('publish_hold',codes); self.assertIn('propagation_score',codes); self.assertIn('s_min_score',codes)

    def test_state_manifest_id_drift_fails(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); ep=repo/'episodes/09/02'; state=self.base_state(); manifest=self.base_manifest(); manifest['episode']['id']='09-99'; write_json(ep/'meta/episode-state.json',state); write_json(ep/'meta/release-manifest.json',manifest)
            self.assertIn('id_drift',{f.code for f in validator.validate_episode(ep,repo,True)})

    def test_propagation_decision_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); ep=repo/'episodes/09/02'; state=self.base_state('PUBLISH_READY'); manifest=self.base_manifest()
            for rel in ['docs/production.md','docs/captions.md','docs/publish.md','docs/propagation.md']:
                f=repo/rel; f.parent.mkdir(parents=True,exist_ok=True); f.write_text('ok',encoding='utf-8')
            manifest['artifacts'].update({'production_review':'docs/production.md','captions':'docs/captions.md','publish_copy':'docs/publish.md','propagation_card':'docs/propagation.md'})
            manifest['release'].update({'version':'V1','publish_dir':'episodes/09/02/publish','cover_path':'episodes/09/02/cover.png'})
            manifest['quality'].update({'production_gate':'pass','propagation_score':9.4,'s_min_score':8.7,'propagation_decision':'publishable','publish_decision':'go'})
            manifest['publication'].update({'actual_title':'t','description':'d','topics':['x']})
            write_json(ep/'meta/episode-state.json',state); write_json(ep/'meta/release-manifest.json',manifest)
            self.assertIn('propagation_decision_mismatch',{f.code for f in validator.validate_episode(ep,repo,True)})

    def test_absolute_or_outside_repo_path_fails(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); ep=repo/'episodes/09/02'; state=self.base_state('STORYBOARD_LOCKED'); manifest=self.base_manifest(); manifest['artifacts']['storyboard']='../outside.md'; write_json(ep/'meta/episode-state.json',state); write_json(ep/'meta/release-manifest.json',manifest)
            self.assertIn('path_outside_repo',{f.code for f in validator.validate_episode(ep,repo,True)})
            manifest['artifacts']['storyboard']='C:\\temp\\story.md'; write_json(ep/'meta/release-manifest.json',manifest)
            self.assertIn('absolute_path',{f.code for f in validator.validate_episode(ep,repo,True)})

    def test_illegal_state_history_fails(self):
        with tempfile.TemporaryDirectory() as td:
            repo=Path(td); ep=repo/'episodes/09/02'; state=self.base_state('PRODUCTION_PASSED'); state['history']=[{'state':'IDEA_LOCKED','at':'x'},{'state':'PRODUCTION_PASSED','at':'y','mode':'advance','note':'skip'}]; manifest=self.base_manifest(); write_json(ep/'meta/episode-state.json',state); write_json(ep/'meta/release-manifest.json',manifest)
            self.assertIn('illegal_state_history',{f.code for f in validator.validate_episode(ep,repo,True)})

    def test_malformed_history_never_crashes(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            ep = repo / 'episodes/09/02'
            state = self.base_state('STORYBOARD_LOCKED')
            state['history'] = [
                {'state':'IDEA_LOCKED','at':'x','mode':'migration','note':'start'},
                'bad-entry',
                {'state':'BAD','at':'y','mode':'advance','note':'invalid'},
                {'state':'STORYBOARD_LOCKED','at':'z','mode':'advance','note':'tail'},
            ]
            manifest = self.base_manifest()
            storyboard = repo / 'docs/storyboard.md'
            storyboard.parent.mkdir(parents=True, exist_ok=True)
            storyboard.write_text('ok', encoding='utf-8')
            manifest['artifacts']['storyboard'] = 'docs/storyboard.md'
            write_json(ep/'meta/episode-state.json', state)
            write_json(ep/'meta/release-manifest.json', manifest)
            findings = validator.validate_episode(ep, repo, True)
            codes = {f.code for f in findings if f.level == 'FAIL'}
            self.assertIn('state_history_entry', codes)

    def test_production_passed_requires_captions(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            ep = repo / 'episodes/09/02'
            state = self.base_state('PRODUCTION_PASSED')
            manifest = self.base_manifest()
            for rel in ['docs/storyboard.md', 'docs/visual.md', 'docs/production.md']:
                f = repo / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text('ok', encoding='utf-8')
            manifest['artifacts'].update({
                'storyboard':'docs/storyboard.md',
                'visual_spec':'docs/visual.md',
                'production_review':'docs/production.md',
            })
            manifest['quality']['production_gate'] = 'pass'
            write_json(ep/'meta/episode-state.json', state)
            write_json(ep/'meta/release-manifest.json', manifest)
            findings = validator.validate_episode(ep, repo, True)
            self.assertTrue(
                any(f.level == 'FAIL' and 'manifest.artifacts.captions' in f.message for f in findings),
                findings,
            )

    def test_portable_path_syntax_fails(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            ep = repo / 'episodes/09/02'
            state = self.base_state()
            for raw, expected_code in [
                ('C:temp\\story.md', 'absolute_path'),
                ('..\\outside.md', 'non_portable_path'),
            ]:
                with self.subTest(path=raw):
                    manifest = self.base_manifest()
                    manifest['artifacts']['story'] = raw
                    write_json(ep/'meta/episode-state.json', state)
                    write_json(ep/'meta/release-manifest.json', manifest)
                    codes = {f.code for f in validator.validate_episode(ep, repo, True) if f.level == 'FAIL'}
                    self.assertIn(expected_code, codes)

    def test_propagation_threshold_boundaries(self):
        cases = [
            (9.2, 8.5, 'strong'),
            (9.1999, 8.5, 'publishable'),
            (8.7, 7.5, 'publishable'),
            (8.6999, 10.0, 'conditional'),
            (8.3, 7.0, 'conditional'),
            (8.2999, 10.0, 'not_recommended'),
            (10.0, 6.9999, 'not_recommended'),
            (10.0, 8.4999, 'publishable'),
            (10.0, 8.5, 'strong'),
        ]
        for score, s_min, expected in cases:
            with self.subTest(score=score, s_min=s_min):
                self.assertEqual(validator.derive_propagation_decision(score, s_min), expected)


if __name__ == '__main__': unittest.main()
