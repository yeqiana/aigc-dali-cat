
import json,pathlib
ep=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')/r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
p=ep/'meta/visual-lock-baseline-review.json'
if p.is_file():
    d=json.loads(p.read_text(encoding='utf-8'))
    s=json.dumps(d,ensure_ascii=False)
    print('baseline review len',len(s))
    import re
    for m in re.finditer(r'.{200}face_box.{400}',s):
        print(m.group(0))
        break
    print('--- keys',list(d.keys()))
else:
    print('missing',p)

