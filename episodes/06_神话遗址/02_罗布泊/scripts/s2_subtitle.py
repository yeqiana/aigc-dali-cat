#!/usr/bin/env python3
"""S2《罗布泊·楼兰之门》字幕叠加与尺寸归一化。

输入：images/s2_keyframe/图NN_*.png（941x1672 v1 试产帧）
输出：images/s2_subtitle/（1080x1920 带字幕版）
"""

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "images" / "s2_keyframe"
OUT = ROOT / "images" / "s2_subtitle"
FONT = r"C:\Windows\Fonts\msyh.ttc"
TARGET = (1080, 1920)
PAD_X, PAD_Y = 28, 20
RADIUS = 20
LINE_H = 40

SUBS = {
    "01": ("沙暴还有三天。盐壳下面，露出了一扇不该存在的门。", 0.08, 0.05),
    "02": ("我叫林澈，第七科考队。师兄陈默说，楼兰不是灾变，是进去了。", 0.10, 0.05),
    "03": ("门框上的纹路在发光，一明一暗，像在呼吸。", 0.08, 0.05),
    "04": ("陈默对这里熟得不正常。他说，这条盐壳路他走过。", 0.42, 0.05),
    "05": ("师兄说，不能跨过门槛，也不能看门那边。", 0.52, 0.05),
    "06": ("门缝里的光，有节奏地亮暗，像有什么在等。", 0.08, 0.05),
    "07": ("我把墨脱石片上的纹路，对到门框上。一模一样。", 0.52, 0.05),
    "08": ("沙暴提前了。陈默却盯着门，说三年前它就找过他。", 0.40, 0.05),
    "09": ("门缝里不是黑暗。是一座亮着灯的城，有人在走动。", 0.08, 0.05),
    "10": ("陈默在人群里，认出了他失踪多年的父亲。", 0.40, 0.05),
    "11": ("他跨了过去。盐壳，开始从地面往门上爬。", 0.50, 0.05),
    "12": ("门内的光吞没了他。我把安全绳往腰上系。", 0.55, 0.05),
    "13": ("盐壳爬上了门框，门在一点一点地合拢。", 0.52, 0.05),
    "14": ("我拽住安全绳。门缝里，有人伸出手，挡住了门。", 0.10, 0.05),
    "15": ("盐壳爬上了我的袖口。我不能松手。", 0.12, 0.05),
    "16": ("我把他拖出来了。门缝里的手，收了回去。", 0.12, 0.05),
    "17": ("回驻地他才承认：三年前，门就找过他。", 0.10, 0.05),
    "18": ("门址封存。陈默说，别再来了。", 0.08, 0.05),
    "19": ("他的手臂上结着一层盐壳，洗不掉。", 0.10, 0.05),
    "20": ("相机里多了一张照片：城墙上，根本没有门。", 0.08, 0.05),
}


def wrap(text, font, max_width):
    lines, current = [], ""
    for char in text:
        candidate = current + char
        if current and font.getlength(candidate) > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT, 28)
    done = 0
    for key in sorted(SUBS, key=int):
        matches = sorted(SRC.glob(f"图{int(key):02d}_*.png"))
        if not matches:
            print("MISS", key)
            continue
        # 同一帧多版本时优先取最高版本（_vN），旧版保留为历史。
        source = max(matches, key=lambda p: int(re.search(r"_v(\d+)", p.stem).group(1)))
        image = Image.open(source).convert("RGB").resize(TARGET, Image.Resampling.BICUBIC)
        text, y_fraction, x_fraction = SUBS[key]
        drawer = ImageDraw.Draw(image, "RGBA")
        max_width = int(image.width * 0.55)
        lines = wrap(text, font, max_width - 2 * PAD_X)
        bubble_height = PAD_Y * 2 + LINE_H * len(lines)
        bubble_width = int(max(font.getlength(line) for line in lines)) + 2 * PAD_X
        x0 = min(int(image.width * x_fraction), image.width - bubble_width - 20)
        y0 = int(image.height * y_fraction)
        drawer.rounded_rectangle(
            [x0, y0, x0 + bubble_width, y0 + bubble_height],
            radius=RADIUS,
            fill=(0, 0, 0, 150),
        )
        for index, line in enumerate(lines):
            text_y = y0 + PAD_Y + index * LINE_H
            drawer.text((x0 + PAD_X + 1, text_y + 1), line, font=font, fill=(0, 0, 0, 255))
            drawer.text((x0 + PAD_X, text_y), line, font=font, fill=(255, 255, 255, 255))

        output = OUT / f"S2_图{int(key):02d}_带字幕.png"
        image.save(output, "PNG")
        done += 1
    print(f"subtitle done: {done}/{len(SUBS)} -> {OUT}")


if __name__ == "__main__":
    main()
