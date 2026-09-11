import json,os,re
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
pk=json.load(open(os.path.join(ep,'meta/runtime/prompt-packages/01.json'),encoding='utf-8'))
print('PKG_KEYS', list(pk.keys()))
for k in pk.keys():
    v=pk[k]
    if isinstance(v,str) and len(v)<80: print(' ',k,'=',v)
print('=== queue ctx ===')
t=open(os.path.join(ep,'meta/production-queue.json'),encoding='utf-8').read()
for m in list(re.finditer('ab1bd5fb',t))[:4]:
    s=max(0,m.start()-260); print('CTX', t[s:m.end()+80].replace(chr(10),' ')); print('--')
print('=== release manifest ===')
rm=json.load(open(os.path.join(ep,'meta/release-manifest.json'),encoding='utf-8'))
print(json.dumps(rm,ensure_ascii=False)[:2200])
