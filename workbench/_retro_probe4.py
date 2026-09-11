
import json, os, collections
ep = r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
led = json.load(open(os.path.join(ep, 'meta/production-ledger.json'), encoding='utf-8'))
fr = led['frames']
codes = collections.Counter()
per_frame = collections.Counter()
for k, v in fr.items():
    for f in (v.get('technical_failures') or []):
        codes[f.get('code')] += 1
        per_frame[k] += 1
print('failure codes:', dict(codes))
print('failures per frame:', dict(sorted(per_frame.items())))
print('total failures:', sum(codes.values()))
print('frames with failures:', len(per_frame))
# silent-no-image count
silent = 0
for k, v in fr.items():
    for f in (v.get('technical_failures') or []):
        if 'no_valid_image=true' in (f.get('message') or ''):
            silent += 1
print('rc=0/rc=1 no_valid_image failures:', silent)
# content repairs total
print('content_repairs_used total:', sum((v.get('content_repairs_used') or 0) for v in fr.values()))
attempt_kinds = collections.Counter()
for k, v in fr.items():
    for a in (v.get('attempts') or []):
        attempt_kinds[a.get('attempt_kind') or a.get('kind')] += 1
print('attempt kinds:', dict(attempt_kinds))

