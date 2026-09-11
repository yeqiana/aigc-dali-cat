import json,os,glob,hashlib
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
lc=os.path.join(ep,'meta/image-workers/01-87d54b6a927d-a1.lifecycle.json')
print('LC',open(lc,encoding='utf-8').read()[:900])
print('--- journal tail ---')
jp=os.path.join(ep,'meta/runtime/queue-journal.jsonl')
lines=open(jp,encoding='utf-8').read().strip().split('\n')
print('N',len(lines))
for l in lines[-14:]:
    e=json.loads(l)
    print(e.get('at'), e.get('event'), e.get('item_id'), str(e.get('detail') or e.get('message') or '')[:150])
print('--- prompt files ---')
for p in sorted(glob.glob(os.path.join(ep,'docs/prompts/reveal-order-v2/01.txt*'))):
    b=open(p,'rb').read()
    print(os.path.basename(p), len(b), hashlib.sha256(b).hexdigest(), os.path.getmtime(p))
