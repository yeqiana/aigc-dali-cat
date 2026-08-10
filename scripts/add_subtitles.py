# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
import os, sys
sys.stdout.reconfigure(encoding="utf-8")

INPUT_DIR = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\output\imagegen\batch-01-25-merged"
OUTPUT_DIR = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\output\imagegen\batch-01-25-subtitled"
FONT_PATH = r"C:\Windows\Fonts\simhei.ttf"

CAPTIONS = {
    "01": "什么情况…我是不是还没睡醒",
    "02": "好家伙，这边还有一个",
    "03": "我拉开窗帘看了一眼…家人们出大事了",
    "04": "根是真的扎进土里的，不是做梦",
    "05": "葵姐在跟着太阳转…它好安静",
    "06": "掉下来了，它在发光",
    "07": "热的…家人们它竟然是热的",
    "08": "射手哥好像需要这个，给你",
    "09": "卧槽它开炮了！！不是我按的！！",
    "10": "真的倒了…射手哥你是真的猛",
    "11": "我没看错，它还在那躺着",
    "12": "完蛋，它们发现我们了，越聚越多",
    "13": "葵姐又掉了几个，快快快",
    "14": "继续打继续打，不要停！",
    "15": "射手哥好像不行了…它好累",
    "16": "给你给你，吃了就好了，撑住",
    "17": "家人们，它们过来了，越来越近",
    "18": "就是现在，全部打出去！！",
    "19": "停了…？我们守住了吗…",
    "20": "等下，倒下那个旁边…那是种子？",
    "21": "我不敢下去拿，但它们就在那",
    "22": "捡回来了捡回来了，差点吓死",
    "23": "是真的种子，和阳光不一样，能种",
    "24": "埋进去了，剩下的等明天吧",
    "25": "我还不知道它会长成什么\n但第二天早上\n它已经发芽了",
}


import re

def wrap_text_smart(draw, text, font, max_width):
    """智能换行：优先在标点处断，避免单字孤儿行"""
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        # If whole paragraph fits, keep it
        bb = draw.textbbox((0, 0), paragraph, font=font)
        if bb[2] - bb[0] <= max_width:
            lines.append(paragraph)
            continue
        # Need to wrap: find break points (after punctuation or every N chars)
        chars = list(paragraph)
        current = ""
        for i, ch in enumerate(chars):
            test = current + ch
            bb = draw.textbbox((0, 0), test, font=font)
            if bb[2] - bb[0] <= max_width:
                current = test
            else:
                # Don't break if current is too short (< 3 chars)
                if len(current) < 3:
                    # Force this char in and break after
                    current = test
                    # Find last punctuation to break at
                    punct_pos = max(
                        current.rfind("，"), current.rfind("。"),
                        current.rfind("！"), current.rfind("？"),
                        current.rfind("…"), current.rfind(" "),
                        current.rfind("、")
                    )
                    if punct_pos >= 3:
                        lines.append(current[:punct_pos+1])
                        current = current[punct_pos+1:]
                    else:
                        lines.append(current)
                        current = ""
                else:
                    # Try to break at last punctuation
                    punct_pos = max(
                        current.rfind("，"), current.rfind("。"),
                        current.rfind("！"), current.rfind("？"),
                        current.rfind("…"), current.rfind(" "),
                        current.rfind("、")
                    )
                    if punct_pos >= 3:
                        lines.append(current[:punct_pos+1])
                        current = current[punct_pos+1:] + ch
                    else:
                        lines.append(current)
                        current = ch
        if current:
            # If last line is very short, merge with previous
            if len(current) <= 2 and len(lines) > 0:
                lines[-1] = lines[-1] + current
            else:
                lines.append(current)
    return lines

os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_SIZE = 64

for fname, text in CAPTIONS.items():
    img_path = os.path.join(INPUT_DIR, fname + ".png")
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    max_text_width = int(w * 0.82)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    lines = wrap_text_smart(draw, text, font, max_text_width)
    stroke_w = max(4, int(FONT_SIZE * 0.09))

    line_heights = []
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bb[3] - bb[1])

    spacing = int(FONT_SIZE * 0.4)
    total_h = sum(line_heights) + spacing * (len(lines) - 1)

    n_lines = len(lines)
    if n_lines <= 1:
        y_ratio = 0.78
    elif n_lines == 2:
        y_ratio = 0.72
    else:
        y_ratio = 0.66

    y0 = int(h * y_ratio) - total_h // 2

    for i, line in enumerate(lines):
        bb = draw.textbbox((0, 0), line, font=font)
        tw = bb[2] - bb[0]
        x = (w - tw) // 2
        y = y0 + sum(line_heights[:i]) + i * spacing
        draw.text(
            (x, y), line,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=stroke_w,
            stroke_fill=(0, 0, 0, 255),
        )

    result = Image.alpha_composite(img, overlay).convert("RGB")
    out_path = os.path.join(OUTPUT_DIR, fname + ".png")
    result.save(out_path, quality=95)
    line_preview = " / ".join(lines)
    print("  " + fname + ".png  [64px]  " + line_preview)

print("")
print("Done! " + str(len(CAPTIONS)) + " images -> " + OUTPUT_DIR)