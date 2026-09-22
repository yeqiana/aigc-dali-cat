import json
base = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
for path, sel in [("docs/04_婚礼前夜_视觉规范_V2.0.md", None), ("docs/07_揭露顺序与提示词修订说明_V2.md", None)]:
    print("=====", path)
    s = open(base + "/" + path, encoding="utf8").read()
    print(s[:4200])

