import json, urllib.request
BASE='http://127.0.0.1:8080'
def get(p):
    with urllib.request.urlopen(BASE+p, timeout=10) as r:
        return json.loads(r.read().decode('utf-8'))
s=get('/api/v1/runtime/statuses?limit=50&offset=0')
d=s['data']
out=[{'episode_ref':r['episode_ref'],'stage':r['production_stage'],'src':r['state_source']} for r in d['items']]
import sys
with open('${W}/.codex_tmp/statuses.json'.replace('${W}','D:/workspace/YeQianWorkSpace/yeqian/storyOS'),'w',encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print('wrote', len(out))
