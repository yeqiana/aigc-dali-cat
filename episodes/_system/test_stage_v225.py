#!/usr/bin/env python3
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,time
from pathlib import Path
SYSTEM=Path(__file__).resolve().parent; ROOT=SYSTEM.parents[1]
import test_stage_v224 as v224
import visual_profile_bridge_v224 as visual_bridge
import codex_subscription_image
from canvas_normalize import normalize
VERSION="2.2.5"; NON_AUTHORITY="NON_AUTHORITY_TEST_ONLY"
def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def rj(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def wj(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def prepdirs(ep):
 for p in [ep/'media/tests/visual/raw',ep/'media/tests/visual',ep/'meta/tests/logs',ep/'meta/tests/plans']: p.mkdir(parents=True,exist_ok=True)
def scene_of(a):
 s=(getattr(a,'scene',None) or '').strip()
 if getattr(a,'scene_file',None): s=Path(a.scene_file).read_text(encoding='utf-8').strip()
 if not s: raise SystemExit('visual test scene is empty')
 return s
def visual_prepare(a):
 ep=v224.episode(a.episode_dir); v224.need_bootstrap(ep); v224.check_drift(ep); prepdirs(ep)
 s=scene_of(a); vc=visual_bridge.compile_prompt_contract(ep); w,h=v224.canvas(ep); stamp=dt.datetime.now().strftime('%Y%m%d_%H%M%S')
 prompt=ep/'meta/tests/plans'/f'visual-test-{stamp}.txt'; prompt.write_text(s+'\n',encoding='utf-8')
 raw=ep/'media/tests/visual/raw'/f'visual-test-{stamp}.png'; out=ep/'media/tests/visual'/f'visual-test-{stamp}.png'; planp=ep/'meta/tests/visual-test-active-plan.json'
 plan={'version':VERSION,'test_type':'VISUAL_TEST','status':'VISUAL_TEST_NATIVE_IMAGE_REQUIRED','authority':NON_AUTHORITY,'promotion_allowed':False,'route':'MAIN_SESSION_NATIVE_IMAGE','requires':'BOOTSTRAP_VALIDATE_PASS','requires_preproduction':False,'scene':s,'prompt_file':str(prompt.relative_to(ep)),'raw_target':str(raw.relative_to(ep)),'output_target':str(out.relative_to(ep)),'report_target':'meta/tests/visual-test-report.json','visual_profile':{'profile_id':vc['profile_id'],'profile_path':vc['profile_path'],'profile_sha256':vc['profile_sha256'],'authority_source':vc.get('authority_source'),'prompt_contract':vc['text']},'image_model':{'requested':a.image_model,'strict':bool(a.strict_model)},'target_size':[w,h],'provider_size':codex_subscription_image.provider_size(w,h),'created_at':now(),'started_epoch':time.time()}
 plan['native_instruction']=f'Use CURRENT MAIN SESSION image generation exactly once; do not spawn isolated worker. Request {a.image_model}. Save/copy the real image to {raw}. Then run: python -X utf8 scripts/story_test.py visual-finalize "{ep}"'
 wj(planp,plan); print(json.dumps(plan,ensure_ascii=False,indent=2)); return 0
def visual_finalize(a):
 ep=v224.episode(a.episode_dir); v224.need_bootstrap(ep); v224.check_drift(ep); planp=Path(a.plan).resolve() if a.plan else ep/'meta/tests/visual-test-active-plan.json'
 if not planp.is_file(): raise SystemExit(f'VISUAL_TEST_PLAN_MISSING: {planp}')
 p=rj(planp)
 if p.get('authority')!=NON_AUTHORITY or p.get('promotion_allowed') is not False: raise SystemExit('VISUAL_TEST_PLAN_AUTHORITY_INVALID')
 if p.get('status')!='VISUAL_TEST_NATIVE_IMAGE_REQUIRED': raise SystemExit(f"VISUAL_TEST_PLAN_STATE_INVALID: {p.get('status')}")
 vc=visual_bridge.compile_prompt_contract(ep); expected=(p.get('visual_profile') or {}).get('profile_sha256')
 if expected!=vc['profile_sha256']: raise SystemExit(f"VISUAL_TEST_PROFILE_STALE: plan={expected} current={vc['profile_sha256']}")
 raw=ep/p['raw_target']; out=ep/p['output_target']
 if not codex_subscription_image.valid_image(raw): raise SystemExit(f'VISUAL_TEST_IMAGE_MISSING_OR_INVALID: {raw}')
 w,h=map(int,p['target_size']); norm=normalize(raw,out,w,h)
 if not codex_subscription_image.valid_image(out): raise SystemExit(f'VISUAL_TEST_NORMALIZED_IMAGE_INVALID: {out}')
 elapsed=round(max(0,time.time()-p.get('started_epoch',time.time())),2)
 rep={**p,'version':VERSION,'status':'VISUAL_TEST_GENERATED_PENDING_REVIEW','route':'MAIN_SESSION_NATIVE_IMAGE','raw_sha256':sha(raw),'output_sha256':sha(out),'normalization':norm,'total_elapsed_seconds':elapsed,'generation_elapsed_seconds':a.generation_seconds,'review_required':True,'review_rule':'NON_AUTHORITY_TEST_ONLY; cannot become master, Visual Lock admission or Production Frame.','finalized_at':now()}; rep.pop('native_instruction',None)
 wj(ep/'meta/tests/visual-test-report.json',rep); p['status']='VISUAL_TEST_NATIVE_IMAGE_CONSUMED'; p['finalized_report']='meta/tests/visual-test-report.json'; wj(planp,p); print(json.dumps(rep,ensure_ascii=False,indent=2)); return 0
def check(a):
 print(json.dumps({'version':VERSION,'default_visual_route':'MAIN_SESSION_NATIVE_IMAGE','isolated_worker_default':False},ensure_ascii=False,indent=2)); return v224.check(a)
def selftest(a):
 assert NON_AUTHORITY=='NON_AUTHORITY_TEST_ONLY'; assert codex_subscription_image.provider_size(1080,1350)=='1024x1280'; assert not codex_subscription_image.valid_image(Path('__missing__')); print('STORY OS V2.2.5 VISUAL TEST FAST PATH SELF-TEST PASS'); return 0
def main():
 ap=argparse.ArgumentParser(description='Story OS V2.2.5 Visual Test Fast Path'); sub=ap.add_subparsers(dest='cmd',required=True)
 p=sub.add_parser('check'); p.add_argument('episode_dir'); p.set_defaults(func=check)
 p=sub.add_parser('visual'); p.add_argument('episode_dir'); g=p.add_mutually_exclusive_group(required=True); g.add_argument('--scene'); g.add_argument('--scene-file'); p.add_argument('--image-model',default='gpt-image-2'); p.add_argument('--strict-model',action='store_true'); p.add_argument('--worker-route',action='store_true'); p.add_argument('--timeout',type=int,default=600); p.add_argument('--codex'); p.set_defaults(func=lambda a:v224.visual(a) if a.worker_route else visual_prepare(a))
 p=sub.add_parser('visual-finalize'); p.add_argument('episode_dir'); p.add_argument('--plan'); p.add_argument('--generation-seconds',type=float); p.set_defaults(func=visual_finalize)
 p=sub.add_parser('production-smoke'); p.add_argument('episode_dir'); p.add_argument('--frame',required=True); p.add_argument('--prompt-file',required=True); p.add_argument('--image-model',default='gpt-image-2'); p.add_argument('--timeout',type=int,default=600); p.add_argument('--codex'); p.set_defaults(func=v224.production_smoke)
 p=sub.add_parser('self-test'); p.set_defaults(func=selftest); a=ap.parse_args(); return a.func(a)
if __name__=='__main__': raise SystemExit(main())
