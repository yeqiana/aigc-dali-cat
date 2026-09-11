
import json, os, glob
from datetime import datetime
ep = r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
# a) queue item
q = json.load(open(os.path.join(ep, 'meta/production-queue.json'), encoding='utf-8'))
items = q.get('items') or q.get('queue') or []
print('queue keys', list(q.keys())[:10], 'items', len(items))
for it in items:
    if it.get('item_id') == '87d54b6a927d' or it.get('frame') in (1, '01'):
        s = json.dumps(it, ensure_ascii=False)
        if '87d54b6a927d' in s:
            print('ITEM:', s[:900])
            break
# b) trace events after 17:00
p = os.path.join(ep, 'meta/runtime/trace-events.jsonl')
rows = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
print('trace rows', len(rows))
for r in rows[-14:]:
    print('  ', r.get('at'), r.get('event'), r.get('name'), str(r.get('attrs'))[:160])
# c) expected output exists?
out = os.path.join(ep, 'media/candidates/scheduled/01-87d54b6a927d-a1.png')
print('expected output exists:', os.path.exists(out))
d = os.path.join(ep, 'media/candidates/scheduled')
if os.path.isdir(d):
    fs = sorted(glob.glob(os.path.join(d, '01-*')), key=os.path.getmtime)
    for f in fs[-6:]:
        print('   cand', os.path.basename(f), datetime.fromtimestamp(os.path.getmtime(f)).strftime('%H:%M:%S'))
# d) automations
ad = r'C:/Users/79873/.codex/automations'
print('automations dir exists:', os.path.isdir(ad))
if os.path.isdir(ad):
    for f in glob.glob(os.path.join(ad, '*', 'automation.toml')):
        print('   ', f)

