# -*- coding: utf-8 -*-
import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
led = json.load(open(os.path.join(EP, "meta/production-ledger.json"), encoding="utf-8"))
f1 = led["frames"]["01"]
print("status:", f1.get("status"), "| repairs_used:", f1.get("content_repairs_used"))
print("keys:", list(f1.keys()))
for k in ("events", "history", "audit", "transitions"):
    if k in f1:
        print("==", k)
        print(json.dumps(f1[k], ensure_ascii=False, indent=1)[:3000])
for a in f1.get("attempts", []):
    if a.get("attempt_id") in ("66050a6e0cbd", "447e3ec0e076", "2c7bd4b0bb37", "c59d1604f631"):
        print("==", a.get("attempt_id"), "kind", a.get("kind"), "result", a.get("result"))
        for k in ("notes", "started_at", "completed_at", "request_fingerprint"):
            if k in a:
                print("   ", k, ":", json.dumps(a[k], ensure_ascii=False)[:400])
        if "error" in a:
            print("    error:", json.dumps(a["error"], ensure_ascii=False)[:400])
        if "candidate" in a:
            print("    candidate:", json.dumps(a["candidate"], ensure_ascii=False)[:400])
        if "review" in a:
            print("    review:", json.dumps(a["review"], ensure_ascii=False)[:400])
        if "authorization" in a:
            print("    authorization:", json.dumps(a["authorization"], ensure_ascii=False)[:400])
