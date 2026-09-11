
import json, os
EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
q = json.load(open(os.path.join(EP, "meta/production-queue.json"), encoding="utf-8"))
print("queue keys:", list(q.keys()))
items = q.get("items", [])
print("items:", len(items))
for it in items:
    if it.get("frame") == "01" or it.get("frame") == 1:
        print(json.dumps({k: v for k, v in it.items() if k in ("frame","id","kind","scope","status","attempts","contract_sha256","frame_contract","completed_at","last_error","created_at","updated_at")}, ensure_ascii=False)[:700])
        print("  --")

