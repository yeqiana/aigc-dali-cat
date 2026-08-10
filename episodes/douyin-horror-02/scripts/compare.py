import os
from PIL import Image

old_dir = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\douyin-horror-02\images"
new_dir = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\douyin-horror-02\images_916"

# Compare key images: 07 (12 bowls), 10 (grandfather on TV), 15 (she sits), 12 (dark grid)
keys = ["图07.png", "图10.png", "图15.png", "图12.png"]
for k in keys:
    old_fp = os.path.join(old_dir, k)
    new_fp = os.path.join(new_dir, k)
    old_exists = os.path.exists(old_fp)
    new_exists = os.path.exists(new_fp)
    if old_exists:
        img = Image.open(old_fp)
        print(f"OLD {k}: {img.size[0]}x{img.size[1]}")
    if new_exists:
        img = Image.open(new_fp)
        print(f"NEW {k}: {img.size[0]}x{img.size[1]}")
    print(f"  OLD exists: {old_exists}, NEW exists: {new_exists}")
    print()
