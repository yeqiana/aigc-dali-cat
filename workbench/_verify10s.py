import json
b=json.load(open('workbench/_void_backup/queue.20260910_171822.bak',encoding='utf-8'))
for it in b['items']:
    if it.get('frame')==1:
        print(it['id'], it.get('status'), it.get('kind'), it.get('scope'))
print('--- ledger backup frame01 status ---')
l=json.load(open('workbench/_void_backup/ledger.20260910_171822.bak',encoding='utf-8'))
f=l['frames']['01']
print('status',f.get('status'),'attempts',len(f.get('attempts',[])),'lock',bool(f.get('lock')))
print('lock', json.dumps(f.get('lock'),ensure_ascii=False)[:300])
print('gen_baseline' , [k for k in f.keys()])
