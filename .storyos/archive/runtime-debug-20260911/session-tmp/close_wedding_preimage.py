from pathlib import Path
import json,re,sys,hashlib,subprocess
import yaml
R=Path.cwd(); E=R/'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'; A=E/'meta/preimage-revisions/20260909_reveal_order_v2'
sys.path.insert(0,str(R/'episodes/_system'))
import frame_contract,prompt_package
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
subpath=E/'meta/subtitles.yaml'; d=yaml.safe_load(subpath.read_text(encoding='utf-8'))
changes={5:'醒来，脚踝还红着。',7:'他们只叫我新娘子。',12:'车里还有新娘，脚上也带着铁。'}
bp=E/'docs/03_婚礼前夜_20张正式分镜_V2.0.md'; board=bp.read_text(encoding='utf-8')
for n,t in changes.items(): board=board.replace('- 字幕：'+d['frames'][n],'- 字幕：'+t); d['frames'][n]=t
bp.write_text(board,encoding='utf-8')
subpath.write_text('frames:\n'+''.join(f'  {n}: '+json.dumps(t,ensure_ascii=False)+'\n' for n,t in d['frames'].items())+'silent_frames: [20]\nvoice_card:\n'+''.join('  '+k+': '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in d['voice_card'].items()),encoding='utf-8')
idx=frame_contract.compile_all(E)
for n in range(1,21):
    row=frame_contract.compile_frame(E,n)
    excerpt=row['storyboard_frame']['text']
    scene=re.search(r'- 画面：(.*)',excerpt).group(1)
    boundary=re.search(r'- 本帧允许知道：(.*)',excerpt).group(1)
    prompt=scene+'\n信息边界：'+boundary+'\nCP03现场光，4:5，禁电影灯、HDR、文字水印。'
    assert len(prompt)<=260 and len(prompt.encode('utf-8'))<=900,(n,len(prompt))
    path=E/f'docs/prompts/reveal-order-v2/{n:02d}.txt'; path.write_text(prompt+'\n',encoding='utf-8')
    package=prompt_package.compile_frame(E,n,path)
    assert package['frame_contract_sha256']==row['contract_sha256']
errors=frame_contract.verify_all(E); assert not errors,errors
# Confirm evidence records inside the edited source container were not rewritten.
old=json.loads((A/'before/meta/story-gates.json').read_text(encoding='utf-8')); new=json.loads((E/'meta/story-gates.json').read_text(encoding='utf-8'))
for key in ['continuity','environment_contract','frame_directives']:
    old['visual'].pop(key,None); new['visual'].pop(key,None)
assert old==new,'unrelated gate/evidence mutation'
cmds=[['text_audit.py',str(E),'--report',str(A/'text-audit.json')],['evidence_gate.py',str(E),'--target','PUBLISH_READY']]
results=[]
for cmd in cmds:
    r=subprocess.run([sys.executable,'-X','utf8',str(R/'episodes/_system'/cmd[0]),*cmd[1:]],capture_output=True,text=True,encoding='utf-8')
    (A/(cmd[0]+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8'); results.append({'command':cmd[0],'returncode':r.returncode})
assert results[0]['returncode']==0,results
assert results[1]['returncode']!=0,'old release unexpectedly certified revision'
sourcefiles=['docs/02_婚礼前夜_StoryLock_V2.0.md','docs/03_婚礼前夜_20张正式分镜_V2.0.md','docs/04_婚礼前夜_视觉规范_V2.0.md','meta/subtitles.yaml','meta/shot-progression-review.json','meta/story-gates.json']+[f'docs/prompts/reveal-order-v2/{n:02d}.txt' for n in range(1,21)]
record={'revision_id':'20260909_reveal_order_v2','not_episode_stage':True,'user_scope':'处理1-3，先不跑图','image_generation_allowed':False,'independent_review':'PENDING','source_files':{rel:h(E/rel) for rel in sourcefiles},'compiled_contracts':20,'compiled_prompt_packages':20,'contract_verify_errors':errors,'checks':results,'old_evidence_untouched_except_source_contract_sections':True,'old_release_gate':'FAIL_EXPECTED_SOURCE_DRIFT','resume_policy':'不得以旧PUBLISH_READY/旧队列直接生图或交付。本版先完成独立评审；用户授权生图后重建队列，读取docs/prompts/reveal-order-v2。所有合同因Story SHA漂移须重新核验，不能据此直接判定所有图片须重生。','historical_assets':'原图片、ZIP、production-ledger、production-queue、immutable runtime-request、episode-state、release-manifest和snapshot均未主动修改。'}
(A/'revision.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'contracts':20,'packages':20,'verify_errors':errors,'checks':results,'audit':json.loads((A/'text-audit.json').read_text(encoding='utf-8'))['summary']},ensure_ascii=False))
