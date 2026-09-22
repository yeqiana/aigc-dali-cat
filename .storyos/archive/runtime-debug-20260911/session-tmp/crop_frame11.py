# -*- coding: utf-8 -*-
from PIL import Image
from pathlib import Path

src = Path(r'C:/Users/79873/.codex/generated_images/01a0819b-ee28-7212-9979-45a281e1bdf6/exec-a22a9bdf-45ea-4b5e-b4a6-e2521c4d0021.png')
dst = Path('episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉/media/raw/manual/11.png')

im = Image.open(src)
w, h = im.size
# 目标比例 4:5 = 0.8。保持宽度不变，裁剪高度使 ratio 接近 0.8
target_h = int(round(w / 0.8))
if target_h > h:
    target_w = int(round(h * 0.8))
    left = (w - target_w) // 2
    right = left + target_w
    im = im.crop((left, 0, right, h))
else:
    top = (h - target_h) // 2
    bottom = top + target_h
    im = im.crop((0, top, w, bottom))

dst.parent.mkdir(parents=True, exist_ok=True)
im.save(dst, format='PNG')
print('crop result size:', im.size, 'ratio:', round(im.size[0]/im.size[1], 4))
