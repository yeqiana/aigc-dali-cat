#!/usr/bin/env python3
"""叠加 iPhone 6 随手拍质感（K1 生产工具）。

用法:
  python iphone6_casual.py <输入图> [--out <输出.jpg>] [--strength 0.5-2.0]

处理链对应 iPhone 6 后置摄像头（800 万像素小传感器）与手机自动曝光的特征：
  1. 转正 EXIF 方向，缩放到 9:16 竖图宽 1080（iPhone 6 时代竖拍约 1080x1920）
  2. 轻微高斯模糊：小传感器边缘软化
  3. 亮度噪声 + 少量彩噪：暗部颗粒感
  4. 降对比、压平黑位与高光：无 HDR，亮部易过曝发白
  5. 轻微降饱和 + 白平衡略偏冷
  6. JPEG 压缩伪影：模拟相册压缩（chroma 4:2:0，quality 约 72）
  7. 轻微自然暗角
"""

import argparse
import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def exif_transpose(img: Image.Image) -> Image.Image:
    return ImageOps.exif_transpose(img)


def apply_grain(rgb: np.ndarray, sigma: float, chroma: float, rng: np.random.Generator) -> np.ndarray:
    """叠加亮度噪声与少量彩色噪声，暗部噪点更明显。"""
    y = rgb.mean(axis=2, keepdims=True)
    noise = rng.normal(0.0, sigma, size=rgb.shape).astype(np.float32)
    luma_factor = 1.0 + (1.0 - y / 255.0) * 0.6
    noise *= luma_factor
    rgb = rgb.astype(np.float32) + noise
    rgb += rng.normal(0.0, chroma, size=rgb.shape).astype(np.float32) * np.array([1.0, 0.6, 1.2], dtype=np.float32)
    return rgb


def tone_flat(rgb: np.ndarray, contrast: float, black_lift: float, white_drop: float) -> np.ndarray:
    """无 HDR 的自动曝光曲线：压对比、抬黑位、压高光。"""
    rgb = (rgb - 128.0) * contrast + 128.0 + black_lift
    rgb = np.clip(rgb, 0.0, 255.0)
    # 高光轻微过曝发白（255 -> ~250），暗部不死黑（0 -> ~8）
    over = rgb > 240.0
    rgb[over] = 240.0 + (rgb[over] - 240.0) * white_drop
    rgb = np.clip(rgb, 0.0, 255.0)
    return rgb


def vignette(rgb: np.ndarray, strength: float) -> np.ndarray:
    """轻微自然暗角，非戏剧性。"""
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    r = np.sqrt(((xx - cx) / (w / 2.0)) ** 2 + ((yy - cy) / (h / 2.0)) ** 2)
    factor = np.clip(1.0 - (r - 0.55) * 0.5 * strength, 0.82, 1.0)
    return rgb * factor[..., None]


def process(src: Path, out: Path, strength: float) -> None:
    rng = np.random.default_rng(20260812)
    img = Image.open(src)
    img = exif_transpose(img).convert("RGB")

    target_w = 1080
    scale = target_w / img.width
    img = img.resize((target_w, int(round(img.height * scale))), Image.LANCZOS)

    blur = max(0.0, 0.45 * strength)
    if blur > 0.0:
        img = img.filter(ImageFilter.GaussianBlur(blur))

    rgb = np.asarray(img).astype(np.float32)
    rgb = apply_grain(rgb, 6.5 * strength, 3.0 * strength, rng)
    rgb = tone_flat(rgb, 1.0 - 0.06 * strength, 3.0 * strength, 0.6)
    rgb = vignette(rgb, min(strength, 1.2))
    rgb = np.clip(rgb, 0.0, 255.0).astype(np.uint8)

    out_img = Image.fromarray(rgb, "RGB")
    out_img = ImageEnhance.Color(out_img).enhance(1.0 - 0.06 * strength)

    # 白平衡略偏冷：轻微加蓝
    r, g, b = out_img.split()
    out_img = Image.merge("RGB", (r.point(lambda v: int(v * 0.99)), g, b.point(lambda v: int(v * 1.02))))

    # JPEG 压缩伪影：chroma 4:2:0，quality 随强度下降
    buf = io.BytesIO()
    out_img.save(buf, format="JPEG", quality=int(round(78 - 6 * strength)), subsampling=2)
    buf.seek(0)
    final = Image.open(buf).convert("RGB")
    final.save(out, format="JPEG", quality=92)
    print(f"ok: {out} ({final.width}x{final.height}, strength={strength})")


def main() -> None:
    parser = argparse.ArgumentParser(description="叠加 iPhone 6 随手拍质感")
    parser.add_argument("src", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--strength", type=float, default=1.0)
    args = parser.parse_args()

    if not args.src.exists():
        raise SystemExit(f"输入文件不存在: {args.src}")
    out = args.out or args.src.with_name(args.src.stem + "_iphone6.jpg")
    process(args.src, out, args.strength)


if __name__ == "__main__":
    main()
