#!/usr/bin/env python3
"""S1《墨脱·修行洞窟》基础图尺寸归一化与字幕合成。"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "images" / "keyframe"
OUT = ROOT / "images" / "subtitle"
FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"
TARGET = (1080, 1920)
PAD_X, PAD_Y = 28, 20
RADIUS = 20
LINE_H = 40

FRAME_FILES = {
    1: "1.png",
    2: "2.png",
    3: "图03_设备坏了洞里却是暖的_v3.png",
    4: "4.png",
    5: "5.png",
    6: "6.png",
    7: "7.png",
    8: "8.png",
    9: "9.png",
    10: "10_v2.png",
    11: "图11_羽毛后面站着一个人_v3.png",
    12: "12.png",
    13: "13_v2.png",
    14: "14.png",
    15: "15.png",
    16: "16_v2.png",
    17: "17.png",
    18: "18.png",
    19: "19.png",
    20: "20.png",
}

SUBTITLES = {
    1: "我叫林澈，曾是第七科考队的人。父亲林远川失踪前，最后标记了墨脱，还留下两个字：羽化。这次我和旧同事青岚、从小一起长大的川儿进山，要找的就是我爸最后留下的线索，弄清他当年看见了什么。",
    2: "父亲失踪前，留下过一本缺页的地图。墨脱，是他最后标记过的地方。此后，地图上再没有新的记录。",
    3: "雨季封山前，我们按父亲留下的地图找到了这里。相比洞外的湿冷，洞内竟然异常温暖。",
    4: "一进洞，外面的雨声就远了。连脚下的地面，都是干的。",
    5: "次仁是当地研究者，我爸以前联系过他；达瓦是这次带我们进山的当地向导。看到我爸留下的标记，次仁沉默了很久，只提醒我：别再往里面走。",
    6: "达瓦说，里面那具不腐的遗体叫“遗蜕”。老人说，那是羽化后留下的壳。别靠近，也别碰发光的石壁。",
    7: "可那具遗蜕没有腐烂，像只是睡着了。我第一次怀疑，羽化也许真的存在。",
    8: "偏偏这时，我们用来记录位置的定位器滑到了遗蜕旁边。我得进去拿回来。",
    9: "青岚先把退路固定好。可我看着那道纹路，还是伸出了手。",
    10: "指尖一碰，光就沿着手腕往上走。洞里太暖了，我突然不想松手。",
    11: "羽毛后面，站着一个人。那种站姿，我只在我爸的旧照片里见过。",
    12: "他没有说话。只是抬着手，像是在等我过去。",
    13: "我往前走了一步，又一步。青岚和川儿的声音，越来越远。",
    14: "川儿终于从后面抓住了我。可前面那个人影，还像我爸一样站着。",
    15: "我还是不想空手离开。被川儿往回拽时，我顺着裂口掰下了一块石片。",
    16: "羽毛突然全部往洞里倒流。等我再抬头，那个人影已经不见了。",
    17: "他们把我拖出了洞。重新核对位置后，我们才确定：这里就是父亲地图上最后标记的地方。",
    18: "离开后，次仁才承认，我爸当年也跟他来过这里。他们见过那道光，却没碰发光石壁，也没带走任何东西。我爸只把断纹抄进地图，那页还没补完，人就失踪了，后来只找回了这本缺页的地图。",
    19: "石片还在发热，我手腕上的痕迹也没有消失。青岚只说：先收好，暂时别让其他人知道。",
    20: "回去后，我们发现石片上的断纹，正好补上了父亲地图没画完的那一段。原来他留下的不是石片，而是一条没走完的路线。它指向山外——一片地图上没有名字、远看却像海一样的白色荒原。",
}

# 默认中左；高风险画面避开遗蜕、父亲身影、石片和手腕。
POSITIONS = {
    # 统一放在左侧中部，避开顶部留白不足和底部关键动作；绘制时仍会按气泡高度自动兜底。
    1: (0.05, 0.38), 2: (0.05, 0.38), 3: (0.05, 0.38), 4: (0.05, 0.38),
    5: (0.05, 0.38), 6: (0.05, 0.38), 7: (0.05, 0.38), 8: (0.05, 0.38),
    9: (0.05, 0.38), 10: (0.05, 0.38), 11: (0.05, 0.38), 12: (0.05, 0.38),
    13: (0.05, 0.38), 14: (0.05, 0.38), 15: (0.05, 0.38), 16: (0.05, 0.38),
    17: (0.05, 0.38), 18: (0.05, 0.38), 19: (0.05, 0.38), 20: (0.05, 0.38),
}


def wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
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


def normalize(source: Path) -> Image.Image:
    return ImageOps.fit(
        Image.open(source).convert("RGB"),
        TARGET,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT_PATH, 28)
    for number in range(1, 21):
        source = SRC / FRAME_FILES[number]
        if not source.exists():
            raise FileNotFoundError(source)

        base = normalize(source)
        # 同步覆盖基础图，确保 keyframe 目录也是正式尺寸。
        base.save(source, "PNG", optimize=True)

        image = base.copy()
        draw = ImageDraw.Draw(image, "RGBA")
        lines = wrap(SUBTITLES[number], font, int(image.width * 0.55) - 2 * PAD_X)
        bubble_height = PAD_Y * 2 + LINE_H * len(lines)
        bubble_width = int(max(font.getlength(line) for line in lines)) + 2 * PAD_X
        x_fraction, y_fraction = POSITIONS[number]
        x0 = min(int(image.width * x_fraction), image.width - bubble_width - 20)
        y0 = min(int(image.height * y_fraction), image.height - bubble_height - 20)
        draw.rounded_rectangle(
            [x0, y0, x0 + bubble_width, y0 + bubble_height],
            radius=RADIUS,
            fill=(0, 0, 0, 150),
        )
        for index, line in enumerate(lines):
            text_y = y0 + PAD_Y + index * LINE_H
            draw.text((x0 + PAD_X + 1, text_y + 1), line, font=font, fill=(0, 0, 0, 255))
            draw.text((x0 + PAD_X, text_y), line, font=font, fill=(255, 255, 255, 255))

        output = OUT / f"S1_图{number:02d}_带字幕.png"
        image.save(output, "PNG", optimize=True)

    print(f"基础图尺寸归一化并完成字幕：20/20 -> {OUT}")


if __name__ == "__main__":
    main()
