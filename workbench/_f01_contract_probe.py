
import json, os, glob
ep = r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
p = os.path.join(ep, 'meta/runtime/contracts/frames/01.json')
d = json.load(open(p, encoding='utf-8'))
s = json.dumps(d, ensure_ascii=False)
print('contract 01 keys:', list(d.keys()))
import re
for kw in ['正脸', '脸', 'face', 'POV', '第一人称', '自拍', '镜']:
    hits = [m.start() for m in re.finditer(kw, s)]
    print(kw, len(hits))
    for h in hits[:4]:
        print('   ...', s[max(0,h-120):h+120].replace('\n',' '))

