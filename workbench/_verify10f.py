import json,os,glob,hashlib
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
print('--- find journals ---')
for p in glob.glob(os.path.join(ep,'meta/**/*journal*'),recursive=True)+glob.glob(os.path.join(ep,'meta/**/*queue*'),recursive=True):
    print(p, os.path.getsize(p))
print('--- prompt files ---')
for p in sorted(glob.glob(os.path.join(ep,'docs/prompts/reveal-order-v2/01*'))):
    b=open(p,'rb').read()
    import datetime
    print(os.path.basename(p), len(b), hashlib.sha256(b).hexdigest()[:24], datetime.datetime.fromtimestamp(os.path.getmtime(p)).isoformat())
print('--- transcripts/trace tail ---')
tp=os.path.join(ep,'meta/runtime/trace-events.jsonl')
if os.path.exists(tp):
    lines=open(tp,encoding='utf-8').read().strip().split('\n')
    print('N',len(lines))
    for l in lines[-12:]:
        e=json.loads(l)
        print(e.get('at') or e.get('timestamp'), e.get('event') or e.get('name'), str(e.get('detail') or e.get('data') or '')[:160])
