
import json, os
ep = r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
led = json.load(open(os.path.join(ep, 'meta/production-ledger.json'), encoding='utf-8'))
fr = led['frames']
for k in ['01','02','04','12']:
    v = fr[k]
    print(k, 'status=', v.get('status'), 'content_repairs_used=', v.get('content_repairs_used'),
          'technical_failures=', v.get('technical_failures'), 'attempts=', len(v.get('attempts') or []))
print()
print('frames with content_repairs_used>0:',
      [k for k, v in fr.items() if (v.get('content_repairs_used') or 0) > 0])
print('frames with technical_failures>0:',
      [k for k, v in fr.items() if (v.get('technical_failures') or 0) > 0])
print('repair_authorization on 01:', json.dumps(fr['01'].get('repair_authorization'), ensure_ascii=False)[:600])
print('authority_refresh_history len 01:', len(fr['01'].get('authority_refresh_history') or []))
print('superseded_locks len 01:', len(fr['01'].get('superseded_locks') or []))
# attempt kind breakdown for frame 01
kinds = [(a.get('attempt_kind') or a.get('kind'), a.get('status')) for a in (fr['01'].get('attempts') or [])]
print('frame01 attempts:', kinds)

