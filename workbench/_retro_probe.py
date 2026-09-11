
import json, os, glob, collections
ep = r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
# 1. image worker logs per frame
logs = glob.glob(os.path.join(ep, 'meta/image-workers/*.jsonl'))
per = collections.Counter()
for p in logs:
    n = os.path.basename(p).split('-')[0]
    per[n] += 1
print('image-worker logs per frame:', dict(sorted(per.items())))
print('total worker logs:', len(logs))
# 2. ledger telemetry
led = json.load(open(os.path.join(ep, 'meta/production-ledger.json'), encoding='utf-8'))
print('ledger top keys:', list(led.keys())[:15])
att = led.get('attempts') or []
print('ledger attempts count:', len(att))
if att:
    c = collections.Counter(a.get('frame') for a in att)
    print('per-frame attempts:', dict(sorted((k, v) for k, v in c.items() if k is not None)))
    kinds = collections.Counter((a.get('kind') or a.get('attempt_kind')) for a in att)
    print('attempt kinds:', dict(kinds))
# 3. perf ledger gaps
perf = json.load(open(os.path.join(ep, 'meta/episode-performance-ledger.json'), encoding='utf-8'))
print('perf stage_wall:', perf.get('summary', {}).get('stage_wall'))
print('perf image_attempts list len:', len(perf.get('image_attempts') or []))

