import json
base = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
spr = json.load(open(base + "/meta/shot-progression-review.json", encoding="utf8"))
print("keys:", list(spr.keys()))
frames = spr.get("frames") or spr.get("items") or []
print("frames type:", type(frames).__name__, "len", len(frames))
def show(o, depth=0):
    if depth > 2: return
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, (dict, list)):
                show(v, depth+1)
            else:
                print("  " * depth + f"{k}: {str(v)[:200]}")
    elif isinstance(o, list):
        print("  " * depth + f"list len {len(o)}")
        for i, item in enumerate(o[:3]):
            if isinstance(item, dict):
                print("  " * depth + f"item {i} keys: {list(item.keys())}")
                show(item, depth+1)
            break
show(spr)

