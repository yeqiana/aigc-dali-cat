import os, glob, sys
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')

img_dir = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\douyin-horror-02\images_916"
files = sorted(glob.glob(os.path.join(img_dir, "*.png")))

ok = 0
bad = 0
for fp in files:
    fname = os.path.basename(fp)
    img = Image.open(fp)
    w, h = img.size
    ratio = w/h
    is_916 = abs(ratio - 9/16) < 0.03
    if is_916:
        ok += 1
    else:
        bad += 1
        print(f"BAD {fname}: {w}x{h} ratio={ratio:.2f}")

print(f"\nOK: {ok}, BAD: {bad}, TOTAL: {ok+bad}")
