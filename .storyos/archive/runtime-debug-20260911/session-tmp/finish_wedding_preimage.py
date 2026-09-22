exec_source = None
from pathlib import Path
import sys,json,hashlib,shutil,re
ROOT=Path.cwd(); EP=ROOT/'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
sys.path.insert(0,str(ROOT/'episodes/_system'))
import frame_contract,prompt_package
p=EP/'meta/shot-progression-review.json'
d=json.loads(p.read_text(encoding='utf-8')); d['status']='LOCKED'
d['revision_note']='修订规格固定以编译合同；不授予独立评审PASS，不批准旧图片，本轮禁止生图。'
for f in d['frames']:
    n=int(f['frame'])
    f['pov_mode']='P01第一人称主观眼位；仅手脚肩袖局部'
    if n in [7,8,19]: f['anomaly_concealment']['carrier']='mirror'
    if n in [3,11,12]: f['anomaly_concealment']['carrier']='foreground_occlusion'
    if f.get('emotion',{}).get('trigger'): f['emotion']['trigger']=f['visual_function']
    if f.get('interaction',{}).get('action'): f['interaction']['action']=f['action']
    f['capture_purpose']=f['visual_function']
    f['anomaly_logic_stage']=('ordinary' if n<3 or n==6 else 'discovery' if n<9 else 'confirmation' if n<11 else 'spatial_contradiction' if n==11 else 'human_consequence' if n<17 else 'payoff')
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
gpath=EP/'meta/story-gates.json'; backup=EP/'meta/preimage-revisions/20260909_reveal_order_v2/before/meta/story-gates.json'
if not backup.exists(): shutil.copy2(gpath,backup)
g=json.loads(gpath.read_text(encoding='utf-8'))
v=g['visual']; a=v['continuity']['anchors']
a['wardrobe']='P01浅色碎花长袖、深色裤、旧布鞋；01—18不换装，16—18布鞋沾泥；19梦里同衣同姿态，20同碎花袖；男方深色外套。'
a['key_prop']='小白药瓶只在02/13/20按逐帧限制出现；红绣鞋09翻起但不穿；金镯10—15未扣合；红布01—10遮住窗栏，11掀布后才显露。'
segments=v['environment_contract']['segments']
for seg in segments:
    # Segment cues must describe environment, never inject later plot props into earlier frames.
    seg['physical_cues']=['现场可用光照亮关键证据','衣着与空间连续','具体人物和道具严格按本帧指令，不跨帧提前加入']
    if seg['id']=='S2': seg['physical_cues']=['梦境木床边缘与土墙','暗部轻噪点，关键铁链和手部仍清楚']; seg['conditional_effects']=[]
    if seg['id']=='S4': seg['condition']='深夜床边白炽灯仍亮，窗边只接收室内漏光，11栏杆与窗框固定关系须可读'; seg['conditional_effects']=[]
    if seg['id']=='S7': seg['physical_cues']=['沾泥的原布鞋和深色裤脚','院外车灯与检查站灯光']
for f in d['frames']:
    n=int(f['frame']); key=f'{n:02d}'; directive=v['frame_directives'][key]
    directive['required_visual_cues']=[f['action']]
    directive['reveal_boundary']=f['visual_function']
    directive['pov_and_wardrobe']=a['wardrobe']+' P01第一人称，不能出现自己的脸；镜内外同人同衣同姿态。'
    directive['medicine_visibility']=('桌角远侧，瓶高≤画高6%，面积≤1%，无递药或盯视' if n==2 else '男人递药并堵前门，瓶高≤画高15%' if n==13 else '远桌角小瓶高≤画高5%，面积≤0.5%，不抢主体' if n==20 else '禁止药瓶入画')
    if n==3: directive['scale_reference']='床脚与短铁链，链的两端不入画'
    if n==4: directive['scale_reference']='手掌与床沿'
    if n==15: directive['scale_reference']='未扣合金镯与女主左手、男人伸来的手'
gpath.write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(frame_contract.compile_all(EP),ensure_ascii=False))
for n in range(1,21): prompt_package.compile_frame(EP,n,EP/f'docs/prompts/reveal-order-v2/{n:02d}.txt')
print('VERIFY',frame_contract.verify_all(EP))
