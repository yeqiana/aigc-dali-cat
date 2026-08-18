# -*- coding: utf-8 -*-
"""历史脚本：S4 发布后源图已清理，最终发布图保留在 s4_subtitle。"""
import os
import re
from PIL import Image, ImageDraw, ImageFont

SRC = os.environ["S4_SRC"]
OUT = os.environ["S4_OUT"]
FONT = r"C:\Windows\Fonts\msyh.ttc"

SUBS = {
    # 封面不叠字幕：抖音图文会在首图底部自动叠加标题+简介，封面文字与平台重复且遮挡主体
    "01": None,
    "02": ("进山那天雾很大。老周说，这片林子去年就有科考队来过。", "mid"),
    "03": ("相机位到了，地上是一圈湿泥地。蹲下去看，没有任何足迹。", "bottom"),
    "04": ("回营地插上读卡器，内存卡里多了一张照片。拍摄时间，昨晚三点十二分。", "top"),
    "05": ("老周说，可能是蹲着的野兽，红外相机常拍到动物。", "mid"),
    "06": ("第二天，又一张。照片里的人，比前一天近了一截。", "bottom"),
    "07": ("第三张，背景里出现了我们的帐篷。他蹲在营地边上。", "bottom"),
    "08": ("按规范做了足迹勘察，半径五米：无足迹，无压痕。", "bottom"),
    "09": ("翻相机日志，连续三天，凌晨三点十二分都没有任何触发记录。", "bottom"),
    "10": ("我问了保护区，他们回函：这个相机位去年就撤了，编号也没登记。", "bottom"),
    "11": ("照片放大打印，蹲着的人，肩膀上有反光的条纹。", "bottom"),
    "12": ("内存卡最后一张，是从蹲着的位置拍的。拍摄时间，是明天。", "top"),
    "13": ("照片里的人形蹲着，轮廓很清楚。他没有脸，但他在看镜头。", "top"),
    "14": ("放大再看，他的手指向镜头——指向相机，也指向我。", "top"),
    "15": ("当晚我去了相机位。他站起来，转向我。雾里就只剩我一个人。", "top"),
    "16": ("雾没有散，贴着地面往营地方向挪了过去。", "top"),
    "17": ("第二天一早，支架的镜头不知什么时候转向了营地。", "top"),
    "18": ("核对了一夜：相机快门只响了四次，卡里却有三十七张照片。", "bottom"),
    "19": ("相机时间比手机快了六个小时。它还在\u201c拍\u201d，只是不在现在。", "bottom"),
    "20": ("档案里翻到1985年的记录，写着同样的话。手机上调阅记录，是空的。", "bottom"),
    "21": ("相机自己开不了机。可它还在\u201c拍\u201d。拍的人，不是相机。", "bottom"),
    "22": ("凌晨三点，营地相机拍到帐篷门口蹲着一个人。时间戳，是明天。", "top"),
    "23": ("掀开帐篷帘，门口空着，地上什么都没有。", "bottom"),
    "24": ("我还没碰它。内存卡自己弹了出来，桌面上多了一道水痕。", "bottom"),
    "25": ("我把照片全删了。屏幕暗下去之前，门口好像还蹲着一个人。", "top"),
}

COVER_TAG = "档案编号 No.4 \u00b7 \u6b64\u524d\u65e0\u4eba\u8c03\u9605"

W, H = 1080, 1920
PAD_X, PAD_Y = 28, 20
RADIUS = 20
MAX_BUBBLE_W = int(W * 0.75)
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
    os.makedirs(OUT, exist_ok=True)
    font = ImageFont.truetype(FONT, 28)
    pat = re.compile(r"^S4_\u56fe(\d+)_")
    by_num = {}
    for name in os.listdir(SRC):
        m = pat.match(name)
        if m:
            by_num[m.group(1)] = os.path.join(SRC, name)

    ok = 0
    for key, val in SUBS.items():
        src_path = by_num.get(key)
        if not src_path:
            print("MISS", key)
            continue
        im = Image.open(src_path).convert("RGB")
        if val is None:
            # 封面：不叠字幕，原图直出（平台会在首图叠加标题+简介）
            im.save(os.path.join(OUT, os.path.basename(src_path)), "PNG")
            ok += 1
            continue
        text, pos = val
        dr = ImageDraw.Draw(im, "RGBA")
        lines = wrap(text, font, MAX_BUBBLE_W - 2 * PAD_X)
        bubble_h = PAD_Y * 2 + LINE_H * len(lines)
        bubble_w = int(max(font.getlength(l) for l in lines)) + 2 * PAD_X
        if pos == "top":
            y0 = int(H * 0.05)
        elif pos == "mid":
            y0 = int(H * 0.55)
        else:
            y0 = int(H * 0.78)
        x0 = (W - bubble_w) // 2
        dr.rounded_rectangle(
            [x0, y0, x0 + bubble_w, y0 + bubble_h],
            radius=RADIUS,
            fill=(0, 0, 0, 150),
        )
        for i, line in enumerate(lines):
            ty = y0 + PAD_Y + i * LINE_H
            dr.text((x0 + PAD_X + 1, ty + 1), line, font=font, fill=(0, 0, 0, 255))
            dr.text((x0 + PAD_X, ty), line, font=font, fill=(255, 255, 255, 255))
        im.save(os.path.join(OUT, os.path.basename(src_path)), "PNG")
        ok += 1

    # 封面补充：档案编号小字（No.4 · 此前无人调阅）
    # 注：V2.0 重出图01 已自带该小字，默认跳过；如需强制叠加设 FORCE_COVER_TAG=1
    if os.environ.get("FORCE_COVER_TAG") == "1":
        cover_path = by_num.get("01")
        if cover_path:
            im = Image.open(cover_path).convert("RGB")
            dr = ImageDraw.Draw(im, "RGBA")
            font_tag = ImageFont.truetype(FONT, 22)
            tw = int(font_tag.getlength(COVER_TAG))
            x0 = (W - tw) // 2
            y0 = 40
            dr.rounded_rectangle(
                [x0 - 16, y0 - 6, x0 + tw + 16, y0 + 36],
                radius=10,
                fill=(0, 0, 0, 120),
            )
            dr.text((x0, y0), COVER_TAG, font=font_tag, fill=(255, 255, 255, 255))
            im.save(os.path.join(OUT, os.path.basename(cover_path)), "PNG")
            print("cover tag added")
    print("subtitle done:", ok, "/", len(SUBS))


if __name__ == "__main__":
    main()
