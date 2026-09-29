#!/usr/bin/env python3
"""《画工画僵尸》：20 张图片尺寸归一化与字幕合成。

输入：images/formal_storyboard/ 下 20 张 941x1672 正式关键帧
输出：images/subtitle/ 下 20 张 1080x1920 带字幕图片

字幕文案与 docs/05_画工画僵尸_20张正式分镜_V1.0.md 逐图一致；
空字幕帧（03/06/10/13/16）仅归一化，不绘制气泡；不覆盖正式分镜原图。
"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "images" / "formal_storyboard"
OUTPUT_DIR = ROOT / "images" / "subtitle"
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"
TARGET_SIZE = (1080, 1920)
FONT_SIZE = 31
PAD_X, PAD_Y = 28, 20
LINE_HEIGHT = 44
RADIUS = 20
MAX_BUBBLE_WIDTH = 0.55
CAPTION_GAP = 44
CAPTION_SHIFT_X = FONT_SIZE * 2


# 与 docs/05 字幕草案一致；y 为气泡顶部比例，默认左侧中部暗区，由视觉门禁逐图复核。
SUBTITLES: dict[int, tuple[str | None, float]] = {
    1: ("这活，先把钱拿到再说", 0.30),
    2: ("画完才能拿钱", 0.34),
    3: (None, 0.0),
    4: ("楼下怎么还不来人", 0.36),
    5: ("抬笔，他就停了", 0.36),
    6: (None, 0.0),
    7: ("不是抽，是在学我", 0.30),
    8: ("现在逃，还来得及吗", 0.34),
    9: ("我再画最后一笔", 0.36),
    10: (None, 0.0),
    11: ("别碰我的画", 0.30),
    12: ("他已经到床边了", 0.36),
    13: (None, 0.0),
    14: ("他还在学", 0.38),
    15: ("苕帚？他怕这个", 0.40),
    16: (None, 0.0),
    17: ("快按住他", 0.42),
    18: ("总算能入棺了", 0.40),
    19: ("这手势，我没画完", 0.30),
    20: ("这笔，谁替我画的？", 0.30),
}


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    closing_punctuation = "，。！？；、：）》」』】”’"
    for paragraph in text.splitlines() or [""]:
        current = ""
        for char in paragraph:
            candidate = current + char
            if current and font.getlength(candidate) > max_width and char not in closing_punctuation:
                lines.append(current)
                current = char
            else:
                current = candidate
        if current:
            lines.append(current)
    return lines


def source_for(number: int) -> Path:
    prefix = rf"^{number:02d}_"
    candidates = sorted(path for path in SOURCE_DIR.iterdir() if re.match(prefix, path.name))
    if len(candidates) != 1:
        raise FileNotFoundError(f"图{number:02d} 源图数量异常：{candidates}")
    return candidates[0]


def draw_caption(
    image: Image.Image,
    text: str,
    y0: int,
    font: ImageFont.FreeTypeFont,
) -> int:
    draw = ImageDraw.Draw(image, "RGBA")
    max_width = int(image.width * MAX_BUBBLE_WIDTH)
    lines = wrap_text(text, font, max_width - 2 * PAD_X)
    bubble_width = int(max(font.getlength(line) for line in lines)) + 2 * PAD_X
    bubble_height = PAD_Y * 2 + LINE_HEIGHT * len(lines)
    x0 = int(image.width * 0.05) + CAPTION_SHIFT_X
    y0 = min(y0, image.height - bubble_height - 20)
    x0 = min(x0, image.width - bubble_width - 20)
    draw.rounded_rectangle(
        (x0, y0, x0 + bubble_width, y0 + bubble_height),
        radius=RADIUS,
        fill=(0, 0, 0, 150),
    )
    for index, line in enumerate(lines):
        text_y = y0 + PAD_Y + index * LINE_HEIGHT
        draw.text(
            (x0 + PAD_X, text_y),
            line,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=1,
            stroke_fill=(0, 0, 0, 255),
        )
    return y0 + bubble_height


def main() -> None:
    if not Path(FONT_PATH).exists():
        raise FileNotFoundError(FONT_PATH)
    if set(SUBTITLES) != set(range(1, 21)):
        raise ValueError("字幕图号必须完整覆盖 01—20")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    for number in range(1, 21):
        source = source_for(number)
        image = Image.open(source).convert("RGB").resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        text, y_fraction = SUBTITLES[number]
        if text:
            caption_y = int(image.height * y_fraction)
            for caption in text.splitlines():
                caption_y = draw_caption(image, caption, caption_y, font) + CAPTION_GAP
        output = OUTPUT_DIR / f"画工画僵尸_图{number:02d}_带字幕.png"
        image.save(output, "PNG", optimize=True)

    print(f"画工画僵尸 subtitle done: 20/20 -> {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
