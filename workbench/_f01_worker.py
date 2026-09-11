# -*- coding: utf-8 -*-
import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
def jload(p):
    with open(p, 'rb') as f:
        return json.load(f)
q = jload(os.path.join(EP, "meta/production-queue.json"))
for it in q.get("items", []):
    if it.get("id") == "2c7bd4b0bb37":
        print("QUEUE ITEM 2c7bd4b0bb37 (approved frame01 repair):")
        print(json.dumps(it, ensure_ascii=False, indent=1)[:3000])
p = os.path.join(EP, "meta/image-workers/01-2c7bd4b0bb37-a1.jsonl")
if os.path.exists(p):
    print("")
    print("== worker jsonl 01-2c7bd4b0bb37-a1 ==")
    for ln in open(p, 'rb').read().decode('utf-8', errors='replace').splitlines():
        print(ln[:2200])
