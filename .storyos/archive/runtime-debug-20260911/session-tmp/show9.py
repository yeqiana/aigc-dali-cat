import json
base = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
for p in ["meta/incremental-frame-audit.json", "meta/frame-semantic-review.json", "meta/frame-reviews/01.json", "meta/frame-reviews/11.json", "meta/production-approval.json"]:
    try:
        d = json.load(open(base + "/" + p, encoding="utf8"))
        s = json.dumps(d, ensure_ascii=False, indent=1)
        print("=====", p, "len", len(s))
        print(s[:2600])
    except Exception as e:
        print("ERR", p, e)

