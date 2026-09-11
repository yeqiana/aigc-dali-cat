
import json,hashlib,pathlib,datetime
root=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat'); ep=root/r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
req=json.loads((ep/'meta/.release-critic-request-stdout.json').read_text(encoding='utf-8'))
print('--- request sources ---')
for row in req['source_files']:
    print(row['path'].split('/')[-1], row['sha256'][:12])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
pub=ep/'production/publish'
for n in ('01','02','12'):
    p=pub/(n+'.png')
    print('publish',n, sha(p)[:12], datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime('%m-%d %H:%M'))
c=ep/'production/cover/cover.png'
print('cover', sha(c)[:12], datetime.datetime.fromtimestamp(c.stat().st_mtime).strftime('%m-%d %H:%M'))
for n in ('01','12'):
    a=ep/('media/approved/'+n+'.png')
    print('approved',n, sha(a)[:12], datetime.datetime.fromtimestamp(a.stat().st_mtime).strftime('%m-%d %H:%M'))
for f in ('meta/caption-image-audit.json','meta/subtitle-layout-audit.json'):
    d=json.loads((ep/f).read_text(encoding='utf-8'))
    print('---',f,'keys',list(d.keys())[:14])

