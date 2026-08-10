import os, glob, sys
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')

v1 = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\02_折多山守夜人\v1_34ratio"
files = sorted(glob.glob(os.path.join(v1, "*.png")))

print("=== 比例检查 ===\n")
bad = []
ok = []
for fp in files:
    fname = os.path.basename(fp)
    img = Image.open(fp)
    w, h = img.size
    ratio = w/h
    is_916 = abs(ratio - 9/16) < 0.03
    is_34 = abs(ratio - 3/4) < 0.03
    tag = "3:4" if is_34 else ("9:16" if is_916 else f"OTHER {ratio:.2f}")
    if is_916: ok.append(fname)
    else: bad.append(f"{fname}: {w}x{h} ({tag})")

print("--- 9:16 ---")
for f in ok: print(f"  {f}")
print(f"\n--- 非9:16 ({len(bad)}张) ---")
for b in bad: print(f"  {b}")
print(f"\n总计: {len(files)}张 | 9:16={len(ok)} | 非9:16={len(bad)}")
