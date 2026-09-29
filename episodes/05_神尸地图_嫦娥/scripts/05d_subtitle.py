#!/usr/bin/env python3
"""05d 嫦娥：月背遗迹 字幕叠加脚本（按制作规范 §5.1-5.3）。

输入：assets/frames/图NN_*.png（941x1672）
处理：先统一缩放至 1080x1920，再覆盖旧时间码、叠加统一时间码和分镜字幕
输出：publish/05d_图NN_名称_带字幕.png（03/14 无字幕，仅时间码与缩放）

用法：
  python 05d_subtitle.py
"""

import re
import os
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "frames"
OUT = ROOT / "publish"
FONT = r"C:\Windows\Fonts\msyh.ttc"
TIME_FONT = r"C:\Windows\Fonts\consola.ttf"

# (文案, 纵向比例, 左偏移比例)。03/14 为无字幕关键帧。
# V1.4：字幕链按剧情可读性重写，连读可自洽成故事，不改变分镜结构与S/Z标签。
# V1.5：图03/14由无字幕关键帧补上解释性字幕，全片20帧均有字幕。
SUBS = {
    "01": ("师傅被带走那天，把月背回收任务交给了我。天空里，悬着不该出现的地球。", 0.40, 0.05),
    "02": ("那片冷白镜面里，映出一颗缺了一块的地球。", 0.13, 0.05),
    "03": ("我抬手，镜子里的倒影慢半拍才抬手。它像是另一个我。", 0.13, 0.05),
    "04": ("录像最后，他留了一句话：月亮上有东西在照我们。别让任何人再上去。", 0.45, 0.05),
    "05": ("天线上也起了这层反光。倒影里，多了一个不该在的人影。", 0.78, 0.05),
    "06": ("进去前，我默念师傅的话：反光不看超过三秒。", 0.13, 0.05),
    "07": ("遗迹墙面都是镜子。我数着秒，不敢看自己的倒影。", 0.78, 0.05),
    "08": ("师傅的采样箱，在镜墙深处。想拿回它，就得数自己的倒影。", 0.78, 0.05),
    "09": ("队友就在我旁边，声音却像从裂谷那头传来。", 0.13, 0.05),
    "10": ("队友开始喊我师傅的名字。我纠正，他一脸陌生。", 0.78, 0.05),
    "11": ("我手背上也起了那层膜。抬手，画面慢了一拍。", 0.13, 0.45),
    "12": ("镜子里，我们隔着几十米。可现实中，他就在我旁边。", 0.13, 0.05),
    "13": ("墙不是墙。那是一只埋在月岩里的手。", 0.13, 0.05),
    "14": ("裂谷不是谷。她闭着眼，整片遗迹都是她的身体。", 0.13, 0.05),
    "15": ("她胸口的月相盘是一面镜子，镜中的地球正在远离。", 0.13, 0.30),
    "16": ("地面让我撤回。我把安全索扣向裂谷那头的队友。", 0.76, 0.05),
    "17": ("拉他回来的时候，镜子里有两双手在拽。另一双，手背带着膜。", 0.13, 0.05),
    "18": ("师母说那是疯话。可回放里，师傅没有疯。", 0.13, 0.05),
    "19": ("隔着玻璃，我把照片举给他看。他点了点头。", 0.76, 0.05),
    "20": ("返航后，他们都开始说同一句话：别让任何人再上去。妈妈在门口，我怎么都走不到。", 0.76, 0.05),
}

PAD_X, PAD_Y = 28, 20
RADIUS = 20
LINE_H = 40
TARGET = (1080, 1920)
FPS = 30
BASE_TIME_SECONDS = 12 * 60 + 41
BASE_TIME_FRAME = 9
FRAME_STEP_SECONDS = 9


def timecode(key):
    """为20张静帧生成连续、可复核的记录仪时间码。"""
    total_frames = (BASE_TIME_SECONDS * FPS + BASE_TIME_FRAME) + (int(key) - 1) * FRAME_STEP_SECONDS * FPS
    seconds, frame = divmod(total_frames, FPS)
    minutes, second = divmod(seconds, 60)
    hour, minute = divmod(minutes, 60)
    return f"{hour:02d}:{minute:02d}:{second:02d}:{frame:02d}"


def draw_timecode(im, key, font):
    """覆盖各批生图中不一致的内嵌数字，再统一写入左上角。"""
    dr = ImageDraw.Draw(im, "RGBA")
    # 旧图的时间码出现在左上、底部中间或右下；暗带只压记录仪边缘，不遮剧情主体。
    dr.rectangle((0, 0, 430, 112), fill=(0, 0, 0, 255))
    dr.rectangle((0, 1780, 1080, 1920), fill=(0, 0, 0, 255))
    label = timecode(key)
    dr.text((38, 30), label, font=font, fill=(225, 230, 235, 255), stroke_width=1, stroke_fill=(0, 0, 0, 255))


def wrap(text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        t = cur + ch
        if font.getlength(t) > max_w and cur:
            if ch in "。！？；：" and len(cur) >= 1:
                cur = t
                continue
            cut = -1
            for p in "。！？；：":
                i = cur.rfind(p)
                if i > cut:
                    cut = i
            if cut >= 0:
                lines.append(cur[:cut + 1])
                cur = cur[cut + 1:] + ch
            else:
                lines.append(cur)
                cur = ch
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def find_src(key):
    pat = re.compile(r"^图" + key + r"_")
    cands = [f for f in SRC.iterdir() if f.is_file() and pat.match(f.name)]
    if not cands:
        return None
    return max(cands, key=lambda f: f.stat().st_mtime)


def short_name(src):
    m = re.match(r"^图\d+_(.+?)(?:_V\d+)?\.png$", src.name)
    return m.group(1) if m else "frame"


def save_png(im, path):
    """先写临时文件再替换；被索引/预览占用时退避重试。"""
    tmp = path.with_name(path.name + ".tmp")
    last = None
    for _ in range(8):
        try:
            im.save(tmp, "PNG")
            os.replace(str(tmp), str(path))
            return
        except OSError as e:
            last = e
            time.sleep(1.5)
    raise last


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*.tmp"):
        stale.unlink(missing_ok=True)
    font = ImageFont.truetype(FONT, 28)
    time_font = ImageFont.truetype(TIME_FONT if Path(TIME_FONT).exists() else FONT, 30)
    ok = 0
    for key in sorted(SUBS.keys(), key=int):
        src = find_src(key)
        if not src:
            print("MISS", key)
            continue
        im = Image.open(src).convert("RGB").resize(TARGET, Image.BICUBIC)
        draw_timecode(im, key, time_font)
        val = SUBS[key]
        out_name = "05d_图%s_%s_带字幕.png" % (key, short_name(src))
        if val is None:
            save_png(im, OUT / out_name)
            ok += 1
            continue
        text, y_frac, x_frac = val
        dr = ImageDraw.Draw(im, "RGBA")
        max_w = int(im.width * 0.55)
        lines = wrap(text, font, max_w - 2 * PAD_X)
        bubble_h = PAD_Y * 2 + LINE_H * len(lines)
        bubble_w = int(max(font.getlength(l) for l in lines)) + 2 * PAD_X
        y0 = int(im.height * y_frac)
        x0 = min(int(im.width * x_frac), max(0, im.width - bubble_w - 20))
        dr.rounded_rectangle(
            [x0, y0, x0 + bubble_w, y0 + bubble_h],
            radius=RADIUS,
            fill=(0, 0, 0, 150),
        )
        for i, line in enumerate(lines):
            ty = y0 + PAD_Y + i * LINE_H
            dr.text((x0 + PAD_X + 1, ty + 1), line, font=font, fill=(0, 0, 0, 255))
            dr.text((x0 + PAD_X, ty), line, font=font, fill=(255, 255, 255, 255))
        save_png(im, OUT / out_name)
        ok += 1
    print("subtitle done:", ok, "/", len(SUBS), "->", OUT)


if __name__ == "__main__":
    main()
