# -*- coding: utf-8 -*-
import os, sys, io, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"

def jload(p):
    try:
        with open(p, 'rb') as f:
            return json.load(f)
    except Exception as e:
        return {"_error": str(e)}

def dump(title, obj, maxlen=7000):
    s = json.dumps(obj, ensure_ascii=False, indent=1)
    print("=" * 15, title, "=" * 15)
    print(s[:maxlen])

for rel in ["meta/delegated-approvals.json", "meta/delegated-release.json", "meta/release-manifest.json", "meta/final-candidate-snapshot.json", "meta/publish-compliance.json"]:
    dump(rel, jload(os.path.join(EP, rel)), 7000)

led = jload(os.path.join(EP, "meta/production-ledger.json"))
items = led.get("items", led.get("entries", led)) if isinstance(led, dict) else led
print("=" * 15, "ledger frame01 rows", "=" * 15)
if isinstance(items, dict):
    rows = items.get("rows", [])
else:
    rows = items
for r in rows if isinstance(rows, list) else []:
    if str(r.get("frame")) == "1" or "frame-01" in str(r.get("item_id", "")) or "01-" == str(r.get("item_id", ""))[:3]:
        print(json.dumps(r, ensure_ascii=False)[:1200])
