#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
import zipfile
from pathlib import Path

SYSTEM=Path(__file__).resolve().parent; ROOT=SYSTEM.parents[1]

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,SYSTEM/file); m=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(m); return m
backend=load('backend202','codex_subscription_image.py'); delivery=load('delivery202','delegated_delivery.py'); delegated=load('delegated202','delegated_approval.py'); gate=load('gate202','evidence_gate.py'); orch=load('orch202','codex_auto_orchestrator.py')

def pillow():
    from PIL import Image
    return Image

class ClosureTests(unittest.TestCase):
    def setUp(self):
        self.base=ROOT/'workbench'/('.v202-test-'+uuid.uuid4().hex[:8]); self.base.mkdir(parents=True)
    def tearDown(self): shutil.rmtree(self.base,ignore_errors=True)
    def make_img(self,p,size=(1080,1350)):
        Image=pillow(); p.parent.mkdir(parents=True,exist_ok=True); Image.new('RGB',size,(80,90,100)).save(p,'PNG')
    def test_backend_normalizes_to_ledger_canvas(self):
        ep=self.base/'ep'; (ep/'meta').mkdir(parents=True); (ep/'meta/production-ledger.json').write_text(json.dumps({'canvas':{'width':1080,'height':1350,'aspect_ratio':'4:5'}}),encoding='utf-8')
        prompt=ep/'prompt.txt'; prompt.write_text('真实手机随手拍，普通室内，自然光。',encoding='utf-8'); out=ep/'candidate.png'; log=ep/'log.jsonl'
        fake=self.base/'fake_codex.py'; fake.write_text('''import sys\nfrom pathlib import Path\nfrom PIL import Image\na=sys.argv\nwd=Path(a[a.index("-C")+1]) if "-C" in a else Path.cwd()\nImage.new("RGB",(1024,1280),(1,2,3)).save(wd/"out.png")\nsys.exit(0)\n''',encoding='utf-8')
        r=subprocess.run([sys.executable,str(SYSTEM/'codex_subscription_image.py'),'generate-for-frame',str(ep),'--frame','01','--prompt-file',str(prompt),'--output',str(out),'--log',str(log),'--codex',str(fake)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
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
        (ep/'meta/runtime-checkpoint.json').write_text(json.dumps({'continuous_execution_authorized':True,'approval_basis':'delegated_continuous_execution'}),encoding='utf-8')
        ns=type('N',(),{'episode_dir':str(ep),'kind':'story_lock','note':'auto'})(); self.assertEqual(delegated.cmd_record(ns),0); self.assertEqual(delegated.verify(ep,'story_lock'),[])
        ok,msg=gate.run_gate(ep,'STORYBOARD_LOCKED'); self.assertTrue(ok,msg)
        store=json.loads((ep/'meta/delegated-approvals.json').read_text(encoding='utf-8')); item=store['approvals']['story_lock']; self.assertFalse(item['user_approved']); self.assertTrue(item['delegated_auto_review'])
    def test_orchestrator_postflight_pauses_incomplete_ledger(self):
        ep=self.base/'post'; (ep/'meta').mkdir(parents=True)
        (ep/'meta/runtime-checkpoint.json').write_text(json.dumps({'continuous_execution_authorized':True,'approval_basis':'delegated_continuous_execution','failed_frames':[]}),encoding='utf-8')
        (ep/'meta/production-ledger.json').write_text(json.dumps({'canvas':{'aspect_ratio':'4:5','width':1080,'height':1350},'frames':{'01':{'status':'PENDING','content_repairs_used':0,'attempts':[],'approved_asset':None,'lock':None}},'policy':{},'asset_roots':{}}),encoding='utf-8')
        status,reason,pkg=orch.postflight(ep); self.assertEqual(status,'PAUSED'); self.assertIsNone(pkg)

if __name__=='__main__': unittest.main()
