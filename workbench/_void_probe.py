import json, os, sys, io
sys.stdout.reconfigure(encoding='utf-8')
ep = r"episodes\09_旧物怪谈\05_婚礼前夜_记忆麻醉"
led = json.load(open(os.path.join(ep, "meta", "production-ledger.json"), encoding="utf-8"))
f = led["frames"]["01"]
print("status:", f.get("status"))
print("lock:", json.dumps(f.get("lock"), ensure_ascii=False))
print("approved_asset.sha256:", (f.get("approved_asset") or {}).get("sha256"))
print("current_candidate.sha256:", (f.get("current_candidate") or {}).get("sha256"))
for k in ("content_repairs_used", "user_exception_repairs_used", "authority_refresh_used", "restore_evidence_gap_used"):
    if k in f: print(k, "=", f[k])
att = f.get("attempts") or []
print("attempt count:", len(att))
for a in att[-3:]:
    print("  attempt", a.get("attempt_id"), a.get("kind"), a.get("result"), a.get("started_at"), (a.get("error") or {}).get("code"))
print("has authority_refresh_history:", len(f.get("authority_refresh_history") or []))
print("has superseded_locks:", len(f.get("superseded_locks") or []))
print("has repair_authorization:", bool(f.get("repair_authorization")))
q = json.load(open(os.path.join(ep, "meta", "production-queue.json"), encoding="utf-8"))
for it in q["items"]:
    if it.get("id") in ("87d54b6a927d", "dc4beaa1ea5f"):
        print("QUEUE", it["id"], it["status"], json.dumps(it.get("execution"), ensure_ascii=False))
print("queue_status_summary:", {})
from collections import Counter
print(Counter(i["status"] for i in q["items"]))
lf = os.path.join(ep, "meta", "image-workers", "01-87d54b6a927d-a1.lifecycle.json")
print("lifecycle exists:", os.path.exists(lf))
if os.path.exists(lf):
    print(json.dumps(json.load(open(lf, encoding="utf-8")), ensure_ascii=False)[:1200])
pj = os.path.join(ep, "docs", "prompts", "reveal-order-v2", "01.txt")
print("prompt01 exists:", os.path.exists(pj))
if os.path.exists(pj):
    txt = open(pj, encoding="utf-8").read()
    print("prompt01 len:", len(txt))
    print(txt[:400])
ov = os.path.join(ep, "meta", "runtime", "raw-candidate-budget-override.json")
print("override exists:", os.path.exists(ov))
if os.path.exists(ov):
    print(open(ov, encoding="utf-8").read()[:800])
