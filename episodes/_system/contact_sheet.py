#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise SystemExit("Pillow is required for contact sheets: python -m pip install Pillow") from exc

from production_ledger import LEDGER_FILE, episode_dir


def load_ledger(ep: Path) -> dict:
    path = ep / LEDGER_FILE
    if not path.exists():
        raise SystemExit(f"production ledger missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_sources(ep: Path, data: dict, source: str) -> list[tuple[str, Path]]:
    items: list[tuple[str, Path]] = []
    for key, frame in (data.get("frames") or {}).items():
        if source == "candidate":
            info = frame.get("current_candidate")
        elif source == "approved":
            info = frame.get("approved_asset")
        else:
            info = None
        if isinstance(info, dict) and info.get("path"):
            raw = Path(info["path"])
            p = raw if raw.is_absolute() else Path(__file__).resolve().parents[2] / raw
            if p.is_file():
                items.append((key, p))
    return items


def fit_thumb(img: Image.Image, width: int, height: int) -> Image.Image:
    copy = img.convert("RGB")
    copy.thumbnail((width, height))
    canvas = Image.new("RGB", (width, height), "white")
    x = (width - copy.width) // 2
    y = (height - copy.height) // 2
    canvas.paste(copy, (x, y))
    return canvas


def main() -> None:
    p = argparse.ArgumentParser(description="Story OS Production Engine contact sheet")
    p.add_argument("episode_dir")
    p.add_argument("--source", choices=["candidate", "approved"], default="candidate")
    p.add_argument("--columns", type=int, default=4)
    p.add_argument("--thumb-width", type=int, default=216)
    p.add_argument("--output")
    args = p.parse_args()

    ep = episode_dir(args.episode_dir)
    data = load_ledger(ep)
    items = resolve_sources(ep, data, args.source)
    if not items:
        raise SystemExit(f"no {args.source} images found")

    columns = max(1, args.columns)
    canvas = data.get("canvas") or {}
    ratio = float(canvas.get("height", 1350)) / float(canvas.get("width", 1080))
    thumb_w = max(100, args.thumb_width)
    thumb_h = int(round(thumb_w * ratio))
    label_h = 32
    gap = 12
    rows = (len(items) + columns - 1) // columns
    sheet_w = gap + columns * (thumb_w + gap)
    sheet_h = gap + rows * (thumb_h + label_h + gap)
    sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for idx, (key, path) in enumerate(items):
        row, col = divmod(idx, columns)
        x = gap + col * (thumb_w + gap)
        y = gap + row * (thumb_h + label_h + gap)
        with Image.open(path) as img:
            thumb = fit_thumb(img, thumb_w, thumb_h)
        sheet.paste(thumb, (x, y))
        status = (data.get("frames") or {}).get(key, {}).get("status", "")
        draw.text((x + 4, y + thumb_h + 7), f"{key}  {status}", fill="black", font=font)

    if args.output:
        out = Path(args.output).resolve()
    else:
        root = ep / (data.get("asset_roots") or {}).get("contact_sheets", "production/contact-sheets")
        root.mkdir(parents=True, exist_ok=True)
        out = root / f"{args.source}-overview.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, format="JPEG", quality=90)
    print(out)


if __name__ == "__main__":
    main()
