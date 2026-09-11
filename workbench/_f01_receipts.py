# -*- coding: utf-8 -*-
import os, sys, io, json, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"

def jload(p):
    with open(p, 'rb') as f:
        return json.load(f)

for p in sorted(glob.glob(os.path.join(EP, "meta/provider-receipts/01-*.json"))):
    j = jload(p)
    s = json.dumps(j, ensure_ascii=False)
    print("=" * 12, os.path.basename(p), len(s), "=" * 12)
    print(s[:2600])
