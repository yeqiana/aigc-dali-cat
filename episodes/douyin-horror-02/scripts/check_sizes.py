import os, glob, sys
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')

img_dir = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\douyin-horror-02\images"
files = sorted(glob.glob(os.path.join(img_dir, "*.png")))

bad = []
for fp in files:
    fname = os.path.basename(fp)
    img = Image.open(fp)
    w, h = img.size
    ratio = w/h
    ok = abs(ratio - 9/16) < 0.05
    tag = "OK" if ok else "BAD"
    if not ok:
        bad.append(f"{fname}: {w}x{h} ratio={ratio:.2f}")
    print(f"[{tag}] {fname}: {w}x{h} ({ratio:.2f})")

print(f"\n=== Non-9:16 images: {len(bad)} ===")
for b in bad:
    print(f"  {b}")
