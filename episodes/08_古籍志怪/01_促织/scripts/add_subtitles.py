#!/usr/bin/env python3
"""《促织》20 张正式图：尺寸归一化与字幕叠加。

输入：images/keyframe/促织_关键帧_图NN_*.png（当前为 941x1672）
输出：images/subtitle/促织_图NN_..._带字幕.png（1080x1920）

只做确定性的尺寸归一化和文字叠加，不重绘原图，不覆盖 keyframe 原始资产。
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
FONT_SIZE = 28
PAD_X, PAD_Y = 28, 20
LINE_HEIGHT = 40
RADIUS = 20
MAX_BUBBLE_WIDTH = 0.55


# 文案与 05_促织_20张正式分镜_V1.0.md 保持一致。
# y 为气泡顶部的画面比例；x 固定在左侧暗区，逐图留出右侧主体空间。
SUBTITLES: dict[int, tuple[str, float]] = {
    1: ("我叫成名，是村里的里正，被限期交一只斗虫，可家里已经没有退路了。", 0.38),
    2: ("十天内交不上虫，差役就会从我家剩下的东西里找。", 0.40),
    3: ("笼子明明是空的，门缝上却挂着孩子袖口的线。", 0.38),
    4: ("她把家里最后几枚钱塞给我，说村口那面荒墙有人见过虫。", 0.40),
    5: ("荒墙里没有灯，只有新掉的土粉和几道细得不像鼠子的爪痕。", 0.38),
    6: ("他说子时前别把虫带进孩子房，可没说这虫到底从哪来。", 0.40),
    7: ("我从砖缝里掏出它时，后足上已经缠着一根土白色的线。", 0.38),
    8: ("妻子不让我靠近孩子，可我得先确认这只虫能不能交差。", 0.40),
    9: ("孩子敲了三下床，笼里的虫也敲了三下，灯焰却朝井口偏了。", 0.36),
    # 图 10 的笼门和手部位于左中部，字幕上移到暗墙，避免覆盖触发动作。
    10: ("我掀开笼盖只想确认它，可它先跳过孩子的床沿。", 0.25),
    11: ("她把孩子拉回来时，井沿、笼门和袖口各少了一截同样的线。", 0.38),
    12: ("我看见它停在井沿，脚上的土粉和孩子袖口是一种颜色。", 0.40),
    13: ("我把它装进新笼，妻子只说了一句：这次别再打开。", 0.38),
    14: ("县衙的虫都在笼里乱撞，只有我这只安静得像在等什么。", 0.38),
    15: ("它没有变大，只是那只更大的虫先退了。", 0.40),
    16: ("他们围着我的笼子喊合格，我第一次敢相信差役会停在这里。", 0.38),
    17: ("木匣盖上朱印，差役终于把我家的名字从文书上划掉了。", 0.40),
    18: ("孩子醒了，却只记得井边有人在笼里敲门。", 0.40),
    19: ("我把空笼翻过来，里面多了三道像孩子指甲留下的刻痕。", 0.38),
    20: ("虫已经交了，孩子也醒了，可笼里的三道刻痕还在。", 0.40),
}


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """按汉字宽度换行，避免标点落在新行开头。"""
    lines: list[str] = []
    current = ""
    closing_punctuation = "，。！？；、：）》」』】”’"
    for char in text:
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
    pattern = re.compile(rf"^促织_关键帧_图{number:02d}_.+\.png$")
    candidates = sorted(path for path in SOURCE_DIR.iterdir() if pattern.match(path.name))
    if len(candidates) != 1:
        raise FileNotFoundError(f"图{number:02d} 源图数量异常：{candidates}")
    return candidates[0]


def draw_caption(image: Image.Image, text: str, y_fraction: float, font: ImageFont.FreeTypeFont) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    max_width = int(image.width * MAX_BUBBLE_WIDTH)
    lines = wrap_text(text, font, max_width - 2 * PAD_X)
    bubble_width = int(max(font.getlength(line) for line in lines)) + 2 * PAD_X
    bubble_height = PAD_Y * 2 + LINE_HEIGHT * len(lines)
    x0 = int(image.width * 0.05)
    y0 = min(int(image.height * y_fraction), image.height - bubble_height - 20)
    x0 = min(x0, image.width - bubble_width - 20)
    draw.rounded_rectangle(
        (x0, y0, x0 + bubble_width, y0 + bubble_height),
        radius=RADIUS,
        fill=(0, 0, 0, 150),
    )
    for index, line in enumerate(lines):
        text_y = y0 + PAD_Y + index * LINE_HEIGHT
        # 轻微黑色描边提高暗光画面中的白字可读性。
        draw.text((x0 + PAD_X, text_y), line, font=font, fill=(255, 255, 255, 255), stroke_width=1, stroke_fill=(0, 0, 0, 255))


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
        draw_caption(image, text, y_fraction, font)
        output_name = source.stem.replace("促织_关键帧_", "促织_") + "_带字幕.png"
        image.save(OUTPUT_DIR / output_name, "PNG", optimize=True)

    print(f"subtitle done: 20/20 -> {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
