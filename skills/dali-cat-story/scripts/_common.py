from __future__ import annotations

import hashlib
import json
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "PyYAML 未安装。请先运行: python -m pip install -r skills/dali-cat-story/requirements.txt"
    ) from exc

STAGES = [
    "candidate",
    "story_locked",
    "visual_admission",
    "production",
    "subtitled",
    "release_ready",
    "published",
]
VALID_REVIEW = {"pending", "passed", "failed", "waived"}

@dataclass
class Report:
    name: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    def merge(self, other: "Report") -> None:
        self.errors.extend(f"[{other.name}] {x}" for x in other.errors)
        self.warnings.extend(f"[{other.name}] {x}" for x in other.warnings)
        self.notes.extend(f"[{other.name}] {x}" for x in other.notes)

    @property
    def ok(self) -> bool:
        return not self.errors

    def print(self) -> None:
        status = "PASS" if self.ok else "FAIL"
        print(f"[{status}] {self.name}")
        for x in self.errors:
            print(f"  ERROR: {x}")
        for x in self.warnings:
            print(f"  WARN : {x}")
        for x in self.notes:
            print(f"  NOTE : {x}")


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML 顶层必须是 mapping: {path}")
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def stage_at_least(stage: str, target: str, *, release: bool = False) -> bool:
    if release and target == "release_ready":
        return True
    try:
        return STAGES.index(stage) >= STAGES.index(target)
    except ValueError:
        return False


def frame_numbers(values: Any, report: Report, field_name: str, total: int) -> list[int]:
    if values is None:
        return []
    if not isinstance(values, list):
        report.error(f"{field_name} 必须是数组")
        return []
    out: list[int] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            report.error(f"{field_name} 含非整数图号: {value!r}")
            continue
        if value < 1 or value > total:
            report.error(f"{field_name} 图号越界: {value}，总帧数={total}")
        out.append(value)
    return out


def resolve_episode_path(manifest_path: Path, rel: str | None) -> Path | None:
    if not rel:
        return None
    p = Path(rel)
    return p if p.is_absolute() else (manifest_path.parent / p).resolve()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def image_dimensions(path: Path) -> tuple[int, int] | None:
    ext = path.suffix.lower()
    try:
        if ext == ".png":
            with path.open("rb") as f:
                head = f.read(24)
            if len(head) >= 24 and head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR":
                return struct.unpack(">II", head[16:24])
            return None
        if ext in {".jpg", ".jpeg"}:
            with path.open("rb") as f:
                data = f.read(2)
                if data != b"\xff\xd8":
                    return None
                while True:
                    marker_start = f.read(1)
                    if not marker_start:
                        return None
                    if marker_start != b"\xff":
                        continue
                    marker = f.read(1)
                    while marker == b"\xff":
                        marker = f.read(1)
                    if not marker:
                        return None
                    code = marker[0]
                    if code in {0xD8, 0xD9}:
                        continue
                    length_raw = f.read(2)
                    if len(length_raw) != 2:
                        return None
                    length = struct.unpack(">H", length_raw)[0]
                    if length < 2:
                        return None
                    if code in {0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF}:
                        payload = f.read(length - 2)
                        if len(payload) < 5:
                            return None
                        height, width = struct.unpack(">HH", payload[1:5])
                        return width, height
                    f.seek(length - 2, 1)
    except OSError:
        return None
    return None


def normalize_frame_map(value: Any, report: Report) -> dict[int, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        report.error("subtitles.frames 必须是 mapping")
        return {}
    out: dict[int, str] = {}
    for k, v in value.items():
        try:
            idx = int(k)
        except (TypeError, ValueError):
            report.error(f"字幕图号不是整数: {k!r}")
            continue
        text = "" if v is None else str(v).strip()
        out[idx] = text
    return out
