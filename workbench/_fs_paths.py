
import json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')/'episodes/_system'))
import frame_semantic_review as fsr
ep=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')/r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
print('SUMMARY_REL',fsr.SUMMARY_REL)
print('review path 01',fsr._review_path(ep,'01'))
p=fsr._review_path(ep,'01')
d=json.loads(p.read_text(encoding='utf-8'))
print('keys',list(d.keys()))
print('has caption_sha256:', 'caption_sha256' in d)
snap=json.loads((ep/'meta/final-candidate-snapshot.json').read_text(encoding='utf-8'))
rows=snap.get('delivery_files') or snap.get('files') or []
for r in rows:
    role=str(r.get('role'))
    if role.startswith('frame_review') or role in ('frame_semantic_review','frame_semantic_audit','incremental_frame_audit'):
        print(role, r.get('path'))

