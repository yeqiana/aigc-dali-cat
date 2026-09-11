
import json,pathlib
ep=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')/r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
ca=json.loads((ep/'meta/caption-image-audit.json').read_text(encoding='utf-8'))
print('caption audit summary',json.dumps(ca.get('summary'),ensure_ascii=False))
fr=ca.get('frames')
print('caption frames type',type(fr).__name__, len(fr) if hasattr(fr,'__len__') else '')
if isinstance(fr,list):
    print('first',json.dumps(fr[0],ensure_ascii=False)[:400])
sl=json.loads((ep/'meta/subtitle-layout-audit.json').read_text(encoding='utf-8'))
print('layout summary',json.dumps(sl.get('summary'),ensure_ascii=False))
lf=sl.get('frames')
print('layout frames',type(lf).__name__, len(lf) if hasattr(lf,'__len__') else '')
if isinstance(lf,list):
    print('first',json.dumps(lf[0],ensure_ascii=False)[:400])
print('layout policy',json.dumps(sl.get('policy'),ensure_ascii=False)[:500])

