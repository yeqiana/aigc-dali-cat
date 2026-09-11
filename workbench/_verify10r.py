import json,os
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
b=json.load(open(os.path.join(ep,'meta/runtime/raw-candidate-budget.json'),encoding='utf-8'))
ev=b.get('events',[])
print('N_EVENTS',len(ev))
for e in ev[-10:]:
    print(json.dumps(e,ensure_ascii=False)[:300])
print('=== override per_frame authorizations ===')
o=json.load(open(os.path.join(ep,'meta/runtime/raw-candidate-budget-override.json'),encoding='utf-8'))
print(json.dumps(o.get('per_frame_authorizations'),ensure_ascii=False)[:1200])
