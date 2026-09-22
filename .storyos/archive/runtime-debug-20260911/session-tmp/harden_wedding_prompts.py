from pathlib import Path
import json,re,sys,hashlib
R=Path.cwd(); E=R/'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'; A=E/'meta/preimage-revisions/20260909_reveal_order_v2'
sys.path.insert(0,str(R/'episodes/_system'))
import frame_contract,prompt_package
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
# frame -> medicine visibility exclusion (mirrors doc03 totals)
bottle={
 1:'画面中不得出现药瓶、药片、铁链、铁栏。',
 2:'小白瓶只在远侧桌角，瓶高不超过画高6%，面积不超过画面1%，不特写、不发光。',
 3:'画面中不得出现药、脚镣全貌、人脸。',
 4:'画面中不得出现药、杯瓶、嘴、完整锁链、来者袖口与脸。',
 5:'画面中不得出现药、铁环、递药动作。',
 6:'画面中不得出现药。',
 7:'画面中不得出现药，不生成任何文字。',
 8:'画面中不得出现药。',
 9:'画面中不得出现药；铁环只焊在鞋底，不套在脚上。',
 10:'画面中不得出现药；镯子未扣合，不展示开锁。',
 11:'画面中不得出现药；其余红布仍完整遮挡，一次发现动作。',
 12:'画面中不得出现药；女主不坐车厢、不穿红嫁衣。',
 13:'小白瓶瓶高不超过画高15%，只作为递药动作的一部分。',
 14:'画面中不出现药瓶，只有落到湿土上的药。',
 15:'画面中不得出现药；镯子仍未扣合。',
 16:'画面中不得出现药，不得出现其他女孩替她开门。',
 17:'画面中不得出现药、白婚纱、脚镣。',
 18:'画面中不得出现药、白婚纱。',
 19:'画面中不得出现药、白婚纱；镜内外同人同坐姿同衣。',
 20:'小白瓶只在远侧床头桌边，瓶高不超过画高5%，面积不超过画面0.5%，不抢主体。',
}
always='整体不得出现清晰正脸、第三人称旁观、电影布光、HDR、文字、水印。'
for n in range(1,21):
    p=E/f'docs/prompts/reveal-order-v2/{n:02d}.txt'
    p.write_text(p.read_text(encoding='utf-8').rstrip()+'\n'+bottle[n]+'\n'+always+'\n',encoding='utf-8')
    s=p.read_text(encoding='utf-8').strip()
    assert len(s)<=260,(n,'chars',len(s))
    assert len(s.encode('utf-8'))<=900,(n,'bytes',len(s.encode('utf-8')))
    pkg=prompt_package.compile_frame(E,n,p)
    assert pkg['frame_contract_sha256']==frame_contract.compile_frame(E,n)['contract_sha256']
errs=frame_contract.verify_all(E); assert not errs,errs
rec=A/'revision.json'; r=json.loads(rec.read_text(encoding='utf-8'))
for n in range(1,21): r['source_files'][f'docs/prompts/reveal-order-v2/{n:02d}.txt']=h(E/f'docs/prompts/reveal-order-v2/{n:02d}.txt')
r['prompt_hardening']={'note':'新增逐帧药瓶范围与全局排除词，2026-09-09 复核后发现首版短提示词缺排除项','global_exclusions':'清晰正脸/第三人称/电影布光/HDR/文字/水印'}
rec.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prompts_hardened':20,'verify_errors':errs},ensure_ascii=False))
