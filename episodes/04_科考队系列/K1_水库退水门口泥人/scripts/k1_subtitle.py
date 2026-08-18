#!/usr/bin/env python3
"""历史脚本：K1 发布后源图已清理，最终发布图保留在 k1_publish。

用法:
  python k1_subtitle.py

字幕文案取自分镜文档 06 各图「字幕」行；图01 为封面不叠字（抖音图集首图自动叠加标题）。
位置按 §5.2 逐张微调，主体居中或底部的图统一放顶部暗区。
"""

import os
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "images" / "k1_keyframe"
OUT = ROOT / "images" / "k1_subtitle"
FONT = r"C:\Windows\Fonts\msyh.ttc"

# 每条字幕为 (文案, 纵向位置, 左偏移比例)。位置原则：靠左中放置，避开右边/顶部/底部与画面主体。
SUBS = {
    "01": ("水库回水前，我陪爸来测最后一次水位。每户门口，都坐着一个泥人。", 0.42, 0.05),
    "02": ("那些泥人全朝着屋里，像在等原来的住户回来。", 0.16, 0.03),
    "03": ("我们要在六点回水前补完三支标。爸是唯一认得旧路的人。", 0.30, 0.06),
    "04": ("第二个泥人穿着和我爸一样的外套，连磨损都在同一边。", 0.30, 0.25),
    "05": ("屋里叫谁的名字都别答，更不能进自己从前的家。", 0.30, 0.05),
    "06": ("扫描只确认一件事：每间空屋里，都多出一个人形。", 0.24, 0.28),
    "07": ("全镇只有我爸家的门口是空的，门却刚被人擦干净。", 0.46, 0.05),
    "08": ("泥地上的鞋印和我爸一模一样，却比我们先走进屋里。", 0.35, 0.05),
    "09": ("屋里有人用我妈的声音叫他。爸说：我回来拿照片。", 0.30, 0.05),
    "10": ("我伸手抓住他时，他已经跨过了自己家的门槛。", 0.26, 0.04),
    "11": ("屋里站着年轻三十岁的他，手里抱着我家的旧铁盒。", 0.28, 0.25),
    "12": ("他碰到铁盒后，湿泥沿着袖口往上长，皱纹开始消失。", 0.30, 0.20),
    "13": ("镜子里只剩年轻的他，真正的我爸却还站在我旁边。", 0.46, 0.04),
    "14": ("街上所有泥人同时站了起来，脸全都转向这间屋。", 0.32, 0.18),
    "15": ("每扇窗后都多了一个住户。水还没回来，镇子先住满了。", 0.45, 0.18),
    "16": ("我把安全绳套在爸腰上，另一头却被屋里的他抓住了。", 0.24, 0.05),
    "17": ("爸松开铁盒，抓住了我的手。屋里的年轻人第一次没有学他。", 0.33, 0.04),
    "18": ("他承认妈妈走后回来过一次，也知道屋里的声音不是她。", 0.30, 0.30),
    "19": ("最后一支水位标刚装完，旧镇就重新沉进了水里。", 0.48, 0.04),
    "20": ("铁盒明明留在水下。第二天，它和年轻的我爸一起坐在家门口。", 0.26, 0.15),
}

PAD_X, PAD_Y = 28, 20
RADIUS = 20
MAX_BUBBLE_W_RATIO = 0.75
LINE_H = 40


def wrap(text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        t = cur + ch
        if font.getlength(t) > max_w and cur:
            # 句号/问号等结尾标点不单独成行
            if ch in "\u3002\uff01\uff1f\uff1b" and len(cur) >= 1:
                cur = t
                continue
            lines.append(cur)
            cur = ch
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT, 28)
    pat = re.compile(r"^K1_\u56fe(\d+)_")
    by_num = {}
    for name in os.listdir(SRC):
        m = pat.match(name)
        if m and name.endswith("_final.jpg"):
            by_num[m.group(1)] = SRC / name

    ok = 0
    for key, val in sorted(SUBS.items()):
        src_path = by_num.get(key)
        if not src_path:
            print("MISS", key)
            continue
        im = Image.open(src_path).convert("RGB")
        w, h = im.size
        out_name = src_path.stem + ".png"
        if val is None:
            im.save(OUT / out_name, "PNG")
            ok += 1
            continue
        text, y_frac, x_frac = val
        dr = ImageDraw.Draw(im, "RGBA")
        max_w = int(w * min(MAX_BUBBLE_W_RATIO, 0.55))
        lines = wrap(text, font, max_w - 2 * PAD_X)
        bubble_h = PAD_Y * 2 + LINE_H * len(lines)
        bubble_w = int(max(font.getlength(l) for l in lines)) + 2 * PAD_X
        y0 = int(h * y_frac)
        x0 = min(int(w * x_frac), max(0, w - bubble_w - 20))
        dr.rounded_rectangle(
            [x0, y0, x0 + bubble_w, y0 + bubble_h],
            radius=RADIUS,
            fill=(0, 0, 0, 150),
        )
        for i, line in enumerate(lines):
            ty = y0 + PAD_Y + i * LINE_H
            dr.text((x0 + PAD_X + 1, ty + 1), line, font=font, fill=(0, 0, 0, 255))
            dr.text((x0 + PAD_X, ty), line, font=font, fill=(255, 255, 255, 255))
        im.save(OUT / out_name, "PNG")
        ok += 1
    print("subtitle done:", ok, "/", len(SUBS), "->", OUT)


if __name__ == "__main__":
    main()
