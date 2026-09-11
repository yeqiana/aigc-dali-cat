
import json, os, collections
ep = r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
led = json.load(open(os.path.join(ep, 'meta/production-ledger.json'), encoding='utf-8'))
fr = led.get('frames')
print('frames type', type(fr))
if isinstance(fr, dict):
    keys = list(fr.keys())[:3]
    print('sample frame keys', keys)
    f1 = fr.get('01') or fr.get(keys[0])
    print('frame01 subkeys', list(f1.keys()) if isinstance(f1, dict) else f1)
tot = collections.Counter()
kind = collections.Counter()
for k, v in (fr or {}).items():
    atts = (v or {}).get('attempts') or []
    tot[k] = len(atts)
    for a in atts:
        kind[(a.get('kind') or a.get('attempt_kind') or a.get('status'))] += 1
print('attempts per frame:', dict(sorted(tot.items())))
print('attempt status/kind totals:', dict(kind))
print('batches:', json.dumps(led.get('batches'), ensure_ascii=False)[:400])

