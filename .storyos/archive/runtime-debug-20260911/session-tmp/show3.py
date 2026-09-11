import json
base = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
for path in ["meta/caption-image-audit.json", "meta/subtitle-layout-audit.json", "meta/frame-semantic-audit.json"]:
    data = json.load(open(base + "/" + path, encoding="utf8"))
    print("=====", path, "keys:", list(data.keys())[:20])
    s = json.dumps(data, ensure_ascii=False, indent=1)
    print(s[:3800])

