#!/usr/bin/env python3
"""S6 Dong Hai Long Gong subtitle overlay: K1 left-center method, width <=55%W, avoid subjects."""

import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC_V1 = ROOT / "images" / "s6_v1"
SRC_V2 = ROOT / "images" / "s6_v2_龙形更新"
OUT = ROOT / "images" / "s6_subtitle"
FONT = r"C:\Windows\Fonts\msyh.ttc"

SUBS = {
    "01": ("\u6211\u966a\u963f\u53d4\u51fa\u6700\u540e\u4e00\u8d9f\u6d77\u3002\u706f\u5149\u626b\u8fc7\u6d77\u5e95\uff0c\u649e\u89c1\u4e00\u7247\u53d1\u5149\u7684\u8001\u5efa\u7b51\u3002", 0.42, 0.05),
    "02": ("\u963f\u53d4\u8981\u9000\u4f11\u4e86\u3002\u624b\u673a\u91cc\u5b58\u7740\u4ed6\u4e09\u5341\u5e74\u524d\u62cd\u8fc7\u7684\u4e1c\u897f\u3002", 0.38, 0.05),
    "03": ("\u963f\u53d4\u8bf4\uff0c\u770b\u4e00\u773c\u5c31\u8d70\u3002\u58f0\u5450\u663e\u793a\u4e0b\u9762\u6709\u89c4\u6574\u7ed3\u6784\uff0c\u6211\u8fd8\u662f\u8c03\u4eae\u4e86\u706f\u3002", 0.45, 0.05),
    "04": ("\u77f3\u67f1\u4e0a\u7684\u9cde\u7eb9\u5728\u53d1\u5149\uff0c\u4e0d\u662f\u523b\u7684\uff0c\u50cf\u957f\u5728\u91cc\u9762\u3002", 0.45, 0.05),
    "05": ("\u963f\u53d4\u8bf4\uff0c\u770b\u5230\u53d1\u5149\u7684\u4e1c\u897f\u522b\u9760\u8fd1\uff0c\u522b\u5f00\u5f3a\u5149\u3002", 0.52, 0.05),
    "06": ("\u5efa\u7b51\u7fa4\u7684\u5c3d\u5934\uff0c\u7acb\u7740\u4e00\u6247\u5de8\u5927\u7684\u95e8\u3002\u95e8\u7f1d\u91cc\uff0c\u900f\u51fa\u4e0d\u8be5\u5728\u6df1\u6d77\u7684\u5149\u3002", 0.40, 0.05),
    "07": ("\u5bab\u95e8\u6253\u5f00\u3002\u90a3\u4e0d\u662f\u9057\u5740\u2014\u2014\u662f\u4e00\u6761\u76d8\u5728\u5bab\u6bbf\u4e0a\u7684\u9f99\u3002", 0.30, 0.08),
    "08": ("\u6c34\u6d41\u7a81\u7136\u6539\u4e86\u65b9\u5411\uff0c\u628a\u6211\u4eec\u5f80\u5bab\u95e8\u91cc\u63a8\u3002", 0.42, 0.05),
    "09": ("\u5b83\u7741\u5f00\u773c\u3002\u77b3\u5b54\u8f6c\u8fc7\u6765\uff0c\u770b\u5411\u6211\u4eec\u3002", 0.28, 0.05),
    "10": ("\u5b83\u53d1\u73b0\u6211\u4eec\u4e86\u3002\u6c34\u6d41\u5f00\u59cb\u5f80\u56de\u9876\uff0c\u6f5c\u822a\u5668\u5728\u6296\u3002", 0.28, 0.05),
    "11": ("\u5b83\u9760\u8fc7\u6765\u3002\u4e00\u53ea\u77b3\u5b54\uff0c\u6bd4\u6211\u4eec\u6574\u6247\u89c2\u5bdf\u7a97\u8fd8\u5927\u3002", 0.28, 0.05),
    "12": ("\u5b83\u6ca1\u6709\u653b\u51fb\uff0c\u53ea\u662f\u6162\u6162\u6446\u4e86\u4e00\u4e0b\u5c3e\u3002\u6c34\u6d41\u5f00\u59cb\u9001\u6211\u4eec\u51fa\u53bb\u3002", 0.30, 0.05),
    "13": ("\u6211\u5173\u6389\u4e86\u706f\u3002\u9ed1\u6697\u91cc\uff0c\u53ea\u6709\u5b83\u7684\u5149\u8fd8\u5728\u3002", 0.50, 0.05),
    "14": ("\u6211\u4eec\u9000\u51fa\u4e86\u5bab\u95e8\u3002\u95e8\u5728\u8eab\u540e\u5408\u62e2\uff0c\u5b83\u8fd8\u5728\u770b\u7740\u6211\u4eec\u3002", 0.35, 0.05),
    "15": ("\u963f\u53d4\u8bf4\uff0c\u90a3\u5f20\u7167\u7247\u662f\u771f\u7684\u3002\u4e0a\u62a5\u4e86\uff0c\u88ab\u538b\u4e86\u4e0b\u6765\u3002", 0.52, 0.05),
    "16": ("\u6211\u5728\u5907\u5fd8\u5f55\u91cc\u8bb0\u4e0b\uff1a\u5750\u6807\u5c01\u5b58\u3002\u8fd9\u91cc\u7684\u4e8b\uff0c\u4e0d\u518d\u4e0a\u62a5\u3002", 0.45, 0.05),
    "17": ("\u8239\u79bb\u5f00\u4e86\u90a3\u7247\u6d77\u3002\u6c34\u9762\u5f88\u5e73\uff0c\u50cf\u4ec0\u4e48\u90fd\u6ca1\u53d1\u751f\u8fc7\u3002", 0.38, 0.05),
    "18": ("\u4e0b\u8239\u524d\uff0c\u6211\u5728\u7532\u677f\u4e0a\u770b\u5230\u4e00\u9053\u6f6e\u75d5\uff0c\u5f62\u72b6\u50cf\u4e00\u7247\u9cde\u3002", 0.52, 0.05),
    "19": ("\u6211\u628a\u6d77\u91cc\u7684\u9cde\u7eb9\u622a\u56fe\u548c\u5b83\u6bd4\u4e86\u4e00\u4e0b\uff0c\u4e00\u6a21\u4e00\u6837\u3002", 0.52, 0.05),
    "20": ("\u6f6e\u75d5\u8fd8\u5728\u53d1\u7740\u5fae\u5149\u3002\u90a3\u6761\u9f99\uff0c\u8fd8\u5728\u4e0b\u9762\u3002", 0.38, 0.05),
}

V2_MAP = {
    "07": "\u56fe07_\u9f99\u771f\u8eab_v4_\u7425\u73c0\u91d1\u773c.png",
    "09": "\u56fe09_\u5b83\u7741\u5f00\u4e86\u773c_v2_\u53c2\u8003\u56fe\u57fa\u51c6.png",
    "10": "\u56fe10_\u88ab\u53d1\u73b0\u4e86_v2_\u53c2\u8003\u56fe\u57fa\u51c6.png",
    "11": "\u56fe11_\u77b3\u5b54\u5927\u8fc7\u89c2\u5bdf\u7a97_v2_\u53c2\u8003\u56fe\u57fa\u51c6.png",
    "12": "\u56fe12_\u4e00\u6b21\u6446\u5c3e_v2_\u53c2\u8003\u56fe\u57fa\u51c6.png",
    "14": "\u56fe14_\u5bab\u95e8\u5408\u62e2_v2_\u53c2\u8003\u56fe\u57fa\u51c6.png",
}

PAD_X, PAD_Y = 28, 20
RADIUS = 20
LINE_H = 40


def wrap(text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        t = cur + ch
        if font.getlength(t) > max_w and cur:
            if ch in ".\uff01\uff1f\uff1b" and len(cur) >= 1:
                cur = t; continue
            lines.append(cur); cur = ch
        else:
            cur = t
    if cur: lines.append(cur)
    return lines


def find_src(k):
    if k in V2_MAP:
        p = SRC_V2 / V2_MAP[k]
        if p.exists():
            return p
    for f in sorted(SRC_V1.iterdir()):
        if f.is_file() and f.stem.startswith("\u56fe" + k + "_"):
            return f
    k2 = "%02d" % int(k)
    for f in sorted(SRC_V1.iterdir()):
        if f.is_file() and f.stem.startswith("\u56fe" + k2 + "_"):
            return f
    return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT, 28)
    ok = 0
    for key in sorted(SUBS.keys(), key=int):
        val = SUBS[key]
        src = find_src(key)
        if not src:
            print("MISS", key)
            continue
        im = Image.open(src).convert("RGB")
        w, h = im.size
        text, y_frac, x_frac = val
        dr = ImageDraw.Draw(im, "RGBA")
        max_w = int(w * 0.55)
        lines = wrap(text, font, max_w - 2 * PAD_X)
        bubble_h = PAD_Y * 2 + LINE_H * len(lines)
        bubble_w = int(max(font.getlength(l) for l in lines)) + 2 * PAD_X
        y0 = int(h * y_frac)
        x0 = min(int(w * x_frac), max(0, w - bubble_w - 20))
        dr.rounded_rectangle(
            [x0, y0, x0 + bubble_w, y0 + bubble_h],
            radius=RADIUS, fill=(0, 0, 0, 150),
        )
        for i, line in enumerate(lines):
            ty = y0 + PAD_Y + i * LINE_H
            dr.text((x0 + PAD_X + 1, ty + 1), line, font=font, fill=(0, 0, 0, 255))
            dr.text((x0 + PAD_X, ty), line, font=font, fill=(255, 255, 255, 255))
        out_f = OUT / ("S6_" + src.name)
        im.save(out_f, "PNG")
        ok += 1
    print("subtitle done:", ok, "/ 20 ->", OUT)


if __name__ == "__main__":
    main()
