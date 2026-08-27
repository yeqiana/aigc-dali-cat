#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise SystemExit("Pillow is required: python -m pip install Pillow") from exc

ROLES = (
    ("baseline", "普通相册基线"),
    ("worst_condition", "最差但成立条件"),
    ("first_major_anomaly", "首次重大异常"),
)


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return data


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(repo_root().resolve()).as_posix()


def resolve_asset(item: dict) -> Path:
    raw = item.get("asset_path") or item.get("path")
    if not isinstance(raw, str) or not raw:
        raise SystemExit("calibration asset_path missing")
    p = Path(raw)
    return p if p.is_absolute() else repo_root() / p


def fit_crop(img: Image.Image, width: int, height: int) -> Image.Image:
    src = img.convert("RGB")
    scale = max(width / src.width, height / src.height)
    size = (max(1, int(round(src.width * scale))), max(1, int(round(src.height * scale))))
    src = src.resize(size)
    left = max(0, (src.width - width) // 2)
    top = max(0, (src.height - height) // 2)
    return src.crop((left, top, left + width, top + height))


def main() -> None:
    p = argparse.ArgumentParser(description="Build and hash the three-frame realism calibration sheet")
    p.add_argument("episode_dir")
    p.add_argument("--output")
    p.add_argument("--thumb-width", type=int, default=360)
    args = p.parse_args()

    ep = Path(args.episode_dir).resolve()
    gates_path = ep / "meta/story-gates.json"
    gates = load_json(gates_path)
    visual = gates.get("visual") or {}
    calibration = visual.get("calibration") or {}
    items = []
    for role, label in ROLES:
        item = calibration.get(role)
        if not isinstance(item, dict) or item.get("decision") != "passed":
            raise SystemExit(f"calibration {role} must be recorded and passed first")
        asset = resolve_asset(item)
        if not asset.is_file():
            raise SystemExit(f"calibration asset missing: {asset}")
        actual = sha256_file(asset)
        if actual != item.get("sha256"):
            raise SystemExit(f"calibration hash drift: {role}")
        items.append((role, label, item, asset))

    thumb_w = max(180, args.thumb_width)
    with Image.open(items[0][3]) as first:
        ratio = first.height / first.width
    thumb_h = int(round(thumb_w * ratio))
    gap = 16
    label_h = 54
    sheet = Image.new("RGB", (gap + len(items) * (thumb_w + gap), gap * 2 + thumb_h + label_h), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for idx, (_, label, item, asset) in enumerate(items):
        x = gap + idx * (thumb_w + gap)
        y = gap
        with Image.open(asset) as img:
            thumb = fit_crop(img, thumb_w, thumb_h)
        sheet.paste(thumb, (x, y))
        frame = int(item.get("frame"))
        draw.text((x + 6, y + thumb_h + 8), f"{frame:02d}  {label}", fill="black", font=font)
        draw.text((x + 6, y + thumb_h + 26), str(item.get("note") or "")[:42], fill="black", font=font)

    out = Path(args.output).resolve() if args.output else ep / "production/contact-sheets/calibration.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, format="JPEG", quality=90)
    visual["calibration_contact_sheet"] = {
        "path": repo_relative(out),
        "sha256": sha256_file(out),
    }
    gates["visual"] = visual
    save_json(gates_path, gates)
    print(out)


if __name__ == "__main__":
    main()
