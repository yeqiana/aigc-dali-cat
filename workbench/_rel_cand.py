
import pathlib,json
ep=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')/r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
p=ep/'meta/.release-semantic-review.candidate.json'
raw=p.read_bytes()
print('bytes',len(raw))
print('head',raw[:300])
t=raw.decode('utf-8-sig',errors='replace')
print('stripped head',t.lstrip()[:200])
try:
    d=json.loads(t.lstrip().removeprefix('```json').removeprefix('```').rsplit('```',1)[0] if '```' in t else t)
    print('parsed-with-strip keys',list(d.keys()))
except Exception as e:
    print('still failing',e)

