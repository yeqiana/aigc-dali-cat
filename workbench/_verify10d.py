import json,os,glob
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
d=json.load(open(os.path.join(ep,'meta/production-ledger.json'),encoding='utf-8'))
f=d['frames']['01']
print('USER_EXC', f.get('user_exception_repairs_used'))
last=f['attempts'][-1]
print('LAST', json.dumps(last,ensure_ascii=False)[:1500])
prev=f['attempts'][-2]
print('PREV', json.dumps({k:prev.get(k) for k in ('attempt_id','kind','result','completed_at','started_at')},ensure_ascii=False))
print('---QUEUE---')
q=json.load(open(os.path.join(ep,'meta/production-queue.json'),encoding='utf-8'))
for it in q['items']:
    if it.get('frame')==1:
        print(it['id'], it.get('status'), it.get('kind'), it.get('scope'), it.get('output_path'), str(it.get('last_error'))[:120])
print('---LIFECYCLE FILES frame01---')
for p in sorted(glob.glob(os.path.join(ep,'meta/image-workers/01-*'))):
    print(os.path.basename(p), os.path.getsize(p))
