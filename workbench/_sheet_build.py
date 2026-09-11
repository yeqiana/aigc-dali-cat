
# -*- coding: utf-8 -*-
"""Rebuild the manifest-declared publish contact sheet from current release assets."""
import hashlib, pathlib
from PIL import Image, ImageDraw, ImageFont

root = pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')
ep = root / r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
cover = ep / 'production/cover/cover.png'
body = sorted((ep / 'production/publish').glob('[0-9][0-9].png'))
assert len(body) == 20, len(body)
items = [('COVER', cover)] + [(p.stem, p) for p in body]

cols, thumb_w, label_h, gap = 4, 258, 26, 12
ratio = 1350 / 1080
thumb_h = int(round(thumb_w * ratio))
rows = (len(items) + cols - 1) // cols
sheet = Image.new('RGB', (gap + cols * (thumb_w + gap), gap + rows * (thumb_h + label_h + gap)), 'white')
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 18)
except Exception:
    font = ImageFont.load_default()
for idx, (label, path) in enumerate(items):
    r, c = divmod(idx, cols)
    x = gap + c * (thumb_w + gap)
    y = gap + r * (thumb_h + label_h + gap)
    with Image.open(path) as img:
        t = img.convert('RGB')
        t.thumbnail((thumb_w, thumb_h))
    sheet.paste(t, (x + (thumb_w - t.width) // 2, y))
    draw.text((x + 4, y + thumb_h + 4), label, fill='black', font=font)
out = ep / 'production/contact-sheets/publish-final.jpg'
sheet.save(out, format='JPEG', quality=90)
print('sheet', sheet.size, out, hashlib.sha256(out.read_bytes()).hexdigest()[:16])

