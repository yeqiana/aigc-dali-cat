
import json, os, datetime
ep = r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
p = os.path.join(ep, 'meta/production-ledger.json')
st = os.stat(p)
print('ledger mtime', datetime.datetime.fromtimestamp(st.st_mtime))
d = json.load(open(p, encoding='utf-8'))
print('updated_at', d.get('updated_at'))
f1 = d['frames']['01']
print('frame01 status', f1.get('status'))
print('attempts', len(f1.get('attempts') or []))
for a in (f1.get('attempts') or [])[-4:]:
    print('  ', a.get('attempt_id'), a.get('attempt_kind') or a.get('kind'), a.get('status'), a.get('started_at'), a.get('ended_at'), str(a.get('error_code') or '')[:60])
print('current_candidate', json.dumps(f1.get('current_candidate'), ensure_ascii=False)[:200])
print('approved_asset', json.dumps(f1.get('approved_asset'), ensure_ascii=False)[:200])
print('lock', json.dumps(f1.get('lock'), ensure_ascii=False)[:200])
print('technical_failures tail', json.dumps((f1.get('technical_failures') or [])[-2:], ensure_ascii=False)[:300])

