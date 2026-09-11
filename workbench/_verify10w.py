import json,os,datetime
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
d=json.load(open(os.path.join(ep,'meta/production-ledger.json'),encoding='utf-8'))
from collections import Counter
print('LEDGER', dict(Counter(f.get('status') for f in d['frames'].values())))
print('NOW', datetime.datetime.now().isoformat())
