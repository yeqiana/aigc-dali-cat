#!/usr/bin/env python3
"""Assemble the final 20-frame S6 publish set.

Rules applied (non-destructive; reads s6_v1 / s6_v2_龙形更新 only):
- Dragon frames 07/09/10/11/12/14 use the approved reference-based versions.
- Frame 16 uses the approved _v2 cabin version.
- Every frame is normalized to the canonical 1080x1350 (4:5) canvas required by
  the repo subtitle renderer; sources are cropped to 4:5 with per-frame x/y
  bias, then Lanczos-resized.
- Output is exactly 20 files in images/s6_final/.
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "images" / "s6_v1"
V2 = ROOT / "images" / "s6_v2_龙形更新"
OUT = ROOT / "images" / "s6_final"

TARGET_W, TARGET_H = 1080, 1350

# frame -> (source dir, source file, x_bias, y_bias)
FRAMES = {
    "01": (V1, "图01_海底亮起的鳞纹.png", 0.5, 0.5),
    "02": (V1, "图02_最后一次任务.png", 0.5, 0.5),
    "03": (V1, "图03_声呐上的规整.png", 0.5, 0.5),
    "04": (V1, "图04_石柱上的鳞纹.png", 0.5, 0.5),
    "05": (V1, "图05_阿叔的警告.png", 0.85, 0.5),
    "06": (V1, "图06_宫门轮廓.png", 0.5, 0.5),
    "07": (V2, "图07_龙真身_v4_琥珀金眼.png", 0.5, 0.5),
    "08": (V1, "图08_水流把我们推过去.png", 0.5, 0.5),
    "09": (V2, "图09_它睁开了眼_v2_参考图基准.png", 0.5, 0.5),
    "10": (V2, "图10_被发现了_v2_参考图基准.png", 0.5, 0.5),
    "11": (V2, "图11_瞳孔大过观察窗_v2_参考图基准.png", 0.5, 0.5),
    "12": (V2, "图12_一次摆尾_v2_参考图基准.png", 0.5, 0.5),
    "13": (V1, "图13_灯光熄灭.png", 0.5, 0.5),
    "14": (V2, "图14_宫门合拢_v2_参考图基准.png", 0.5, 0.5),
    "15": (V1, "图15_阿叔的手在抖.png", 0.5, 0.5),
    "16": (V1, "图16_坐标封存_v2.png", 0.5, 0.5),
    "17": (V1, "图17_返航.png", 0.5, 0.5),
    "18": (V1, "图18_甲板上的潮痕.png", 0.5, 0.6),
    "19": (V1, "图19_潮痕与鳞纹.png", 0.5, 0.55),
    "20": (V1, "图20_它还在下面.png", 0.5, 0.6),
}

SHORT = {
    "01": "海底亮起的鳞纹",
    "02": "最后一次任务",
    "03": "声呐上的规整",
    "04": "石柱上的鳞纹",
    "05": "阿叔的警告",
    "06": "宫门轮廓",
    "07": "宫门里的龙",
    "08": "水流把我们推过去",
    "09": "它睁开了眼",
    "10": "被发现了",
    "11": "瞳孔大过观察窗",
    "12": "一次摆尾",
    "13": "灯光熄灭",
    "14": "宫门合拢",
    "15": "阿叔的手在抖",
    "16": "坐标封存",
    "17": "返航",
    "18": "甲板上的潮痕",
    "19": "潮痕与鳞纹",
    "20": "它还在下面",
}


def crop_to_45(im, x_bias, y_bias):
    w, h = im.size
    ratio = TARGET_W / TARGET_H
    if w / h > ratio:
        cw = min(int(h * ratio), w)
        x0 = max(0, min(w - cw, int((w - cw) * x_bias)))
        return im.crop((x0, 0, x0 + cw, h))
    ch = min(int(w / ratio), h)
    y0 = max(0, min(h - ch, int((h - ch) * y_bias)))
    return im.crop((0, y0, w, y0 + ch))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    done = []
    for key in sorted(FRAMES, key=int):
        src_dir, src_name, x_bias, y_bias = FRAMES[key]
        src = src_dir / src_name
        if not src.exists():
            raise SystemExit(f"MISSING SOURCE: {src}")
        im = Image.open(src).convert("RGB")
        im = crop_to_45(im, x_bias, y_bias)
        if im.size != (TARGET_W, TARGET_H):
            im = im.resize((TARGET_W, TARGET_H), Image.LANCZOS)
        out_name = f"图{key}_{SHORT[key]}.png"
        im.save(OUT / out_name, "PNG")
        done.append(out_name)

    print(f"assembled {len(done)} frames -> {OUT}")
    for name in sorted(done):
        p = OUT / name
        print(f"{name}  {p.stat().st_size}")


if __name__ == "__main__":
    main()
