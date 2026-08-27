from __future__ import annotations

import argparse
import re
from pathlib import Path
from _common import Report, image_dimensions, load_yaml, resolve_episode_path, stage_at_least

NUMERIC = re.compile(r"^(\d+)$")


def validate(manifest_path: Path, *, release: bool = False) -> Report:
    r = Report("publish package")
    try:
        d = load_yaml(manifest_path)
    except Exception as e:
        r.error(str(e)); return r
    stage = str(d.get("stage", "candidate"))
    need = release or stage_at_least(stage, "production")
    paths = d.get("paths") or {}
    pub = resolve_episode_path(manifest_path, paths.get("publish_dir"))
    if pub is None:
        if need: r.error("paths.publish_dir 未配置")
        else: r.note("尚未配置 publish_dir，candidate 阶段跳过")
        return r
    if not pub.exists() or not pub.is_dir():
        if need: r.error(f"publish_dir 不存在: {pub}")
        else: r.note(f"publish_dir 尚不存在: {pub}")
        return r

    fmt = d.get("format") or {}
    total = int(fmt.get("frame_count") or 0)
    allowed = {"."+str(x).lower().lstrip(".") for x in (fmt.get("allowed_extensions") or ["png","jpg","jpeg"])}
    found: dict[int, Path] = {}
    ignored: list[str] = []
    for p in sorted(pub.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() not in allowed:
            ignored.append(p.name); continue
        m = NUMERIC.match(p.stem)
        if not m:
            ignored.append(p.name); continue
        idx = int(m.group(1))
        if idx in found:
            r.error(f"重复图号 {idx}: {found[idx].name} / {p.name}")
        else:
            found[idx] = p
    if ignored:
        r.note("忽略非发布编号文件: " + ", ".join(ignored[:8]) + (" ..." if len(ignored)>8 else ""))
    expected = set(range(1, total+1))
    actual = set(found)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing: r.error("缺失图号: " + ", ".join(f"{x:02d}" for x in missing))
    if extra: r.error("超出 frame_count 的图号: " + ", ".join(map(str, extra)))
    if len(found) != total:
        r.error(f"发布图数量={len(found)}，manifest frame_count={total}")

    width, height = fmt.get("width"), fmt.get("height")
    for idx,p in sorted(found.items()):
        size = image_dimensions(p)
        if size is None:
            r.warn(f"无法解析尺寸: {p.name}")
            continue
        if size != (width, height):
            r.error(f"{p.name} 尺寸 {size[0]}×{size[1]}，要求 {width}×{height}")
    return r


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("manifest",type=Path); ap.add_argument("--release",action="store_true")
    a=ap.parse_args(); r=validate(a.manifest.resolve(),release=a.release); r.print(); return 0 if r.ok else 1
if __name__ == "__main__": raise SystemExit(main())
