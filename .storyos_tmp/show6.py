import json
base = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
sg = json.load(open(base + "/meta/story-gates.json", encoding="utf8"))
print("story-gates top keys:", list(sg.keys()))
def walk(o, path="", depth=0):
    if depth > 3: return
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)):
                print("  " * depth + f"[{k}]")
                walk(v, path + "/" + str(k), depth + 1)
            else:
                s = str(v)
                print("  " * depth + f"{k}: {s[:160]}")
    elif isinstance(o, list):
        print("  " * depth + f"<list len {len(o)}>")
        if o and isinstance(o[0], dict):
            print("  " * depth + "first item keys:", list(o[0].keys()))
            walk(o[0], path, depth + 1)
walk(sg)

