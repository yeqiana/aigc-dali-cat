#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import production_ledger

from story_os_contract import story_os_version
from canvas_spec import CANONICAL_SIZES
from text_audit import captions_from_text, discover_input, parse_simple_subtitles_yaml
import story_json
import episode_state_persistence

ROOT = Path(__file__).resolve().parents[2]
REPORT_REL = Path("meta/subtitle-layout-audit.json")
TARGET_CONTRACT = (2, 0, 3, 2)
SEMANTIC_RE = re.compile(r"[\u3400-\u9fffA-Za-z0-9]")
ENGINE = "story_os_subtitle_layout_v1"
DEFAULT_Y_RATIO = 0.52
LEFT_MIDDLE_MIN_RATIO = 0.42
LEFT_MIDDLE_MAX_RATIO = 0.62
PIXEL_SAFE_Y_RATIOS = (0.32, 0.44, 0.52, 0.60, 0.70)
MAX_AUTO_PLACEMENT_REPAIRS_PER_FRAME = 1


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return story_json.read_json(path)


def write_json(path: Path, data: dict) -> None:
    story_json.write_json(path, data)


def version_tuple(raw: object) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(raw or "").split("."))
    except ValueError:
        return (0,)


def layout_required(ep: Path) -> bool:
    state = episode_state_persistence.load(Path(ep).resolve()) or {}
    if version_tuple(state.get("tool_version")) >= TARGET_CONTRACT:
        return True
    p = ep / "meta/release-manifest.json"
    if p.is_file():
        try:
            if version_tuple(read_json(p).get("tool_version")) >= TARGET_CONTRACT:
                return True
        except Exception:
            pass
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
    if (width, height) not in CANONICAL_SIZES:
        raise RuntimeError(f"subtitle renderer requires canonical canvas; got {width}x{height}")
    font = ImageFont.truetype(str(font_path), 42)
    max_width = width - 144
    lines, dropped = wrap_caption(caption, font, max_width)
    if not lines:
        raise RuntimeError("non-silent caption became empty")

    x = 72
    baseline_y = int(height * DEFAULT_Y_RATIO) if y is None else int(y)
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


def _layout_config(ep: Path) -> tuple[Path, dict]:
    path = ep / "meta/subtitle-layout.json"
    return path, (read_json(path) if path.is_file() else {})


def _pixel_safe_ratio(raw: object) -> float:
    try:
        value = float(raw)
    except Exception as exc:
        raise RuntimeError(f"invalid pixel-safe subtitle y ratio: {raw!r}") from exc
    for allowed in PIXEL_SAFE_Y_RATIOS:
        if abs(value - allowed) <= 0.005:
            return allowed
    raise RuntimeError(
        "pixel-safe subtitle y ratio must be one of " + ", ".join(str(x) for x in PIXEL_SAFE_Y_RATIOS)
    )


def current_frame_y_ratio(ep: Path, frame: str) -> float | None:
    report = ep / REPORT_REL
    if not report.is_file():
        return None
    row = (read_json(report).get("frames") or {}).get(str(frame).zfill(2))
    if not isinstance(row, dict):
        return None
    try:
        return float(row.get("y_ratio"))
    except Exception:
        return None


def apply_pixel_safe_overrides(ep: Path, repairs: dict[str, dict]) -> dict:
    """Persist one bounded actual-pixel placement repair per frame.

    This is layout configuration, not visual-review authority.  The final publish
    pixels must still be rerendered and pass caption_image_audit afterwards.
    """
    if not repairs:
        return {"updated": []}
    ledger = production_ledger.load_authority(ep, default={}) or {}
    try:
        height = int((ledger.get("canvas") or {}).get("height"))
    except Exception as exc:
        raise RuntimeError("production ledger canvas height missing") from exc
    config_path, config = _layout_config(ep)
    config.setdefault("schema_version", 1)
    frames = config.setdefault("frames", {})
    updated: list[str] = []
    for raw_key, repair in sorted(repairs.items()):
        key = str(raw_key).zfill(2)
        if key not in (ledger.get("frames") or {}):
            raise RuntimeError(f"pixel-safe subtitle repair references unknown frame {key}")
        if not isinstance(repair, dict):
            raise RuntimeError(f"pixel-safe subtitle repair {key} must be object")
        ratio = _pixel_safe_ratio(repair.get("y_ratio"))
        reason = str(repair.get("reason") or "").strip()
        if not reason:
            raise RuntimeError(f"pixel-safe subtitle repair {key} requires obstruction reason")
        current = frames.get(key) or frames.get(str(int(key))) or {}
        used = int(current.get("auto_placement_repairs_used") or 0) if isinstance(current, dict) else 0
        if used >= MAX_AUTO_PLACEMENT_REPAIRS_PER_FRAME:
            raise RuntimeError(f"frame {key} automatic subtitle placement repair budget exhausted")
        current_ratio = current_frame_y_ratio(ep, key)
        if current_ratio is not None and abs(current_ratio - ratio) <= 0.005:
            raise RuntimeError(f"frame {key} suggested subtitle placement does not move the text")
        frames[key] = {
            **(current if isinstance(current, dict) else {}),
            "y": int(round(height * ratio)),
            "safe_zone_override_reason": reason[:500],
            "auto_placement_repairs_used": used + 1,
            "placement_source": "caption_image_actual_pixel_audit",
            "suggested_y_ratio": ratio,
        }
        updated.append(key)
    write_json(config_path, config)
    return {"updated": updated, "config_path": config_path.relative_to(ROOT).as_posix()}


def configured_dirty_frames(ep: Path) -> list[str]:
    """Return configured frames whose rendered audit has not consumed that config yet."""
    config_path, config = _layout_config(ep)
    report_path = ep / REPORT_REL
    if not config_path.is_file() or not report_path.is_file():
        return []
    configured = config.get("frames") or {}
    rendered = read_json(report_path).get("frames") or {}
    dirty: list[str] = []
    for raw_key, row in configured.items():
        key = str(raw_key).zfill(2) if str(raw_key).isdigit() else str(raw_key)
        if not isinstance(row, dict) or row.get("y") is None:
            continue
        actual = rendered.get(key)
        if not isinstance(actual, dict) or int(actual.get("y") or -1) != int(row["y"]):
            dirty.append(key)
    return sorted(set(dirty))


def render_all(
    ep: Path,
    *,
    font_raw: str | None = None,
    default_y_ratio: float = DEFAULT_Y_RATIO,
    only_frames: set[str] | None = None,
) -> Path:
    if not (0.1 <= default_y_ratio <= 0.85):
        raise RuntimeError("default_y_ratio must be 0.1..0.85")
    source = discover_input(ep)
    data = load_caption_data(source)
    frames = data.get("frames") or {}
    silent = set(data.get("silent_frames") or [])
    ledger = production_ledger.load_authority(ep, default={}) or {}
    layout_cfg_path, layout_cfg = _layout_config(ep)
    y_cfg = layout_cfg.get("frames") or {}
    font_path = find_font(font_raw)

    canvas = ledger.get("canvas") or {}
    try:
        canonical_width = int(canvas.get("width"))
        canonical_height = int(canvas.get("height"))
    except Exception as exc:
        raise RuntimeError("production ledger canvas width/height missing") from exc
    if (canonical_width, canonical_height) not in CANONICAL_SIZES:
        raise RuntimeError(f"subtitle renderer requires canonical ledger canvas; got {canonical_width}x{canonical_height}")

    out = ep / REPORT_REL
    if only_frames is not None:
        only_frames = {str(key).zfill(2) for key in only_frames}
        if not only_frames:
            raise RuntimeError("targeted subtitle rerender requires at least one frame")
        if not out.is_file():
            raise RuntimeError("targeted subtitle rerender requires an existing canonical layout audit")
        prior = read_json(out)
        if prior.get("engine") != ENGINE or prior.get("canonical_renderer") is not True:
            raise RuntimeError("targeted subtitle rerender requires a canonical prior layout audit")
        if str(prior.get("source_sha256") or "").lower() != sha256_file(source).lower():
            raise RuntimeError("targeted subtitle rerender refused: caption source changed")
        rows = dict(prior.get("frames") or {})
    else:
        rows = {}
    for key, frame in sorted((ledger.get("frames") or {}).items()):
        if only_frames is not None and key not in only_frames:
            continue
        number = int(key)
        approved = frame.get("approved_asset")
        if not isinstance(approved, dict) or not approved.get("path"):
            raise RuntimeError(f"frame {key} approved_asset missing; subtitles render only from approved bases")
        base = resolve_repo_file(approved["path"])
        output = ep / "production" / "publish" / f"{key}.png"
        per = y_cfg.get(key) or y_cfg.get(str(number)) or {}
        y_value = per.get("y") if isinstance(per, dict) else None
        override_reason = str(per.get("safe_zone_override_reason") or "").strip() if isinstance(per, dict) else ""
        if y_value is None:
            y_value = int(canonical_height * default_y_ratio)
        y_ratio = int(y_value) / canonical_height
        if not LEFT_MIDDLE_MIN_RATIO <= y_ratio <= LEFT_MIDDLE_MAX_RATIO and not override_reason:
            raise RuntimeError(f"frame {key} subtitle leaves left-middle safe zone without safe_zone_override_reason")

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
            "y_ratio": round(int(y_value) / canonical_height, 4),
            "safe_zone_override_reason": override_reason,
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
            "horizontal_alignment": "left",
            "default_y_ratio": DEFAULT_Y_RATIO,
            "preferred_vertical_zone": [LEFT_MIDDLE_MIN_RATIO, LEFT_MIDDLE_MAX_RATIO],
            "outside_zone_requires_reason": True,
        },
        "frames": rows,
        "summary": {"passed": True, "frame_count": len(rows)},
    }
    write_json(out, report)
    mode = "targeted" if only_frames is not None else "all"
    print(f"SUBTITLE RENDER PASS | mode={mode} | frames={len(rows)} | report={out}")
    return out


def render_frames(ep: Path, frames: list[str] | set[str], *, font_raw: str | None = None) -> Path:
    return render_all(ep, font_raw=font_raw, only_frames={str(key).zfill(2) for key in frames})


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
    ledger = production_ledger.load_authority(ep, default=None)
    if not isinstance(ledger, dict):
        errors.append("production ledger missing for subtitle layout verification")
        return errors
    ledger_keys = set((ledger.get("frames") or {}).keys())
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
        if int(row.get("x") or -1) != 72:
            errors.append(f"{key}: subtitle must remain left aligned at x=72")
        try:
            y_ratio=float(row.get("y_ratio"))
        except Exception:
            errors.append(f"{key}: y_ratio missing"); y_ratio=DEFAULT_Y_RATIO
        if not LEFT_MIDDLE_MIN_RATIO <= y_ratio <= LEFT_MIDDLE_MAX_RATIO and not str(row.get("safe_zone_override_reason") or "").strip():
            errors.append(f"{key}: outside left-middle zone without safe_zone_override_reason")
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
    assert DEFAULT_Y_RATIO == 0.52
    assert LEFT_MIDDLE_MIN_RATIO < DEFAULT_Y_RATIO < LEFT_MIDDLE_MAX_RATIO
    assert contains_semantic_character("。A")
    assert not contains_semantic_character("。！？……”）")
    lines, dropped = sanitize_wrapped_lines(["昨天我明明锁进柜子里了", "。"])
    assert lines == ["昨天我明明锁进柜子里了"] and dropped
    lines, dropped = sanitize_wrapped_lines(["第一行", "第二行。"])
    assert lines == ["第一行", "第二行。"] and not dropped
    assert _pixel_safe_ratio(0.44) == 0.44
    try:
        _pixel_safe_ratio(0.47)
        raise AssertionError("arbitrary subtitle auto-repair ratio must be rejected")
    except RuntimeError:
        pass
    print("SUBTITLE LAYOUT SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("render-all")
    p.add_argument("episode_dir")
    p.add_argument("--font")
    p.add_argument("--default-y-ratio", type=float, default=DEFAULT_Y_RATIO)
    p = sub.add_parser("render-frames")
    p.add_argument("episode_dir")
    p.add_argument("--frames", required=True)
    p.add_argument("--font")
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
    if args.cmd == "render-frames":
        try:
            keys = [part.strip().zfill(2) for part in str(args.frames).split(",") if part.strip()]
            render_frames(ep, keys, font_raw=args.font)
            return 0
        except Exception as exc:
            print("SUBTITLE TARGETED RENDER FAIL:", exc)
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
