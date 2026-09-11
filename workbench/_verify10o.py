import json,os,hashlib,datetime
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
def sh(p):
    return hashlib.sha256(open(p,'rb').read()).hexdigest()
def mt(p):
    return datetime.datetime.fromtimestamp(os.path.getmtime(p)).isoformat()
for rel in ('production/publish/01.png','production/cover/cover.png','meta/final-candidate-snapshot.json','deliveries/05_婚礼前夜_记忆麻醉_DELEGATED_AUTO_F01FACE.zip','meta/runtime/contracts/frames/01.json','docs/prompts/reveal-order-v2/01.txt'):
    p=os.path.join(ep,rel)
    print(rel, os.path.getsize(p), sh(p)[:24], mt(p))
print('--- release lock in manifest ---')
rm=json.load(open(os.path.join(ep,'meta/release-manifest.json'),encoding='utf-8'))
print(json.dumps({k:v for k,v in rm.items() if k in ('release_lock','snapshot','lock','evidence')},ensure_ascii=False)[:1500])
print('MANIFEST_KEYS', list(rm.keys()))
