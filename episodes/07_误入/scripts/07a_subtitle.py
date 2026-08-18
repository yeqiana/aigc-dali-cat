#!/usr/bin/env python3
"""误入 A《古镇茶馆·还席》字幕叠加与尺寸归一化。

输入：images/draft/图NN_*.png
输出：images/publish/07A_图NN_*.png（图07、图20为无字幕关键帧）
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "images" / "draft"
OUT = ROOT / "images" / "publish"
FONT = r"C:\Windows\Fonts\msyh.ttc"
TARGET = (1080, 1920)
PAD_X, PAD_Y = 28, 20
RADIUS = 20
LINE_H = 40

# (字幕, 纵向比例, 横向比例)。图07、图20保留战略性静默。
SUBS = {
    "01": ("我们来找地图上没有标注的旧水关，雨里却看见一间还在等人的茶馆。", 0.10, 0.05),
    "02": ("石桥走到尽头，手机上的定位停了，门里的鞋印却是新鲜的。", 0.48, 0.05),
    "03": ("茶还温着，可这间屋子明明冷得像废弃了很多年。", 0.08, 0.05),
    "04": ("我把杯子挪开了，桌面上那块温度却还没散。", 0.08, 0.05),
    "05": ("我们刚想离开，身上的衣服已经换成了这里的样式。", 0.58, 0.05),
    "06": ("下一秒，桌上已经摆好了不属于我们的饭，空位比我们的人数多一个。", 0.08, 0.05),
    "07": None,
    "08": ("我们没有吃那碗饭，可门槛下这块泥还是温的，像刚有人站过。", 0.08, 0.05),
    "09": ("巷口有人朝茶馆追过来，我才发现他们穿的衣服像旧照片里的。", 0.08, 0.05),
    "10": ("泥还没干，窗里面又像刚有人用手擦过。", 0.08, 0.05),
    "11": ("我只是想摸一下这扇窗，看看里面的雾为什么一直不散。", 0.52, 0.05),
    "12": ("窗外没有后院，只有一条更长的水巷，家家都像刚有人离开。", 0.08, 0.05),
    "13": ("他们追到桌边，却不看我们，只盯着那副空碗筷。", 0.08, 0.05),
    "14": ("我把唯一能垫脚的木凳拖到窗下，窗里的雾气被震散了一下。", 0.52, 0.05),
    "15": ("我撑住窗台时，手底下压着半枚从没见过的铜钱。", 0.08, 0.05),
    "16": ("我撞破窗框摔进水里，再抬头时，茶馆已经是一间封死的荒屋。", 0.08, 0.05),
    "17": ("我们找到了旧水关，现实里的水巷却已经荒了很多年。", 0.08, 0.05),
    "18": ("旧水关找到了，人也回来了，可我的背包里多了一样东西。", 0.52, 0.05),
    "19": ("手机里那张茶馆照片还在，里面的饭像刚端上桌。", 0.08, 0.05),
    "20": None,
}

# 新版素材白名单：旧圆环图片不得被脚本误打包进新版发布目录。
# 图01、图02、图18 已通过旧母题排查，暂允许使用旧版候选；其余帧必须等待新版文件。
SOURCE_NAMES = {
    "01": ("图01_雨里的旧水关_v3.png", "图01_雨里的旧水关_v2.png", "图01_雨里的旧水关_v1.png"),
    "02": ("图02_石桥尽头的门帘_v3.png", "图02_石桥尽头的门帘_v2.png", "图02_石桥尽头的门帘_v1.png"),
    "03": ("图03_杯里的余温_v4.png", "图03_杯里的余温_v3.png", "图03_杯里的余温_v2.png"),
    "04": ("图04_杯子挪开后的温差_v3.png",),
    "05": ("图05_换上的粗布袖口_v2.png",),
    "06": ("图06_饭桌仍有热气_v2.png",),
    "07": ("图07_空席仍有余温_v5.png", "图07_空席仍有余温_v4.png", "图07_空席仍有余温_v3.png"),
    "08": ("图08_后门还没干的泥_v3.png",),
    "09": ("图09_巷口的巡查人_v2.png",),
    "10": ("图10_木窗内侧的雾_v3.png",),
    "11": ("图11_我去摸那扇窗_v3.png", "图11_我去摸那扇窗_v2.png"),
    "12": ("图12_窗里是另一条水巷_v4.png", "图12_窗里是另一条水巷_v3.png", "图12_窗里是另一条水巷_v2.png"),
    "13": ("图13_巡查人盯着空席_v3.png", "图13_巡查人盯着空席_v2.png"),
    "14": ("图14_凳子震散窗雾_v3.png", "图14_凳子震散窗雾_v2.png"),
    "15": ("图15_窗台上的半枚铜钱_v3.png", "图15_窗台上的半枚铜钱_v2.png"),
    "16": ("图16_摔回现实_v4.png", "图16_摔回现实_v3.png", "图16_摔回现实_v2.png"),
    "17": ("图17_现实里的旧水关_v3.png",),
    "18": ("图18_背包里多出的半枚铜钱_v1.png",),
    "19": ("图19_照片里的空席_v3.png",),
    "20": ("图20_还席_v5.png", "图20_还席_v4.png", "图20_还席_v3.png"),
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


def find_source(key):
    for name in SOURCE_NAMES[key]:
        candidate = SRC / name
        if candidate.is_file():
            return candidate
    return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT, 28)
    completed = 0
    for key in sorted(SUBS, key=int):
        source = find_source(key)
        if source is None:
            print("MISS", key)
            continue

        image = Image.open(source).convert("RGB").resize(TARGET, Image.Resampling.BICUBIC)
        caption = SUBS[key]
        if caption is not None:
            text, y_fraction, x_fraction = caption
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

        output = OUT / f"07A_图{key}_{source.stem[4:]}_发布.png"
        image.save(output, "PNG")
        completed += 1

    print(f"subtitle done: {completed}/{len(SUBS)} -> {OUT}")


if __name__ == "__main__":
    main()
