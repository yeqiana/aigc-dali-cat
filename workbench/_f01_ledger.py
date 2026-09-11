# -*- coding: utf-8 -*-
import os, sys, io, json, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
def jload(p):
    with open(p, 'rb') as f:
        return json.load(f)
led = jload(os.path.join(EP, "meta/production-ledger.json"))
print("ledger top keys:", list(led.keys())[:20] if isinstance(led, dict) else type(led))
frames = led.get("frames", {})
print("frames keys:", list(frames.keys())[:30] if isinstance(frames, dict) else 'n/a')
if isinstance(frames, dict):
    f1 = frames.get("1") or frames.get("01")
    print("frame01 ledger:")
    print(json.dumps(f1, ensure_ascii=False, indent=1)[:6000])
else:
    print(json.dumps(led, ensure_ascii=False)[:3000])
