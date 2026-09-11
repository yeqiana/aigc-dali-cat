import json
base = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
p = base + "/meta/provider-receipts/01-1788935240.json"
d = json.load(open(p, encoding="utf8"))
s = json.dumps(d, ensure_ascii=False, indent=1)
print("len", len(s))
print(s[:5200])

