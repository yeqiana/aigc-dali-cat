
# -*- coding: utf-8 -*-
"""Rebuild the ep05 release cover from the new frame-01 asset + doc06 cover copy.

Cover copy (docs/06_婚礼前夜_最终发布文案_V2.0.md 封面文案):
  line1 2007年
  line2 婚礼前夜，我发现婚鞋底下
  line3 焊着铁环   (largest, per doc typography rule)
Style stays inside the release's own subtitle system: Microsoft YaHei Bold,
white fill with black stroke.
"""
import hashlib, shutil, pathlib
from PIL import Image, ImageDraw, ImageFont

root = pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')
ep = root / r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
base = ep / 'media/approved/01.png'
cover = ep / 'production/cover/cover.png'
font_path = pathlib.Path('C:/Windows/Fonts/msyhbd.ttc')
assert font_path.is_file(), font_path

lines = [('2007年', 56), ('婚礼前夜，我发现婚鞋底下', 64), ('焊着铁环', 104)]
margin_x, bottom_y, gap = 72, 1258, 22

im = Image.open(base).convert('RGB')
draw = ImageDraw.Draw(im)
fonts = [ImageFont.truetype(str(font_path), size) for _, size in lines]
heights = []
for (text, _), font in zip(lines, fonts):
    box = draw.textbbox((0, 0), text, font=font, stroke_width=6)
    heights.append(box[3] - box[1])
total = sum(heights) + gap * (len(lines) - 1)
y = bottom_y - total
for (text, _), font, h in zip(lines, fonts, heights):
    draw.text((margin_x, y), text, font=font, fill=(255, 255, 255, 255),
              stroke_width=6, stroke_fill=(0, 0, 0, 255))
    y += h + gap

if cover.is_file():
    archive = ep / 'meta/archive'
    archive.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cover, archive / 'cover-pre-f01-face-refresh.png')
im.save(cover, format='PNG')
print('cover written', cover, im.size, hashlib.sha256(cover.read_bytes()).hexdigest())

