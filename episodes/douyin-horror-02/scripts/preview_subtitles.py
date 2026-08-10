import os, glob
from PIL import Image, ImageDraw, ImageFont

img_dir = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\douyin-horror-02\images"
out_dir = os.path.join(img_dir, "preview")
os.makedirs(out_dir, exist_ok=True)
font_path = r"C:\Windows\Fonts\msyh.ttc"

targets = {
    "01": "我叫林晚，今年22岁。\n我爷爷1987年在折多山修路，失踪了。\n三十年后，我找到了那条路。",
    "07": "桌上摆着十二副碗筷。米饭在冒热气。\n小周摸了摸碗——是烫的。\n好像十二个人刚刚放下筷子，随时会回来。",
    "10d": "然后我注意到他背后。\n走廊里站着一个人。太高了。\n它的眼睛是两点黄色的光。\n它转过头了。它在看镜头。",
}

font = ImageFont.truetype(font_path, 28)

for prefix, text in targets.items():
    pattern = os.path.join(img_dir, f"*{prefix}*.png")
    matches = glob.glob(pattern)
    if not matches:
        print(f"NOT FOUND: {prefix}")
        continue
    fp = matches[0]
    fname = os.path.basename(fp)
    img = Image.open(fp).convert("RGBA")
    w, h = img.size
    print(f"{fname}: {w}x{h}")
    
    lines = text.split("\n")
    line_h = 38
    pad = 14
    bar_h = line_h * len(lines) + pad * 2
    top_bar = Image.new("RGBA", (w, bar_h), (0, 0, 0, 170))
    img.paste(top_bar, (0, 0), top_bar)
    
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        y = pad + i * line_h
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
    
    img = img.convert("RGB")
    out_fp = os.path.join(out_dir, fname.replace(".png", "_sub.png"))
    img.save(out_fp, "PNG")
    print(f"OK: {out_fp}")

print("Done!")
