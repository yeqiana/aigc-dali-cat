
import json,pathlib,zipfile,hashlib
root=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat'); ep=root/r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
d=json.loads((ep/'meta/delegated-release.json').read_text(encoding='utf-8'))
print('built_at',d['built_at'],'basis',d['approval_basis'])
rows={r['role']:r for r in d['files']}
for role in ('release_manifest','body:01','body:12','cover','captions','final_candidate_snapshot'):
    r=rows.get(role)
    if r: print(' ',role,r['path'].split('/')[-1],r['sha256'][:16])
zp=ep/'deliveries'/'05_婚礼前夜_记忆麻醉_DELEGATED_AUTO_F01FACE.zip'
print('zip',zp.name,zp.stat().st_size,hashlib.sha256(zp.read_bytes()).hexdigest()[:16])
with zipfile.ZipFile(zp) as zf:
    names=zf.namelist()
print('zip entries',len(names))
for n in names[:8]: print('  ',n)
print('  ...')
for n in names[-6:]: print('  ',n)
st=json.loads((ep/'meta/episode-state.json').read_text(encoding='utf-8'))
print('state',st['current_state'],st['updated_at'])
snap=json.loads((ep/'meta/final-candidate-snapshot.json').read_text(encoding='utf-8'))
print('snapshot_sha256',snap['snapshot_sha256'][:16],'built_at',snap['built_at'])

