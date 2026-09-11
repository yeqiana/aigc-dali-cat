
import json, os
EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
q = json.load(open(os.path.join(EP, "meta/production-queue.json"), encoding="utf-8"))
for it in q.get("items", []):
    if it.get("id") == "dc4beaa1ea5f":
        print(json.dumps(it, ensure_ascii=False, indent=2)[:1800])
print("--- statuses ---")
import collections
print(collections.Counter(x.get("status") for x in q.get("items") or []))
print("updated_at", q.get("updated_at"))
print("--- recent runtime_events ---")
for e in (q.get("runtime_events") or [])[-6:]:
    print(json.dumps(e, ensure_ascii=False)[:300])

