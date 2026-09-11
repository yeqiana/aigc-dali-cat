# -*- coding: utf-8 -*-
import os, sys, io, json, glob, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"

def jload(p):
    try:
        with open(p, 'rb') as f:
            return json.load(f)
    except Exception as e:
        return {"_error": str(e)}

def dump(title, obj, maxlen=6000):
    s = json.dumps(obj, ensure_ascii=False, indent=1)
    print("=" * 15, title, "=" * 15)
    print(s[:maxlen])

# media files
exts = ('.png', '.jpg', '.jpeg', '.zip', '.mp4')
media = []
for root, dirs, files in os.walk(EP):
    dirs[:] = [d for d in dirs if d != 'meta']
    for fn in files:
        if fn.lower().endswith(exts):
            p = os.path.join(root, fn)
            media.append((p, os.path.getsize(p)))
media.sort()
print("=" * 15, "MEDIA FILES", "=" * 15)
for p, sz in media:
    print("%12d  %s" % (sz, p))

for rel in ["meta/runtime/contracts/frames/01.json", "meta/runtime/prompt-packages/01.json"]:
    dump(rel, jload(os.path.join(EP, rel)))
