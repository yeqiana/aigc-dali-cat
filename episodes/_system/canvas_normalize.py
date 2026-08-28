#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Normalize an image to the exact Story OS episode canvas without overwriting the raw source."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def require_pillow():
    try:
        from PIL import Image, ImageOps
        return Image, ImageOps
    except Exception as exc:
        raise SystemExit('Pillow is required. Run: python -m pip install -r episodes/_system/requirements.txt') from exc


def read_canvas(ep: Path) -> tuple[int, int, str]:
    ledger = ep / 'meta' / 'production-ledger.json'
    if ledger.is_file():
        data = json.loads(ledger.read_text(encoding='utf-8'))
        canvas = data.get('canvas') or {}
        w, h = canvas.get('width'), canvas.get('height')
        if isinstance(w, int) and isinstance(h, int) and w > 0 and h > 0:
            return w, h, str(canvas.get('aspect_ratio') or '')
    manifest = ep / 'meta' / 'release-manifest.json'
    if manifest.is_file():
        data = json.loads(manifest.read_text(encoding='utf-8'))
        ratio = str(((data.get('episode') or {}).get('aspect_ratio')) or '4:5')
        if ratio == '9:16':
            return 1080, 1920, ratio
    return 1080, 1350, '4:5'


def normalize(src: Path, dst: Path, width: int, height: int) -> dict:
    Image, ImageOps = require_pillow()
    if not src.is_file():
        raise SystemExit(f'input missing: {src}')
    if dst.exists():
        raise SystemExit(f'output exists: {dst}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = im.convert('RGB')
        source_size = im.size
        source_ratio = source_size[0] / source_size[1]
        target_ratio = width / height
        ratio_delta = abs(source_ratio - target_ratio) / target_ratio
        if ratio_delta > 0.18:
            raise SystemExit(
                f'source aspect too far from target for safe normalization: source={source_size[0]}x{source_size[1]}, target={width}x{height}'
            )
        out = ImageOps.fit(im, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        out.save(dst, 'PNG', optimize=True)
    return {
        'source': str(src),
        'output': str(dst),
        'source_size': list(source_size),
        'target_size': [width, height],
        'ratio_delta': round(ratio_delta, 6),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('file')
    p.add_argument('--input', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--width', required=True, type=int)
    p.add_argument('--height', required=True, type=int)
    p = sub.add_parser('episode')
    p.add_argument('episode_dir', type=Path)
    p.add_argument('--input', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    sub.add_parser('self-test')
    args = ap.parse_args()
    if args.cmd == 'self-test':
        assert read_canvas(Path('__missing__')) == (1080, 1350, '4:5')
        print('CANVAS NORMALIZE SELF-TEST PASS')
        return 0
    if args.cmd == 'episode':
        ep = args.episode_dir.resolve()
        width, height, ratio = read_canvas(ep)
    else:
        width, height, ratio = args.width, args.height, ''
    if width <= 0 or height <= 0:
        raise SystemExit('invalid target canvas')
    result = normalize(args.input.resolve(), args.output.resolve(), width, height)
    result['aspect_ratio'] = ratio
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
