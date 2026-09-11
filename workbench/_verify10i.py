import json,os,glob,hashlib
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
z=os.path.join(ep,'deliveries/05_婚礼前夜_记忆麻醉_DELEGATED_AUTO_F01FACE.zip')
h=hashlib.sha256(open(z,'rb').read()).hexdigest()
print('ZIP', os.path.getsize(z), h)
sn=os.path.join(ep,'meta/final-candidate-snapshot.json')
hs=hashlib.sha256(open(sn,'rb').read()).hexdigest()
print('SNAP_BYTESHA', hs)
d=json.load(open(sn,encoding='utf-8'))
print('SNAP_KEYS', list(d.keys())[:20])
for k in ('snapshot_sha256','sha256','id','build_id'):
    if k in d: print('SNAP',k,d[k])
print('SNAP created', d.get('created_at'), d.get('generated_at'))
print('=== search ab1bd5fb ===')
found=False
for p in glob.glob(os.path.join(ep,'**/*'),recursive=True):
    if os.path.isfile(p) and os.path.getsize(p)<3_000_000:
        try: t=open(p,encoding='utf-8').read()
        except Exception: continue
        if 'ab1bd5fb' in t: print('HIT', p); found=True
print('found',found)
