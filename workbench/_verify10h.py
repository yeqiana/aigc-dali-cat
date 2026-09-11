import json,os,glob,re
ep=r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
d=open(os.path.join(ep,'meta/production-ledger.json'),encoding='utf-8').read()
for m in re.finditer(r'3745e670', d):
    s=max(0,m.start()-320); print('CTX:', d[s:m.end()+120].replace(chr(10),' ')); print('---')
print('=== snapshot search ===')
for p in glob.glob(os.path.join(ep,'**/*snapshot*'),recursive=True)+glob.glob(os.path.join(ep,'**/*deliver*'),recursive=True)+glob.glob(os.path.join(ep,'**/*.zip'),recursive=True):
    print(os.path.relpath(p,r'D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat') if False else p, os.path.getsize(p) if os.path.isfile(p) else 'DIR')
