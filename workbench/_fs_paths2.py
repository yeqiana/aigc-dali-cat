
import json,pathlib
ep=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')/r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
for n in ('01','12','20'):
    p=ep/'meta/frame-reviews'/f'{n}.json'
    d=json.loads(p.read_text(encoding='utf-8'))
    print(n,'keys',list(d.keys()))
    print('   caption_sha256',d.get('caption_sha256'))
snap=json.loads((ep/'meta/final-candidate-snapshot.json').read_text(encoding='utf-8'))
rows=snap.get('delivery_files') or snap.get('files') or []
print('snapshot row count',len(rows))
for r in rows:
    role=str(r.get('role'))
    if role.startswith('frame_review') or 'semantic' in role or 'incremental' in role:
        print(' ',role, r.get('path'))

