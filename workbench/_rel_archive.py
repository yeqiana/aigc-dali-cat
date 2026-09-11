
import json,pathlib,shutil,hashlib
root=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat'); ep=root/r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
p=ep/'meta/runtime/reviews/release-semantic-attempt-1-request.json'
if p.is_file():
    d=json.loads(p.read_text(encoding='utf-8'))
    print('existing status',d.get('status'),'cover binding',[r['sha256'][:12] for r in d['source_files'] if r['path'].endswith('cover.png')])
    dst=p.with_name(p.name.replace('.json','.superseded-cover-refresh.json'))
    shutil.copy2(p,dst); p.unlink(); print('archived ->',dst.name)

