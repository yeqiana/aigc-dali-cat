#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass

DEFAULT_ASPECT_RATIO = "4:5"


@dataclass(frozen=True)
class CanvasSpec:
    aspect_ratio: str
    width: int
    height: int

    @property
    def size(self) -> tuple[int, int]:
        return self.width, self.height


SPECS: dict[str, CanvasSpec] = {
    "4:5": CanvasSpec("4:5", 1080, 1350),
    "9:16": CanvasSpec("9:16", 1080, 1920),
}

ALIASES = {
    "4x5": "4:5",
    "4/5": "4:5",
    "1080x1350": "4:5",
    "1080×1350": "4:5",
    "9x16": "9:16",
    "9/16": "9:16",
    "1080x1920": "9:16",
    "1080×1920": "9:16",
}


def normalize_aspect_ratio(value: str | None) -> str:
    if value is None or not str(value).strip():
        return DEFAULT_ASPECT_RATIO
    raw = str(value).strip().lower().replace(" ", "")
    raw = ALIASES.get(raw, raw)
    if raw not in SPECS:
        allowed = ", ".join(f"{k}={v.width}x{v.height}" for k, v in SPECS.items())
        raise ValueError(f"unsupported aspect ratio {value!r}; allowed: {allowed}")
    return raw


def resolve_canvas_spec(value: str | None) -> CanvasSpec:
    return SPECS[normalize_aspect_ratio(value)]


def describe_canvas(value: str | None = None) -> str:
    spec = resolve_canvas_spec(value)
    return f"{spec.aspect_ratio} / {spec.width}×{spec.height}"
