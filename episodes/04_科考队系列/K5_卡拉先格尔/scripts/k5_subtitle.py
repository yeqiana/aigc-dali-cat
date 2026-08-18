#!/usr/bin/env python3
"""K5 卡拉先格尔字幕叠加与尺寸统一。

说明：K5 已发布，源图已清理；最终图保留在 images/k5_publish/。
统一输出尺寸：1080x1920，保持原始竖图比例，不裁切。
"""

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "images" / "k5_keyframe"
OUT = ROOT / "images" / "k5_subtitle"
FONT = r"C:\Windows\Fonts\msyh.ttc"
TARGET = (1080, 1920)

# (字幕, y比例, x比例)。位置按主体避让，气泡宽度最多55%画面宽。
SUBS = {
    "01": ("我们来测一条老地震裂缝，可裂缝底下竟然还有一片向远处延伸的地面。", 0.08, 0.04),
    "02": ("撤站前，我们必须把这条旧断裂带测完，原始点一个都不能删。", 0.72, 0.04),
    "03": ("手电照到的不是坑底，而是一片能向远处延伸的地面。", 0.10, 0.04),
    "04": ("绳子放了三十多米，没落到底，绳端被下面那片地面横着接住了。", 0.08, 0.04),
    "05": ("程野说，上次也出现过这种横向承托；他把数据删了，项目才过。", 0.08, 0.04),
    "06": ("两年前封存的岩芯里，也有同样的灰白土面和根系。", 0.76, 0.04),
    "07": ("程野说，碰过它的东西，现实里都会多出一个接触面。别再扔了。", 0.08, 0.04),
    "08": ("我扔下的石头没落下去，反而从两百米外另一条裂缝里滚了出来。", 0.76, 0.04),
    "09": ("最后一个测点差半米。我知道红钉会让它回应，还是打了进去。", 0.74, 0.04),
    "10": ("钉子下面开了一个小孔，孔里看见的，是我们头顶的天。", 0.76, 0.04),
    "11": ("红钉之后，细裂纹从那片地下地面一路向营地伸过来。", 0.08, 0.04),
    "12": ("岩芯盒一直没打开，里面却多出了一截同样的水平土面。", 0.76, 0.04),
    "13": ("帐篷脚碰过的地方，也长出了同样的土面。", 0.72, 0.04),
    "14": ("车还没发动，车底已经被一层水平土面托住了。", 0.08, 0.04),
    "15": ("两边裂缝同时接上了同一片地下地面，它还在往营地延伸。", 0.76, 0.04),
    "16": ("测量杆没有倒，是被那片地下地面从侧面托住了。", 0.70, 0.04),
    "17": ("我们拔钉停手，程野把删掉的回波放回原始数据。", 0.74, 0.04),
    "18": ("我们不用再碰裂缝，改用原来的测线把任务闭合。", 0.76, 0.04),
    "19": ("岩芯封好了，原始数据也带走了。卡拉先格尔看起来又只剩一条普通裂缝。", 0.08, 0.04),
    "20": ("封条没开，可岩芯里的车辙正朝着断面外面走。", 0.76, 0.04),
}

PAD_X, PAD_Y = 28, 20
RADIUS = 20
LINE_H = 40
MAX_W = int(TARGET[0] * 0.55)


def wrap(text, font, max_w):
    lines, current = [], ""
    for ch in text:
        candidate = current + ch
        if current and font.getlength(candidate) > max_w:
            # 标点不能单独落在下一行；允许标点附着在上一行，
            # 避免出现“测试\n，现实里……”这类孤立标点。
            if ch in "。！？；，、：）》】』”’" and current:
                current += ch
                continue
            else:
                lines.append(current)
                current = ch
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def resize_to_target(im):
    # 竖图比例接近 9:16，统一到制作规范的 1080x1920；不裁切、不加边。
    return im.convert("RGB").resize(TARGET, Image.Resampling.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT, 28)
    inputs = sorted(SRC.glob("*.png"))
    if len(inputs) != 20:
        raise SystemExit(f"expected 20 keyframes, found {len(inputs)}")

    for index, src in enumerate(inputs, start=1):
        key = f"{index:02d}"
        im = resize_to_target(Image.open(src))
        text, y_frac, x_frac = SUBS[key]
        draw = ImageDraw.Draw(im, "RGBA")
        lines = wrap(text, font, MAX_W - 2 * PAD_X)
        bubble_w = int(max(font.getlength(line) for line in lines)) + 2 * PAD_X
        bubble_h = PAD_Y * 2 + LINE_H * len(lines)
        x0 = min(int(TARGET[0] * x_frac), TARGET[0] - bubble_w - 20)
        y0 = min(int(TARGET[1] * y_frac), TARGET[1] - bubble_h - 20)
        draw.rounded_rectangle(
            [x0, y0, x0 + bubble_w, y0 + bubble_h],
            radius=RADIUS,
            fill=(0, 0, 0, 150),
        )
        for line_no, line in enumerate(lines):
            tx = x0 + PAD_X
            ty = y0 + PAD_Y + line_no * LINE_H
            draw.text((tx + 1, ty + 1), line, font=font, fill=(0, 0, 0, 255))
            draw.text((tx, ty), line, font=font, fill=(255, 255, 255, 255))
        im.save(OUT / f"K5_图{key}_{src.stem}.png", "PNG")
    print(f"subtitle done: {len(inputs)}/20 -> {OUT}")


if __name__ == "__main__":
    main()
