import json,os,glob,hashlib
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
tp=os.path.join(ep,'meta/runtime/trace-events.jsonl')
lines=open(tp,encoding='utf-8').read().strip().split('\n')
print('LASTTRACE', lines[-1][:600])
print('--- search 3745e670 in ledger ---')
d=open(os.path.join(ep,'meta/production-ledger.json'),encoding='utf-8').read()
print('hit3745', '3745e670' in d)
print('hit48d5be', '48d5be97' in d)
print('--- snapshot / deliveries ---')
for p in glob.glob(os.path.join(ep,'release/**/*'),recursive=True):
    if os.path.isfile(p):
        print('REL', os.path.relpath(p,ep), os.path.getsize(p))
