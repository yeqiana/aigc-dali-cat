import json,os,glob,datetime
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
print('=== void backup ===')
for p in glob.glob('workbench/_void_backup/**/*',recursive=True):
    if os.path.isfile(p):
        st=os.stat(p)
        print(p, st.st_size, datetime.datetime.fromtimestamp(st.st_mtime).isoformat())
print('=== workbench _void scripts ===')
for p in glob.glob('workbench/_void*.py')+glob.glob('workbench/_retro_void*.py'):
    st=os.stat(p); print(p, st.st_size, datetime.datetime.fromtimestamp(st.st_mtime).isoformat())
print('=== budget files ===')
b=json.load(open(os.path.join(ep,'meta/runtime/raw-candidate-budget.json'),encoding='utf-8'))
print(json.dumps(b,ensure_ascii=False)[:900])
o=os.path.join(ep,'meta/runtime/raw-candidate-budget-override.json')
print('OVERRIDE', open(o,encoding='utf-8').read()[:700] if os.path.exists(o) else 'MISSING')
print('=== frame01 queue items exec ===')
q=json.load(open(os.path.join(ep,'meta/production-queue.json'),encoding='utf-8'))
for it in q['items']:
    if it['id'] in ('dc4beaa1ea5f','87d54b6a927d','0d0b9814d146'):
        print(it['id'], it.get('status'), it.get('created_at'), json.dumps(it.get('execution'),ensure_ascii=False)[:400])
