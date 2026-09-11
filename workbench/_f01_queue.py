# -*- coding: utf-8 -*-
import os, sys, io, json, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"

def jload(p):
    with open(p, 'rb') as f:
        return json.load(f)

q = jload(os.path.join(EP, "meta/production-queue.json"))
print("queue items summary (frame,id,kind,scope,status,attempts,contract_sha12,completed_at)")
for it in q.get("items", []):
    cs = (it.get("frame_contract") or {}).get("contract_sha256", "")
    print(it.get("frame"), it.get("id"), it.get("kind"), it.get("scope"), it.get("status"), it.get("attempts"), cs[:12], it.get("completed_at") or "", "| err:", (it.get("last_error") or "")[:60])

print()
for d in ["media/candidates/repairs", "media/batch/prompts", "meta/image-workers", "meta/runtime/contracts"]:
    p = os.path.join(EP, d)
    print("==", d, "==")
    if os.path.isdir(p):
        for fn in sorted(os.listdir(p))[:30]:
            print("  ", fn)
    else:
        print("   (missing)")
