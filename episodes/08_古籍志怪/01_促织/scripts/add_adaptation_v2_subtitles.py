#!/usr/bin/env python3
"""《促织》原版骨架改编版：20 张图片尺寸归一化与字幕合成。

输入：images/adaptation_v2/keyframe/ 下新版 20 张 941x1672 图片
输出：images/adaptation_v2/subtitle/ 下 20 张 1080x1920 带字幕图片

不覆盖旧版 keyframe/subtitle；新版字幕只使用 docs/10 的改编文案。
"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "images" / "adaptation_v2" / "keyframe"
OUTPUT_DIR = ROOT / "images" / "adaptation_v2" / "subtitle"
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"
TARGET_SIZE = (1080, 1920)
FONT_SIZE = 28
PAD_X, PAD_Y = 28, 20
LINE_HEIGHT = 40
RADIUS = 20
MAX_BUBBLE_WIDTH = 0.55


# 与 docs/10_促织_原版骨架改编20张正式分镜_V1.0.md 一致。
# y 为气泡顶部比例；全部保持左侧中部暗区优先，再由视觉门禁逐图复核。
SUBTITLES: dict[int, tuple[str, float]] = {
    1: ("我叫成名，原本读书求功名，后来被充作里正役；如今县衙又逼我交虫。", 0.34),
    2: ("交不上这一只，差役就会来搜我家，拿走剩下的东西。", 0.40),
    3: ("妻子花钱求卜，巫者没说一句话，只扔出一张画。", 0.40),
    4: ("画上有殿阁、荆棘和一只青头虫，我只能照着找。", 0.40),
    5: ("村东大佛阁后，石头和画里一模一样，蛤蟆突然跳进草丛。", 0.40),
    6: ("我跟着蛤蟆扒开荆棘，终于看见一只伏在石穴里的蟋蟀。", 0.42),
    7: ("这只青麻头体壮翅金，我把全家的活路都押在它身上。", 0.40),
    8: ("我把它养在盆里，妻子只叮嘱孩子：千万别碰这只虫。", 0.40),
    9: ("我回来时，孩子已经掀开了虫盆，蟋蟀从他手边跳了出去。", 0.40),
    10: ("第一只虫死了，孩子也吓得不见踪影；我不敢想他去了哪里。", 0.38),
    11: ("井边只剩孩子的鞋和翻倒的盆，妻子拉住我，不让我往下看。", 0.42),
    12: ("孩子竟然醒了，却像丢了魂，只盯着空笼一言不发。", 0.40),
    13: ("原以为虫没了，门外却又爬来一只小小的黑赤蟋蟀。", 0.42),
    14: ("它看着很弱，偏偏那只人人夸的蟹壳青先向它撞了过来。", 0.42),
    15: ("小虫突然咬住强虫的脖子，连院里扑来的鸡都没能碰到它。", 0.38),
    16: ("县令原本嫌它太小，斗过几场后，亲手把它送进了贡笼。", 0.40),
    17: ("巡抚接到贡虫，立刻写文上报；这只小虫开始往宫里去了。", 0.40),
    18: ("宫里琴声一响，它竟随着节拍起舞，所有贡虫都比不上它。", 0.40),
    19: ("县令因献虫得赏，我也免了里正役，家里终于有钱送我入学。", 0.40),
    20: ("孩子后来恢复了，只对我说：那晚我好像变成了笼里的虫。", 0.40),
}


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
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
    pattern = re.compile(rf"^促织_(?:改编P0|改编)_图{number:02d}_.+\.png$")
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
        draw.text(
            (x0 + PAD_X, text_y),
            line,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=1,
            stroke_fill=(0, 0, 0, 255),
        )


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
        output = OUTPUT_DIR / f"促织_改编_图{number:02d}_带字幕.png"
        image.save(output, "PNG", optimize=True)

    print(f"adaptation v2 subtitle done: 20/20 -> {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
