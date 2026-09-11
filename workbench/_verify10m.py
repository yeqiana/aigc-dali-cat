import json,os,re
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
p=os.path.join(ep,'meta/image-workers/01-87d54b6a927d-a1.jsonl')
print('--- worker jsonl ---')
for l in open(p,encoding='utf-8').read().strip().split('\n'):
    print(l[:260])
print('--- user exception in ledger frame01 ---')
t=open(os.path.join(ep,'meta/production-ledger.json'),encoding='utf-8').read()
for m in list(re.finditer('user_exception',t))[:6]:
    s=max(0,m.start()-400); print('CTX', t[s:m.end()+400].replace(chr(10),' ')); print('--')
