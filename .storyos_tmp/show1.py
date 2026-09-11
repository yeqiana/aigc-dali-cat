import json
base = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
def show(path):
    data = json.load(open(base + "/" + path, encoding="utf8"))
    s = json.dumps(data, ensure_ascii=False, indent=1)
    print("=====", path, "len", len(s))
    print(s[:5200])
show("meta/character-visual-contract.json")

