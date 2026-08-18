#!/usr/bin/env python3
"""《种梨》：20 张图片尺寸归一化与字幕合成。

输入：images/keyframe/ 下 20 张 941x1672 图片
输出：images/subtitle/ 下 20 张 1080x1920 带字幕图片

文案与 docs/05_种梨_20张正式分镜_V1.0.md 一致；不覆盖 keyframe 原图。
"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "images" / "keyframe"
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
SUBTITLES: dict[int, tuple[str, float]] = {
    1: ("又来集上卖梨了", 0.30),
    2: ("来了个道士，没钱还非要买梨\n还是路过的婆婆好心，给他买了一个", 0.42),
    3: ("不是，什么情况\n我没看错吧！平地长了一颗...梨树？", 0.36),
    4: ("一定是幻觉", 0.30),
    5: ("怎么感觉这么像我卖的梨", 0.36),
    6: ("这老道士人还怪好的，给路人分上梨了", 0.40),
    7: ("不对，我的梨怎么少了一个", 0.36),
    8: ("老道士！还我梨", 0.40),
    9: ("别跑", 0.36),
    10: ("我的架子车啊", 0.34),
    11: ("扛着树还跑这么快...累死我了", 0.36),
    12: ("这是什么", 0.38),
    13: ("断了的梨树变成车把了吗", 0.40),
    14: ("红绳也一模一样", 0.38),
    15: ("车坏了，梨还没了，好气好气", 0.36),
    16: ("他们拿的可都是我的梨啊呜呜呜....", 0.30),
    17: ("命运戏弄苦命人呐...真是倒霉", 0.38),
    18: ("还好地上还有点梨没人看到...", 0.40),
    19: ("我将彻夜研究这些梨", 0.42),
    20: ("以后的人生座右铭就改成：别惹老道士", 0.36),
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
    pattern = re.compile(rf"^种梨_图{number:02d}_.+\.png$")
    candidates = sorted(path for path in SOURCE_DIR.iterdir() if pattern.match(path.name))
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
        caption_y = int(image.height * y_fraction)
        for caption in text.splitlines():
            caption_y = draw_caption(image, caption, caption_y, font) + CAPTION_GAP
        output = OUTPUT_DIR / f"种梨_图{number:02d}_带字幕.png"
        image.save(output, "PNG", optimize=True)

    print(f"种梨 subtitle done: 20/20 -> {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
