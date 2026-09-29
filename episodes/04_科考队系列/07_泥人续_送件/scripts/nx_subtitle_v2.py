#!/usr/bin/env python3
"""泥人续《送件》V2 字幕叠加与发布图输出。

依据 standards/最终字幕视觉规范_V1.0.md：
1080x1920、微软雅黑粗体 42px、纯白字、4px 黑描边、无气泡、左对齐、
左右边距 72px、最大文字宽度 936px、行高 54px、默认 Y=1265-1380。
图06/10/16/19 为无字幕静默图。
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "images" / "v2_keyframe"
OUT = ROOT / "images" / "v2_subtitle"
PUB = ROOT / "images" / "v2_publish"
REPORT = ROOT / "docs" / "09_泥人续_送件_V2_字幕位置报告.txt"
FONT = r"C:\Windows\Fonts\msyhbd.ttc"
TARGET = (1080, 1920)
FONT_SIZE = 42
STROKE_WIDTH = 4
MARGIN = 72
MAX_TEXT_WIDTH = 936
LINE_HEIGHT = 54
DEFAULT_Y = 1280
UPPER_Y = 520
SHADOW_ALPHA = 128

SUBS = {
    "01": "泥人抱着铁盒跟回城后，我还是开了门。",
    "02": "盒子里多了一把钥匙，下面压着一个地址。",
    "03": "我再抬头，它已经挪到门槛前了。",
    "04": "纸条上的地址，是阿岚住的那栋旧楼。",
    "05": "她说，这把钥匙一直在用，根本没丢过。",
    "06": None,  # 静默图
    "07": "钥匙刚过门槛，门外就多了一个“阿岚”。",
    "08": "我还没缓过来，盒里又多了一只缺口的杯子。",
    "09": "我不信邪，又按第二个地址送了一次。",
    "10": None,  # 静默图
    "11": "两个地址，都出现了对应的泥人。",
    "12": "回到家，它已经站进门里了。",
    "13": "爸只看了一眼铁盒：别再替它送了。",
    "14": "钥匙一收回来，那个泥人就开始塌了。",
    "15": "最后一件，地址是我家。",
    "16": None,  # 静默图
    "17": "盒底还有一个包裹，上面是我妈的名字。",
    "18": "爸没拆，只把盒子重新锁上了。",
    "19": None,  # 静默图
    "20": "这次，它学的是我。",
}

# 手动位置修正只改这一张表：{图号: Y}；样式不允许改。
OVERRIDES = {}


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


def busyness(image, x0, y0, width, height):
    region = image.crop((x0, y0, x0 + width, y0 + height)).convert("L")
    edges = region.filter(ImageFilter.FIND_EDGES)
    return ImageStat.Stat(edges).stddev[0]


def draw_text(draw, x, y, lines, font):
    for index, line in enumerate(lines):
        ty = y + index * LINE_HEIGHT
        draw.text(
            (x + 1, ty + 2), line, font=font,
            fill=(0, 0, 0, SHADOW_ALPHA),
            stroke_width=STROKE_WIDTH + 2,
            stroke_fill=(0, 0, 0, SHADOW_ALPHA),
        )
        draw.text(
            (x, ty), line, font=font,
            fill=(255, 255, 255, 255),
            stroke_width=STROKE_WIDTH,
            stroke_fill=(0, 0, 0, 255),
        )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PUB.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT, FONT_SIZE)
    report = []
    done = 0
    silent = 0
    for key in sorted(SUBS, key=int):
        matches = sorted(SRC.glob(f"图{int(key):02d}_*.png"))
        if not matches:
            raise SystemExit(f"MISS 图{key}: no source under {SRC}")
        image = Image.open(matches[0]).convert("RGB").resize(
            TARGET, Image.Resampling.BICUBIC
        )
        text = SUBS[key]
        entry = {"frame": key, "y": None, "lines": 0, "y1280": None, "y520": None}
        if text:
            lines = wrap(text, font, MAX_TEXT_WIDTH)
            if len(lines) > 2:
                raise SystemExit(f"图{key} 字幕超过两行，请先修文案：{text}")
            y = OVERRIDES.get(key)
            if y is None:
                score_default = busyness(
                    image, MARGIN, DEFAULT_Y, MAX_TEXT_WIDTH, LINE_HEIGHT * len(lines)
                )
                score_upper = busyness(
                    image, MARGIN, UPPER_Y, MAX_TEXT_WIDTH, LINE_HEIGHT * len(lines)
                )
                y = DEFAULT_Y if score_default <= score_upper else UPPER_Y
                entry["y1280"] = round(score_default, 2)
                entry["y520"] = round(score_upper, 2)
            entry["y"] = y
            entry["lines"] = len(lines)
            drawer = ImageDraw.Draw(image, "RGBA")
            draw_text(drawer, MARGIN, y, lines, font)
        else:
            silent += 1
            entry["silent"] = True
        for out_dir in (OUT, PUB):
            out_dir.mkdir(parents=True, exist_ok=True)
            image.save(out_dir / f"NX_V2_图{int(key):02d}_带字幕.png", "PNG")
        done += 1
        report.append(entry)

    report_path = REPORT
    with report_path.open("w", encoding="utf-8") as fh:
        fh.write("《泥人续·送件》V2 字幕位置报告\n")
        fh.write(
            "样式：42px 微软雅黑粗体 / 纯白 / 4px黑描边 / 无气泡 / "
            "左对齐 / 边距72 / 默认Y=1265-1380\n"
        )
        fh.write(
            "图06、10、16、19为静默图，无字幕。位置由低信息带检测自动选择，"
            "用户目检后可改OVERRIDES。\n\n"
        )
        fh.write("图号 | 行数 | Y | Y=1280评分 | Y=520评分 | 说明\n")
        for entry in report:
            mark = "静默图" if entry.get("silent") else f"{entry['lines']}行"
            fh.write(
                f"{entry['frame']} | {mark} | {entry['y']} | "
                f"{entry['y1280']} | {entry['y520']}\n"
            )
    print(f"subtitle v2 done: {done}/20 -> {OUT} (+ {PUB}) silent={silent}")
    print(report_path)


if __name__ == "__main__":
    main()
