#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

from story_os_contract import story_os_version
from text_audit import captions_from_text, discover_input, parse_simple_subtitles_yaml

ROOT = Path(__file__).resolve().parents[2]
REPORT_REL = Path("meta/subtitle-layout-audit.json")
TARGET_CONTRACT = (2, 0, 3, 2)
SEMANTIC_RE = re.compile(r"[\u3400-\u9fffA-Za-z0-9]")
ENGINE = "story_os_subtitle_layout_v1"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def version_tuple(raw: object) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(raw or "").split("."))
    except ValueError:
        return (0,)


def layout_required(ep: Path) -> bool:
    for rel in ("meta/episode-state.json", "meta/release-manifest.json"):
        p = ep / rel
        if not p.is_file():
            continue
        try:
            if version_tuple(read_json(p).get("tool_version")) >= TARGET_CONTRACT:
                return True
        except Exception:
            continue
    return False


def contains_semantic_character(text: str) -> bool:
    return bool(SEMANTIC_RE.search(text or ""))


def punctuation_only(text: str) -> bool:
    value = (text or "").strip()
    return bool(value) and not contains_semantic_character(value)


def sanitize_wrapped_lines(lines: list[str]) -> tuple[list[str], bool]:
    cleaned = [str(x).strip() for x in lines if str(x).strip()]
    dropped = False
    if len(cleaned) >= 2 and punctuation_only(cleaned[1]):
        cleaned = [cleaned[0]] + cleaned[2:]
        dropped = True
    return cleaned, dropped


def load_caption_data(path: Path) -> dict:
    if path.suffix.lower() in {".yaml", ".yml"}:
        return parse_simple_subtitles_yaml(path)
    return captions_from_text(path)


def find_font(explicit: str | None = None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    windir = Path(os.environ.get("WINDIR", "C:/Windows"))
    candidates += [
        windir / "Fonts/msyhbd.ttc",
        Path("C:/Windows/Fonts/msyhbd.ttc"),
    ]
    for path in candidates:
        if path.is_file():
            resolved = path.resolve()
            if resolved.name.lower() != "msyhbd.ttc":
                raise RuntimeError("V2.0.3.2 canonical subtitles require Microsoft YaHei Bold (msyhbd.ttc)")
            return resolved
    raise RuntimeError(
        "Microsoft YaHei Bold font not found. Expected C:\\Windows\\Fonts\\msyhbd.ttc; "
        "do not package or substitute a random font."
    )


def wrap_caption(text: str, font, max_width: int) -> tuple[list[str], bool]:
    from PIL import Image, ImageDraw
    probe = Image.new("RGB", (max_width + 20, 100), "white")
    draw = ImageDraw.Draw(probe)
    lines: list[str] = []
    current = ""
    for ch in text.strip():
        if ch == "\n":
            if current:
                lines.append(current)
                current = ""
            continue
        candidate = current + ch
        width = draw.textlength(candidate, font=font)
        if current and width > max_width:
            lines.append(current)
            current = ch
        else:
            current = candidate
    if current:
        lines.append(current)
    lines, dropped = sanitize_wrapped_lines(lines)
    if len(lines) > 2:
        raise RuntimeError(f"caption requires {len(lines)} lines; maximum is 2")
    return lines, dropped


def resolve_repo_file(raw: object) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise RuntimeError("asset path missing")
    rel = Path(raw.strip())
    p = rel.resolve() if rel.is_absolute() else (ROOT / rel).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise RuntimeError("asset path escapes repository") from exc
    if not p.is_file():
        raise RuntimeError(f"asset missing: {raw}")
    return p


def render_one(base: Path, output: Path, caption: str, *, y: int | None, font_path: Path) -> dict:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    image = Image.open(base).convert("RGBA")
    width, height = image.size
    if width != 1080 or height not in {1350, 1920}:
        raise RuntimeError(f"subtitle renderer requires canonical 1080px-wide canvas; got {width}x{height}")
    font = ImageFont.truetype(str(font_path), 42)
    max_width = width - 144
    lines, dropped = wrap_caption(caption, font, max_width)
    if not lines:
        raise RuntimeError("non-silent caption became empty")

    x = 72
    baseline_y = int(height * 0.68) if y is None else int(y)
    line_height = 54

    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    for i, line in enumerate(lines):
        shadow_draw.text(
            (x + 1, baseline_y + i * line_height + 2),
            line,
            font=font,
            fill=(0, 0, 0, 128),
        )
    shadow = shadow.filter(ImageFilter.GaussianBlur(2))
    image = Image.alpha_composite(image, shadow)

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i, line in enumerate(lines):
        draw.text(
            (x, baseline_y + i * line_height),
            line,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=4,
            stroke_fill=(0, 0, 0, 255),
        )
    image = Image.alpha_composite(image, overlay).convert("RGB")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG")
    return {
        "lines": lines,
        "dropped_punctuation_only_second_line": dropped,
        "x": x,
        "y": baseline_y,
        "line_height": line_height,
        "font": str(font_path),
        "font_size": 42,
        "stroke_width": 4,
    }


def render_all(ep: Path, *, font_raw: str | None = None, default_y_ratio: float = 0.68) -> Path:
    if not (0.1 <= default_y_ratio <= 0.85):
        raise RuntimeError("default_y_ratio must be 0.1..0.85")
    source = discover_input(ep)
    data = load_caption_data(source)
    frames = data.get("frames") or {}
    silent = set(data.get("silent_frames") or [])
    ledger_path = ep / "meta/production-ledger.json"
    ledger = read_json(ledger_path)
    layout_cfg_path = ep / "meta/subtitle-layout.json"
    layout_cfg = read_json(layout_cfg_path) if layout_cfg_path.is_file() else {}
    y_cfg = layout_cfg.get("frames") or {}
    font_path = find_font(font_raw)

    rows = {}
    for key, frame in sorted((ledger.get("frames") or {}).items()):
        number = int(key)
        approved = frame.get("approved_asset")
        if not isinstance(approved, dict) or not approved.get("path"):
            raise RuntimeError(f"frame {key} approved_asset missing; subtitles render only from approved bases")
        base = resolve_repo_file(approved["path"])
        output = ep / "production" / "publish" / f"{key}.png"
        per = y_cfg.get(key) or y_cfg.get(str(number)) or {}
        y_value = per.get("y") if isinstance(per, dict) else None
        if y_value is None:
            from PIL import Image
            with Image.open(base) as im:
                y_value = int(im.height * default_y_ratio)

        if number in silent:
            from PIL import Image
            image = Image.open(base).convert("RGB")
            output.parent.mkdir(parents=True, exist_ok=True)
            image.save(output, format="PNG")
            layout = {
                "lines": [],
                "dropped_punctuation_only_second_line": False,
                "silent": True,
                "x": 72,
                "y": int(y_value),
                "font": str(font_path),
                "font_size": 42,
                "stroke_width": 4,
            }
            caption = ""
        else:
            caption = str(frames.get(number) or "").strip()
            if not caption:
                raise RuntimeError(f"frame {key} caption missing and not silent")
            layout = render_one(base, output, caption, y=int(y_value), font_path=font_path)
            layout["silent"] = False

        rows[key] = {
            "caption": caption,
            **layout,
            "base_path": base.relative_to(ROOT).as_posix(),
            "base_sha256": sha256_file(base),
            "output_path": output.relative_to(ROOT).as_posix(),
            "output_sha256": sha256_file(output),
        }

    report = {
        "schema_version": 1,
        "story_os_version": story_os_version(),
        "engine": ENGINE,
        "canonical_renderer": True,
        "source": source.relative_to(ROOT).as_posix(),
        "source_sha256": sha256_file(source),
        "policy": {
            "punctuation_only_second_line": "drop_entire_second_line",
            "max_lines": 2,
            "font": "Microsoft YaHei Bold",
            "font_size": 42,
            "stroke_width": 4,
            "left_margin": 72,
        },
        "frames": rows,
        "summary": {"passed": True, "frame_count": len(rows)},
    }
    out = ep / REPORT_REL
    write_json(out, report)
    print(f"SUBTITLE RENDER PASS | frames={len(rows)} | report={out}")
    return out


def verify_audit(ep: Path) -> list[str]:
    if not layout_required(ep):
        return []
    report_path = ep / REPORT_REL
    if not report_path.is_file():
        return ["meta/subtitle-layout-audit.json missing; run subtitle_layout.py render-all"]
    try:
        report = read_json(report_path)
        source = resolve_repo_file(report.get("source"))
    except Exception as exc:
        return [str(exc)]
    errors = []
    if report.get("engine") != ENGINE or report.get("canonical_renderer") is not True:
        errors.append("subtitle layout audit was not produced by canonical renderer")
    if report.get("story_os_version") != story_os_version():
        errors.append("subtitle layout audit version mismatch")
    if str(report.get("source_sha256") or "").lower() != sha256_file(source).lower():
        errors.append("subtitle layout audit is stale: caption source changed")
    policy = report.get("policy") or {}
    if policy.get("punctuation_only_second_line") != "drop_entire_second_line":
        errors.append("punctuation-only second-line policy missing")

    frames = report.get("frames")
    ledger_path = ep / "meta/production-ledger.json"
    if not ledger_path.is_file():
        errors.append("production ledger missing for subtitle layout verification")
        return errors
    ledger_keys = set((read_json(ledger_path).get("frames") or {}).keys())
    if not isinstance(frames, dict) or not frames:
        errors.append("subtitle layout frame audit missing")
        return errors
    if set(frames.keys()) != ledger_keys:
        errors.append("subtitle layout audit does not cover exactly all ledger frames")
    for key, row in frames.items():
        lines = row.get("lines")
        if not isinstance(lines, list) or len(lines) > 2:
            errors.append(f"{key}: invalid wrapped lines")
            continue
        if len(lines) >= 2 and punctuation_only(str(lines[1])):
            errors.append(f"{key}: PUNCTUATION_ONLY_SECOND_LINE")
        try:
            base = resolve_repo_file(row.get("base_path"))
            output = resolve_repo_file(row.get("output_path"))
        except Exception as exc:
            errors.append(f"{key}: {exc}")
            continue
        if str(row.get("base_sha256") or "").lower() != sha256_file(base).lower():
            errors.append(f"{key}: approved base drift")
        if str(row.get("output_sha256") or "").lower() != sha256_file(output).lower():
            errors.append(f"{key}: publish output drift")
    if errors:
        return errors
    if (report.get("summary") or {}).get("passed") is not True:
        errors.append("subtitle layout summary.passed must be true")
    return errors


def self_test() -> None:
    assert contains_semantic_character("。A")
    assert not contains_semantic_character("。！？……”）")
    lines, dropped = sanitize_wrapped_lines(["昨天我明明锁进柜子里了", "。"])
    assert lines == ["昨天我明明锁进柜子里了"] and dropped
    lines, dropped = sanitize_wrapped_lines(["第一行", "第二行。"])
    assert lines == ["第一行", "第二行。"] and not dropped
    print("SUBTITLE LAYOUT SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("render-all")
    p.add_argument("episode_dir")
    p.add_argument("--font")
    p.add_argument("--default-y-ratio", type=float, default=0.68)
    p = sub.add_parser("audit")
    p.add_argument("episode_dir")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test()
        return 0
    ep = Path(args.episode_dir).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    if args.cmd == "render-all":
        try:
            render_all(ep, font_raw=args.font, default_y_ratio=args.default_y_ratio)
            return 0
        except Exception as exc:
            print("SUBTITLE RENDER FAIL:", exc)
            return 2
    errors = verify_audit(ep)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 2
    print("SUBTITLE LAYOUT AUDIT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
