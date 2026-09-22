import json
base = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
d = json.load(open(base + "/meta/delegated-approvals.json", encoding="utf8"))
print(json.dumps(d, ensure_ascii=False, indent=1)[:6500])

