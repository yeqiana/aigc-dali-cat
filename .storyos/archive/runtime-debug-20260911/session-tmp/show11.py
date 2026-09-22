import json
base = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
spr = json.load(open(base + "/meta/shot-progression-review.json", encoding="utf8"))
frames = spr["frames"]
print("=== frame 01 full ===")
print(json.dumps(frames[0], ensure_ascii=False, indent=1))
print("=== frame 02 ===")
print(json.dumps(frames[1], ensure_ascii=False, indent=1))
print("=== emotion values used across frames ===")
print(sorted({str(f.get("emotion")) for f in frames}))

