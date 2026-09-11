import json,os
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
d=json.load(open(os.path.join(ep,'meta/production-ledger.json'),encoding='utf-8'))
tot=0
for k,f in d['frames'].items():
    tf=f.get('technical_failures',[])
    tot+=len(tf)
    if k=='01':
        print('F01 tf count',len(tf))
        print('codes',[x['code'] for x in tf])
        print('last',json.dumps(tf[-1],ensure_ascii=False)[:300])
print('TOTAL tf', tot)
