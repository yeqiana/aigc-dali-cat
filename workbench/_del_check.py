
import json,pathlib
ep=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')/r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
for name in ('delegated-release.json','delegated-approvals.json'):
    p=ep/'meta'/name
    d=json.loads(p.read_text(encoding='utf-8'))
    print('===',name, 'keys', list(d.keys()))
    s=json.dumps(d,ensure_ascii=False,indent=1)
    print(s[:2500])
    print('...')

