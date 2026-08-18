#!/usr/bin/env python3
"""K2 冰川字幕叠加：左中位放置，宽度<=55%W，避开主体。"""

import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "images" / "k2_keyframe"
OUT = ROOT / "images" / "k2_subtitle"
FONT = r"C:\Windows\Fonts\msyh.ttc"

SUBS = {
    "01": ("我随导师来冰川撤站。探照灯扫过冰壁，深处站着一排穿我们队服的人。", 0.42, 0.05),
    "02": ("冰里那个人的队服和我们一模一样，连口袋上的拉链都相同。", 0.40, 0.05),
    "03": ("我们要在天黑前拆完最后一批设备。导师说，别往冰壁深处看。", 0.50, 0.05),
    "04": ("导师拿灯一照，冰里那个人的工牌和我脖子上挂的一样。他按住胸口，左口袋是破的。", 0.45, 0.05),
    "05": ("张远掏出他爸的工牌照片对着冰壁——导师一把按住他，说别让他们看到。", 0.48, 0.05),
    "06": ("导师用冰镐敲冰壁，平板显示：冰层里多出七个人形。", 0.45, 0.05),
    "07": ("导师说，从你看见冰里那个人的那一刻起，融水不能碰你自己的皮肤。", 0.48, 0.05),
    "08": ("张远对着冰壁说了一声爸。融水，从冰层里流出来了。", 0.42, 0.05),
    "09": ("导师抓住张远时，融水沿他的手指爬上了袖口。", 0.45, 0.05),
    "10": ("导师推开我，自己站在了冰壁和张远之间。融水已经爬到他手腕。", 0.40, 0.05),
    "11": ("冰里，一年前失踪的队伍全睁开了眼。七个人，都看着他。", 0.35, 0.05),
    "12": ("冰里那个队长，朝张远伸出了手。", 0.38, 0.05),
    "13": ("导师转过脸时，半边脸已经冰化了。他还在说快走。", 0.30, 0.05),
    "14": ("我把安全绳套在导师腰上。冰里，他们还在往前挪。", 0.45, 0.05),
    "15": ("我们把他拖出冰壁时，暴风雪起了。冰里，他们没跟出来。", 0.42, 0.05),
    "16": ("导师的手还在冰里，可他一直握着冰镐没松。", 0.42, 0.05),
    "17": ("导师承认了——当年是他让队长独自进的冰隙。这工牌，他一直留着。", 0.48, 0.05),
    "18": ("设备拆完了。暴风雪封了路，冰川不会再让人进来。", 0.42, 0.05),
    "19": ("回去的路上，导师脸上的冰，开始化了。", 0.40, 0.05),
    "20": ("三天后，我在下游的浮冰里看见了一个人。是三十岁的导师。", 0.42, 0.05),
}

PAD_X, PAD_Y = 28, 20
RADIUS = 20
LINE_H = 40


def wrap(text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        t = cur + ch
        if font.getlength(t) > max_w and cur:
            if ch in "\u3002\uff01\uff1f\uff1b" and len(cur) >= 1:
                cur = t; continue
            lines.append(cur); cur = ch
        else:
            cur = t
    if cur: lines.append(cur)
    return lines


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT, 28)
    pat = re.compile(r"^K2_\u56fe(\d+)_")
    by_num = {m.group(1): f for f in SRC.glob("*_final.jpg") if (m := pat.match(f.name))}
    ok = 0
    for key in sorted(SUBS.keys(), key=int):
        src = by_num.get(key)
        if not src:
            print("MISS", key); continue
        im = Image.open(src).convert("RGB")
        w, h = im.size
        text, y_frac, x_frac = SUBS[key]
        dr = ImageDraw.Draw(im, "RGBA")
        max_w = int(w * 0.55)
        lines = wrap(text, font, max_w - 2 * PAD_X)
        bubble_h = PAD_Y * 2 + LINE_H * len(lines)
        bubble_w = int(max(font.getlength(l) for l in lines)) + 2 * PAD_X
        y0 = int(h * y_frac)
        x0 = min(int(w * x_frac), max(0, w - bubble_w - 20))
        dr.rounded_rectangle([x0, y0, x0 + bubble_w, y0 + bubble_h], radius=RADIUS, fill=(0, 0, 0, 150))
        for i, line in enumerate(lines):
            ty = y0 + PAD_Y + i * LINE_H
            dr.text((x0 + PAD_X + 1, ty + 1), line, font=font, fill=(0, 0, 0, 255))
            dr.text((x0 + PAD_X, ty), line, font=font, fill=(255, 255, 255, 255))
        out_f = OUT / (src.stem + ".png")
        im.save(out_f, "PNG")
        ok += 1
    print("subtitle done:", ok, "/ 20 ->", OUT)


if __name__ == "__main__":
    main()
