#!/usr/bin/env python3
"""K4 溶洞字幕叠加：左中位放置，宽度<=55%W，避开主体。"""

import os
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "images" / "k4_keyframe"
OUT = ROOT / "images" / "k4_subtitle"
FONT = r"C:\Windows\Fonts\msyh.ttc"

SUBS = {
    "01": ("我陪哥哥来补父亲没画完的测线。一抬头，洞顶有一串湿泥脚印。", 0.55, 0.06),
    "02": ("洞顶的脚印，和我们鞋底一模一样。连磨损的地方都相同。", 0.12, 0.05),
    "03": ("父亲三年前没画完这条测线。哥哥说，这次一定要画到尽头。", 0.62, 0.06),
    "04": ("我们往前走，头顶的脚印也往前移，始终悬在每个人正上方。", 0.60, 0.28),
    "05": ("哥哥说，别站在自己头顶那枚脚印的正下方。", 0.72, 0.06),
    "06": ("测线最后一段，在竖井最深处。父亲当年，就是进去后没再出来。", 0.13, 0.05),
    "07": ("哥哥一直留着父亲最后一枚标记。他说，要把它放回测线尽头。", 0.16, 0.05),
    "08": ("哥哥伸手去够竖井壁上的标记。他头顶的脚印，开始渗水。", 0.70, 0.06),
    "09": ("他的脚离开地面，整个人被拉向了洞顶。", 0.72, 0.05),
    "10": ("我把安全绳套在他腰上，另一头固定在洞壁上。", 0.13, 0.05),
    "11": ("整片洞顶，全是脚印。它们全都指向竖井深处。", 0.70, 0.25),
    "12": ("竖井深处，好像有人叫了哥哥一声。是父亲的声音。", 0.14, 0.35),
    "13": ("哥哥松开了手，把父亲的标记，扔进了竖井。", 0.35, 0.45),
    "14": ("标记落下去后，那股往上拉的力量，突然停了。", 0.14, 0.05),
    "15": ("测线补完了。父亲的线，到这儿为止。", 0.12, 0.40),
    "16": ("哥哥说，他一直觉得，是当年自己劝父亲进去的。", 0.35, 0.45),
    "17": ("三天后，我回到城里。鞋底还沾着洞里的湿泥。", 0.14, 0.06),
    "18": ("夜里，我听见了洞里的滴水声。", 0.14, 0.30),
    "19": ("天花板上，多了一串湿泥脚印。和洞里的，一模一样。", 0.70, 0.06),
    "20": ("那串脚印，正在从天花板上，一步一印地朝我走下来。", 0.40, 0.40),
}

PAD_X, PAD_Y = 28, 20
RADIUS = 20
MAX_BUBBLE_W_RATIO = 0.55
LINE_H = 40


def wrap(text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        t = cur + ch
        if font.getlength(t) > max_w and cur:
            if ch in "\u3002\uff01\uff1f\uff1b" and len(cur) >= 1:
                cur = t
                continue
            lines.append(cur)
            cur = ch
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT, 28)
    pat = re.compile(r"^K4_\u56fe(\d+)_")
    by_num = {}
    for name in os.listdir(SRC):
        m = pat.match(name)
        if m and name.endswith("_final.jpg"):
            by_num[m.group(1)] = SRC / name

    ok = 0
    for key, val in sorted(SUBS.items()):
        src_path = by_num.get(key)
        if not src_path:
            print("MISS", key)
            continue
        im = Image.open(src_path).convert("RGB")
        w, h = im.size
        out_name = src_path.stem + ".png"
        if val is None:
            im.save(OUT / out_name, "PNG")
            ok += 1
            continue
        text, y_frac, x_frac = val
        dr = ImageDraw.Draw(im, "RGBA")
        max_w = int(w * MAX_BUBBLE_W_RATIO)
        lines = wrap(text, font, max_w - 2 * PAD_X)
        bubble_h = PAD_Y * 2 + LINE_H * len(lines)
        bubble_w = int(max(font.getlength(l) for l in lines)) + 2 * PAD_X
        y0 = int(h * y_frac)
        x0 = min(int(w * x_frac), max(0, w - bubble_w - 20))
        dr.rounded_rectangle(
            [x0, y0, x0 + bubble_w, y0 + bubble_h],
            radius=RADIUS,
            fill=(0, 0, 0, 150),
        )
        for i, line in enumerate(lines):
            ty = y0 + PAD_Y + i * LINE_H
            dr.text((x0 + PAD_X + 1, ty + 1), line, font=font, fill=(0, 0, 0, 255))
            dr.text((x0 + PAD_X, ty), line, font=font, fill=(255, 255, 255, 255))
        im.save(OUT / out_name, "PNG")
        ok += 1
    print("subtitle done:", ok, "/", len(SUBS), "->", OUT)


if __name__ == "__main__":
    main()
