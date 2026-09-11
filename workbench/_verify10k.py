import json,os
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
c=json.load(open(os.path.join(ep,'meta/runtime/contracts/frames/01.json'),encoding='utf-8'))
t=json.dumps(c,ensure_ascii=False)
print('CONTRACT_LEN',len(t))
import re
for kw in ('closeup','特写','近景','正脸','frontface','capture_id','revision'):
    for m in list(re.finditer(kw,t))[:3]:
        s=max(0,m.start()-200); print(kw,'>>>',t[s:m.end()+200]); print('--')
print('=== lifecycle of locked candidate ===')
lc=json.load(open(os.path.join(ep,'meta/image-workers/01-0d0b9814d146-a1.lifecycle.json'),encoding='utf-8'))
print(json.dumps(lc,ensure_ascii=False)[:1400])
