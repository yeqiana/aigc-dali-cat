
import json, os, datetime
ep = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
p = os.path.join(ep, "meta/runtime/raw-candidate-budget-override.json")
d = json.load(open(p, encoding="utf-8"))
for r in d.get("per_frame_authorizations", []):
    if r.get("reason", "").startswith("user-directed frame-01 framing fix"):
        r["authorization"]["authorized_at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        print("authorized_at ->", r["authorization"]["authorized_at"])
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

