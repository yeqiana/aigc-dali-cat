#!/usr/bin/env python3
"""泥人续《送件》字幕叠加与尺寸归一化。

输入：images/keyframe/图NN_*.png（941x1672 v1 试产帧）
输出：images/subtitle/（1080x1920 带字幕版）
"""

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "images" / "keyframe"
OUT = ROOT / "images" / "subtitle"
FONT = r"C:\Windows\Fonts\msyh.ttc"
TARGET = (1080, 1920)
PAD_X, PAD_Y = 28, 20
RADIUS = 20
LINE_H = 40

SUBS = {
    "01": ("泥人跟回家后，我没敢动它。今天，铁盒里多了一件不是我的东西。", 0.08, 0.05),
    "02": ("是一张旧镇的老照片。背面写着一个名字，不是我家的。", 0.42, 0.05),
    "03": ("阿岚也在找旧镇的人。我把照片装进包里，去找她。", 0.45, 0.05),
    "04": ("阿岚说，她也收到了。一串旧钥匙，和一个收件地址。", 0.10, 0.05),
    "05": ("阿岚说，这东西不能拒收。退了，那个泥人就一直站在你门口。", 0.55, 0.05),
    "06": ("每一件，都配一个收件地址。和一张死人的名字。", 0.52, 0.05),
    "07": ("第三件，是旧报纸包的小盒子。那报纸上的字，是我爸的。", 0.45, 0.05),
    "08": ("我决定替他送。这些，都是爸没送出去的东西。", 0.55, 0.05),
    "09": ("我出门送第一件。回头，那个泥人，跟到了巷口。", 0.08, 0.05),
    "10": ("第一件，是一户人家的旧照片。门里的手，抖了一下。", 0.50, 0.05),
    "11": ("每送出去一件，它就在我门口，站得更近一步。", 0.10, 0.05),
    "12": ("第二天，铁盒满了。这些东西，都是要送的。", 0.52, 0.05),
    "13": ("阿岚的门口，也有一个泥人。她家的，昨晚到了她床边。", 0.10, 0.05),
    "14": ("最后一件，地址写的是：林澈家。收件人，是我。", 0.45, 0.05),
    "15": ("我回到家，它已经站在门里了。铁盒，是空的。", 0.55, 0.05),
    "16": ("我拆开给自己的包裹。是爸的照片，背面写着，给女儿。", 0.45, 0.05),
    "17": ("阿岚把最后一件，送给了她自己。她说，她等的，就是这句。", 0.50, 0.05),
    "18": ("我一直没敢说。那年，是我拦着爸，不让他回旧镇的。", 0.45, 0.05),
    "19": ("第二天，泥人碎了。只剩一滩泥，和那个空铁盒。", 0.50, 0.05),
    "20": ("铁盒空了，盒底只剩一小撮湿泥。和旧镇门口，是同一种泥。", 0.52, 0.05),
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

        output = OUT / f"NX_图{int(key):02d}_带字幕.png"
        image.save(output, "PNG")
        done += 1
    print(f"subtitle done: {done}/{len(SUBS)} -> {OUT}")


if __name__ == "__main__":
    main()
