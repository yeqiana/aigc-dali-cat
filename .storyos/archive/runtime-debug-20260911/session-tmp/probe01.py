import hashlib, os
from PIL import Image

base = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
paths = {
    "cover": base + r"/production/cover/cover.png",
    "publish01": base + r"/production/publish/01.png",
    "approved01": base + r"/media/approved/01.png",
    "mediapublish01": base + r"/media/publish/01.png",
}
for k, p in paths.items():
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
    im = Image.open(p)
    print(k, im.size, im.mode, h, os.path.getsize(p))

a = Image.open(paths["approved01"]).convert("RGB")
b = Image.open(paths["publish01"]).convert("RGB")
print("sizes", a.size, b.size)
if a.size == b.size:
    pa, pb = a.load(), b.load()
    diff_rows = []
    for y in range(0, a.size[1], 20):
        d = sum(1 for x in range(0, a.size[0], 40) if pa[x, y] != pb[x, y])
        if d:
            diff_rows.append((y, d))
    print("diff sample rows (y,count):", diff_rows[:60])
