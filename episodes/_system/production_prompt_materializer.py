#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministically materialize concise Production scene prompts from Frame Contracts.

The locked Storyboard/Frame Contract remain authority. These prompts are derived
transport hints only; they do not rewrite Story, Storyboard, Visual Lock or any
canonical stage. The full Resolved Frame Contract is injected by prompt_package
at generation time.
"""
from __future__ import annotations

import re
from pathlib import Path

import frame_contract

PROMPT_DIR = Path("prompts/production")
MAX_CHARS = 250
MAX_BYTES = 860


def _clean_storyboard_text(text: str) -> str:
    value = str(text or "").strip()
    value = re.sub(r"^\s*\d+\.\s*", "", value)
    value = value.replace("**", "").strip()
    return value


def prompt_for_contract(contract: dict) -> str:
    frame = str(contract.get("frame") or "").zfill(2)
    beat = _clean_storyboard_text(((contract.get("storyboard_frame") or {}).get("text") or ""))
    if not beat:
        beat = f"Frame{frame} 按锁定分镜事件自然发生"
    suffix = "按当前Frame Contract生成；真实生活相册感、自然瞬间、普通摄影曝光，避免电影布光、海报摆拍和无依据的额外元素。"
    text = f"{beat} {suffix}".strip()
    while len(text) > MAX_CHARS or len(text.encode("utf-8")) > MAX_BYTES:
        if len(beat) <= 40:
            text = f"{beat[:40]} 按当前Frame Contract生成；真实生活相册感，非电影布光、非海报摆拍。"
            break
        beat = beat[:-8].rstrip("，。；： ")
        text = f"{beat} {suffix}".strip()
    return text


def ensure(ep: Path) -> dict:
    ep = Path(ep).resolve()
    total = frame_contract.frame_count(ep)
    out_dir = ep / PROMPT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    created: list[int] = []
    reused: list[int] = []
    for frame in range(1, total + 1):
        path = out_dir / f"{frame:02d}.txt"
        if path.is_file() and path.read_text(encoding="utf-8-sig").strip():
            reused.append(frame)
            continue
        contract = frame_contract.compile_frame(ep, frame, write_cache=True)
        text = prompt_for_contract(contract)
        path.write_text(text + "\n", encoding="utf-8", newline="\n")
        created.append(frame)
    return {"created": created, "reused": reused, "prompt_dir": PROMPT_DIR.as_posix(), "total": total}


def prepare_queue(ep: Path) -> dict:
    ep = Path(ep).resolve()
    materialized = ensure(ep)
    import image_scheduler
    imported = image_scheduler.import_batch(ep, ep / PROMPT_DIR)
    return {"status": "PASS", "materialized": materialized, "queue": imported}


def self_test() -> None:
    sample = {"frame": "02", "storyboard_frame": {"text": "2. **下楼**：三人沿居民区石阶下楼。"}}
    text = prompt_for_contract(sample)
    assert "下楼" in text and "Frame Contract" in text
    assert len(text) <= 260 and len(text.encode("utf-8")) <= 900
    print("PRODUCTION PROMPT MATERIALIZER SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
