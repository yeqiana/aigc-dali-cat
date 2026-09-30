#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
import zipfile
from unittest.mock import patch
from pathlib import Path

SYSTEM=Path(__file__).resolve().parent; ROOT=SYSTEM.parents[1]

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,SYSTEM/file); m=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(m); return m
backend=load('backend202','codex_subscription_image.py'); delivery=load('delivery202','delegated_delivery.py'); delegated=load('delegated202','delegated_approval.py'); gate=load('gate202','evidence_gate.py'); orch=load('orch202','codex_auto_orchestrator.py')

def _test_mysql_setup():
    """Bootstrap only the generation-authority tables in the TEST_ONLY MySQL container."""
    import subprocess
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.schema_v2 import DATABASE_NAME, DDL_STEPS

    inspected = subprocess.run(["docker", "inspect", "storyos-phase0a-mysql"], check=True,
                               capture_output=True, text=True)
    data = json.loads(inspected.stdout)[0]
    container_env = {}
    for item in data["Config"].get("Env", []):
        if "=" in item:
            key, value = item.split("=", 1)
            container_env[key] = value
    connection_kwargs = {
        "host": "127.0.0.1", "port": 3306, "database": DATABASE_NAME,
        "user": container_env.get("MYSQL_USER") or "root",
        "password": container_env.get("MYSQL_PASSWORD") or container_env.get("MYSQL_ROOT_PASSWORD") or "",
    }
    connection = MySqlConnection(**connection_kwargs)
    connection.health_check()
    for name, sql in DDL_STEPS:
        if name in {"create_generation_asset_state", "create_generation_attempt"}:
            connection.execute(sql)
    connection.close()
    # The production config already points at this TEST_ONLY endpoint; pass the
    # container credentials to the spawned generator without exposing them.
    env = {
        "STORYOS_MYSQL_HOST": "127.0.0.1",
        "STORYOS_MYSQL_PORT": "3306",
        "STORYOS_MYSQL_USER": connection_kwargs["user"],
        "STORYOS_MYSQL_DB": DATABASE_NAME,
        "STORYOS_MYSQL_PWD": connection_kwargs["password"],
        "STORYOS_EPISODE_META_STORE_MODE": "mysql",
    }
    return patch.dict(os.environ, env)

def pillow():
    from PIL import Image
    return Image

class ClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.mysql_env = _test_mysql_setup()
            cls.mysql_env.start()
        except Exception as exc:
            raise unittest.SkipTest(f"TEST_ONLY MySQL container unavailable: {exc}")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "mysql_env"):
            cls.mysql_env.stop()

    def setUp(self):
        self.base=ROOT/'workbench'/('.v202-test-'+uuid.uuid4().hex[:8]); self.base.mkdir(parents=True)
    def tearDown(self): shutil.rmtree(self.base,ignore_errors=True)
    def make_img(self,p,size=(1080,1350)):
        Image=pillow(); p.parent.mkdir(parents=True,exist_ok=True); Image.new('RGB',size,(80,90,100)).save(p,'PNG')
    def test_backend_normalizes_to_ledger_canvas(self):
        ep=self.base/'ep'; (ep/'meta').mkdir(parents=True); (ep/'meta/production-ledger.json').write_text(json.dumps({'canvas':{'width':1080,'height':1350,'aspect_ratio':'4:5'}}),encoding='utf-8')
        prompt=ep/'prompt.txt'; prompt.write_text('真实手机随手拍，普通室内，自然光。',encoding='utf-8'); out=ep/'candidate.png'; log=ep/'log.jsonl'
        # Exercise the real backend and Attempt Gateway, but keep the Provider
        # boundary deterministic. This contract test must never call image_generation.
        def fake_codex_run(command, **kwargs):
            image = pillow()
            image.new('RGB', (1024, 1280), (1, 2, 3)).save(Path(kwargs['cwd']) / 'out.png')
            return subprocess.CompletedProcess(command, 0, '', '')
        from unittest.mock import patch
        argv = [str(SYSTEM/'codex_subscription_image.py'),'generate-for-frame',str(ep),
                '--frame','01','--prompt-file',str(prompt),'--output',str(out),
                '--log',str(log),'--codex','test-only-stub']
        with patch.object(backend.codex_user_runner, 'bridge_required', return_value=False), \
             patch.object(backend.codex_user_runner, 'run_codex', side_effect=fake_codex_run), \
             patch.object(backend, 'image_runtime_preflight', return_value={}), \
             patch.object(sys, 'argv', argv):
            self.assertEqual(backend.main(), 0)
        Image=pillow()
        with Image.open(out) as im:self.assertEqual(im.size,(1080,1350))
        self.assertTrue(any((ep/'media/raw').glob('01-*.png')))
    def setup_release(self):
        ep=self.base/'release'; (ep/'meta').mkdir(parents=True); (ep/'production/publish').mkdir(parents=True); (ep/'docs').mkdir()
        self.make_img(ep/'production/publish/01.png'); self.make_img(ep/'cover.png')
        for name,txt in [('captions.yaml','frames:\n  1: test\n'),('publish.md','# title\n'),('prop.md','score\n')]: (ep/'docs'/name).write_text(txt,encoding='utf-8')
        rel=lambda p:p.resolve().relative_to(ROOT.resolve()).as_posix()
        manifest={'tool_version':'2.0.2','episode':{'id':'T','title':'T','aspect_ratio':'4:5'},'release':{'body_frame_count':1,'publish_dir':rel(ep/'production/publish'),'body_glob':'[0-9][0-9].png','cover_path':rel(ep/'cover.png')},'artifacts':{'captions':rel(ep/'docs/captions.yaml'),'publish_copy':rel(ep/'docs/publish.md'),'propagation_card':rel(ep/'docs/prop.md')}}
        (ep/'meta/release-manifest.json').write_text(json.dumps(manifest),encoding='utf-8'); (ep/'meta/text-audit.json').write_text(json.dumps({'summary':{'passed':True},'source_sha256':'x'*64}),encoding='utf-8')
        (ep/'meta/runtime-checkpoint.json').write_text(json.dumps({'continuous_execution_authorized':True,'approval_basis':'delegated_continuous_execution'}),encoding='utf-8')
        return ep
    def test_delivery_machine_gate_legacy_boundary(self):
        ep=self.setup_release()
        self.assertFalse(delivery.machine_gate_required_for_delivery(ep))
        manifest_path=ep/'meta/release-manifest.json'
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        manifest['tool_version']='2.0.3.3'
        manifest_path.write_text(json.dumps(manifest),encoding='utf-8')
        self.assertTrue(delivery.machine_gate_required_for_delivery(ep))

    def test_delegated_delivery_is_complete_and_verified(self):
        ep=self.setup_release(); z=delivery.build(ep,'TEST'); self.assertEqual(delivery.verify(ep),[])
        with zipfile.ZipFile(z) as f:
            names=set(f.namelist()); self.assertIn('publish/01.png',names); self.assertIn('checksums.sha256',names); self.assertIn('release-manifest.json',names); self.assertTrue(any(x.startswith('text/') for x in names))
        (ep/'production/publish/01.png').unlink()
        with self.assertRaises(SystemExit): delivery.build(ep,'NOFALLBACK')
    def test_delegated_story_lock_passes_stable_gate(self):
        ep=self.base/'gate'; (ep/'meta').mkdir(parents=True); (ep/'docs').mkdir();
        (ep/'docs/story.md').write_text('story',encoding='utf-8'); (ep/'docs/board.md').write_text('board',encoding='utf-8')
        rel=lambda p:p.resolve().relative_to(ROOT.resolve()).as_posix()
        (ep/'meta/release-manifest.json').write_text(json.dumps({'tool_version':'2.0.2','artifacts':{'story':rel(ep/'docs/story.md'),'storyboard':rel(ep/'docs/board.md')},'episode':{}}),encoding='utf-8')
        (ep/'meta/episode-state.json').write_text(json.dumps({'tool_version':'2.0.2','current_state':'IDEA_LOCKED'}),encoding='utf-8')
        (ep/'meta/story-gates.json').write_text(json.dumps({'approvals':{}}),encoding='utf-8')
        # This test exercises the file-backed checkpoint contract explicitly. Save
        # via the authority API; a hand-written projection is not authoritative when
        # the production config selects MySQL.
        import runtime_checkpoint
        with patch.object(runtime_checkpoint.runtime_checkpoint_persistence, "mode", return_value="json"):
            runtime_checkpoint.save(ep, runtime_checkpoint.ensure_shape({
                'continuous_execution_authorized': True,
                'approval_basis': 'delegated_continuous_execution',
            }))
            ns=type('N',(),{'episode_dir':str(ep),'kind':'story_lock','note':'auto'})(); self.assertEqual(delegated.cmd_record(ns),0); self.assertEqual(delegated.verify(ep,'story_lock'),[])
            ok,msg=gate.run_gate(ep,'STORYBOARD_LOCKED'); self.assertTrue(ok,msg)
        store=delegated.approval_persistence.load(ep, delegated.approval_persistence.DELEGATED_BUNDLE); item=store['approvals']['story_lock']; self.assertFalse(item['user_approved']); self.assertTrue(item['delegated_auto_review'])
    def test_orchestrator_postflight_pauses_incomplete_ledger(self):
        ep=self.base/'post'; (ep/'meta').mkdir(parents=True)
        (ep/'meta/runtime-checkpoint.json').write_text(json.dumps({'continuous_execution_authorized':True,'approval_basis':'delegated_continuous_execution','failed_frames':[]}),encoding='utf-8')
        (ep/'meta/production-ledger.json').write_text(json.dumps({'canvas':{'aspect_ratio':'4:5','width':1080,'height':1350},'frames':{'01':{'status':'PENDING','content_repairs_used':0,'attempts':[],'approved_asset':None,'lock':None}},'policy':{},'asset_roots':{}}),encoding='utf-8')
        status,reason=orch.postflight(ep); self.assertEqual(status,'PAUSED')

if __name__=='__main__': unittest.main()
