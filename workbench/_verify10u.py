import json,os
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
d=json.load(open(os.path.join(ep,'meta/delegated-release.json'),encoding='utf-8'))
print(json.dumps(d['package'],ensure_ascii=False,indent=1))
print('N_FILES',len(d['files']))
cov=[f for f in d['files'] if f['role']=='cover']
print('COVER', json.dumps(cov,ensure_ascii=False))
