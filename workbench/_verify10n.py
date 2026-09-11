import json,os
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
p=os.path.join(ep,'meta/runtime/production-reconciliation.json')
print('RECON', open(p,encoding='utf-8').read()[:1500] if os.path.exists(p) else 'MISSING')
c=os.path.join(ep,'meta/runtime/circuit-breaker.json')
print('CB', open(c,encoding='utf-8').read()[:600] if os.path.exists(c) else 'MISSING')
print('--- git status (short) ---')
