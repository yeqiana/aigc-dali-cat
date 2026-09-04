import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ep = Path(sys.argv[1])
out_dir = ep / "production" / "contact-sheets"
out_dir.mkdir(parents=True, exist_ok=True)
body = sorted((ep / "production" / "publish").glob("[0-9][0-9].png"))
cols, rows = 4, 5
tw, th = 300, 375
pad = 10
canvas = Image.new("RGB", (cols * tw + (cols + 1) * pad, rows * th + (rows + 1) * pad + 40), (18, 18, 20))
draw = ImageDraw.Draw(canvas)
font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 26)
for i, p in enumerate(body):
    img = Image.open(p).convert("RGB")
    img.thumbnail((tw, th), Image.LANCZOS)
    x = pad + (i % cols) * (tw + pad)
    y = pad + (i // cols) * (th + pad)
    canvas.paste(img, (x + (tw - img.width) // 2, y + (th - img.height) // 2))
    draw.text((x + 6, y + th + 4), f"{i + 1:02d}", font=font, fill=(255, 255, 255))
out = out_dir / "publish-final.jpg"
canvas.save(out, quality=82)
print(out)
