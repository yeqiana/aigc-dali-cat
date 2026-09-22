import json
base = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
for p in ["meta/runtime/contracts/frames/01.json", "meta/runtime/prompt-packages/01.json"]:
    data = json.load(open(base + "/" + p, encoding="utf8"))
    s = json.dumps(data, ensure_ascii=False, indent=1)
    print("=====", p, "len", len(s))
    print(s[:5200])

