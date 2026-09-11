import json,os,hashlib
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
d=json.load(open(os.path.join(ep,'meta/delegated-release.json'),encoding='utf-8'))
print('KEYS',list(d.keys()))
print(json.dumps(d,ensure_ascii=False)[:1800])
st=json.load(open(os.path.join(ep,'meta/episode-state.json'),encoding='utf-8'))
print('STATE', st.get('current_state'))
p1=os.path.join(ep,'docs/prompts/reveal-order-v2/01.txt')
t=open(p1,encoding='utf-8-sig').read()
print('NORM_SHA', hashlib.sha256(t.strip().encode()).hexdigest())
print('RAW_SHA', hashlib.sha256(open(p1,'rb').read()).hexdigest())
