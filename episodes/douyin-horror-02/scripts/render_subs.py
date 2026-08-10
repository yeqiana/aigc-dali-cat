# -*- coding: utf-8 -*-
import os, json
from PIL import Image, ImageDraw, ImageFont

V3_DIR = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\douyin-horror-02\v3_final"
OUT_DIR = os.path.join(V3_DIR, "subtitled")
JSON_PATH = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\douyin-horror-02\scripts\sub_data.json"
os.makedirs(OUT_DIR, exist_ok=True)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    DATA = json.load(f)

FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"
FONT_SIZE = 28
PX, PY = 28, 20
ALPHA = 150
R = 20
W_RATIO = 0.75

font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

for fname in sorted(os.listdir(V3_DIR)):
    if not fname.endswith(".png"):
        continue
    key = fname.replace(".png", "")
    if key not in DATA:
        continue
    subtitle, pos_ratio = DATA[key]
    img = Image.open(os.path.join(V3_DIR, fname)).convert("RGBA")
    W, H = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    max_w = int(W * W_RATIO) - PX * 2
    lines = []
    cur = ""
    for ch in subtitle:
        test = cur + ch
        bb = draw.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] > max_w:
            lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    lh = FONT_SIZE + 6
    th = lh * len(lines)
    bw = int(W * W_RATIO)
    bh = th + PY * 2
    bx = (W - bw) // 2
    by = int(H * pos_ratio)
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=R, fill=(0, 0, 0, ALPHA))
    ty = by + PY
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        tw = bb[2] - bb[0]
        tx = bx + (bw - tw) // 2
        draw.text((tx, ty), line, font=font, fill=(255, 255, 255, 255))
        ty += lh
    result = Image.alpha_composite(img, overlay).convert("RGB")
    result.save(os.path.join(OUT_DIR, fname), "PNG", quality=95)
    print("OK " + key + " pos=" + str(pos_ratio))
print("ALL DONE")