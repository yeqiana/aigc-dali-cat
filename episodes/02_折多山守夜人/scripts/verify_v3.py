import os, glob, sys
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
v3 = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\02_折多山守夜人\v3_final"
files = sorted(glob.glob(os.path.join(v3, "*.png")))
ok = 0
bad = 0
for fp in files:
    fname = os.path.basename(fp)
    img = Image.open(fp)
    w, h = img.size
    ratio = w/h
    if abs(ratio - 9/16) < 0.05:
        ok += 1
    else:
        bad += 1
        print(f"BAD {fname}: {w}x{h} ({ratio:.2f})")
print(f"OK: {ok} BAD: {bad} TOTAL: {ok+bad}")
