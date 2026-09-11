import json,hashlib,os
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
d=json.load(open(os.path.join(ep,'meta/production-ledger.json'),encoding='utf-8'))
f=d['frames']['01']
print('STATUS',f['status'])
print('KEYS',[k for k in f.keys() if 'sha' in k or 'lock' in k or 'repair' in k or 'attempt' in k])
print(json.dumps({k:v for k,v in f.items() if k!='technical_failures'},ensure_ascii=False)[:2500])
p=os.path.join(ep,'docs/prompts/reveal-order-v2/01.txt')
raw=open(p,'rb').read()
print('PROMPT_SHA_FILE',hashlib.sha256(raw).hexdigest())
print('PROMPT_RB',len(raw))
