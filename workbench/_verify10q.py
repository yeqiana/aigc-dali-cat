import json,os
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
b=json.load(open(os.path.join(ep,'meta/runtime/raw-candidate-budget.json'),encoding='utf-8'))
fr=b['frames']['01']
print('ORIG used',fr['original']['used'],list(fr['original']['claims'].keys()))
print('REPAIR used',fr['repair']['used'])
for cid,c in fr['repair']['claims'].items():
    print(' ',cid, c.get('claimed_at'), 'committed=',c.get('committed'), c.get('reason'))
print('EPISODE', json.dumps(b.get('episode'),ensure_ascii=False) if 'episode' in b else 'n/a')
print('other keys',[k for k in b.keys()])
