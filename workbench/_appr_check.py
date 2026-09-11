
import json,pathlib
ep=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')/r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
d=json.loads((ep/'meta/delegated-approvals.json').read_text(encoding='utf-8'))
a=d['approvals']
print('approval kinds:',list(a.keys()))
for k,v in a.items():
    print('===',k,'approved',v.get('approved'),'at',v.get('approved_at'))
    for row in v.get('artifacts') or []:
        print('   -',row.get('role'),row.get('path','').split('/')[-1],str(row.get('sha256'))[:16])
    if v.get('note'): print('   note',v['note'][:200])
snap=json.loads((ep/'meta/final-candidate-snapshot.json').read_text(encoding='utf-8'))
print('=== snapshot sha fields ===')
for k,v in snap.items():
    if 'sha' in k.lower() or k in ('snapshot_id','built_at','status'):
        print(' ',k,str(v)[:80])

