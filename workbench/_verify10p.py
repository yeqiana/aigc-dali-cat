import json,os,hashlib,re
p=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉/meta/runtime/contracts/frames/01.json'
t=open(p,encoding='utf-8').read()
print('has551', '551c1be4' in t)
d=json.loads(t)
print('KEYS', list(d.keys()))
for k in d.keys():
    if 'sha' in k or 'hash' in k or k in ('contract_id','revision','compiled_at','generated_at','updated_at'):
        print(' ',k,'=',str(d[k])[:120])
