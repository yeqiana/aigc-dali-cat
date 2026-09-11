
import json,hashlib,pathlib
ep=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')/r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
sub=ep/'meta/subtitles.yaml'
print('subtitles.yaml sha', hashlib.sha256(sub.read_bytes()).hexdigest())
rev=json.loads((ep/'meta/frame-semantic-review.json').read_text(encoding='utf-8'))
print('review keys', list(rev.keys()))
for k in ('status','created_at','attempt','caption_source','caption_source_sha256','summary'):
    if k in rev: print(' ',k, json.dumps(rev[k],ensure_ascii=False)[:200])
fr=rev.get('frames')
if isinstance(fr,dict):
    k0=list(fr)[0]
    print(' frames sample', k0, json.dumps(fr[k0],ensure_ascii=False)[:300])
elif isinstance(fr,list):
    print(' frames sample', json.dumps(fr[0],ensure_ascii=False)[:300])
print(' incremental_contract', json.dumps(rev.get('incremental_contract'),ensure_ascii=False)[:300])

