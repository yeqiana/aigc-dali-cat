import json,hashlib,os,glob
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
d=json.load(open(os.path.join(ep,'meta/production-ledger.json'),encoding='utf-8'))
f=d['frames']['01']
print('LOCK', json.dumps(f.get('lock'),ensure_ascii=False)[:1400])
print('SUPERSEDED', json.dumps(f.get('superseded_locks'),ensure_ascii=False)[:900])
print('REPAIR_AUTH', json.dumps(f.get('repair_authorization'),ensure_ascii=False)[:700])
print('N_ATTEMPTS', len(f.get('attempts',[])))
print('ATT_STATUS', [a.get('result') for a in f.get('attempts',[])])
print('ATT_KIND', [a.get('kind') for a in f.get('attempts',[])])
for p in glob.glob(os.path.join(ep,'meta/runtime/prompt-packages/*')):
    print('PKG', os.path.basename(p), os.path.getsize(p))
for p in glob.glob(os.path.join(ep,'meta/runtime/*.json')):
    print('RT', os.path.basename(p))
