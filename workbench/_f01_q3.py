
import json, os
EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
q = json.load(open(os.path.join(EP, "meta/production-queue.json"), encoding="utf-8"))
items = q.get("items", [])
print("items now:", len(items))
for it in items[-4:]:
    fc = (it.get("frame_contract") or {}).get("contract_sha256", "")[:12]
    pp = (it.get("prompt_package") or {}).get("scene_prompt_sha256", "")[:12]
    print(it.get("id"), it.get("frame"), it.get("kind"), it.get("scope"), it.get("status"), "attempts", it.get("attempts"), "contract", fc, "prompt", pp, it.get("queued_at"))
print("queue updated_at:", q.get("updated_at"))

