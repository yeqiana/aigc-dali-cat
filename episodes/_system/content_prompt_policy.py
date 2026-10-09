#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""StoryOS generic content-prompt policy distilled from aigc-cat-partner.

This module imports the reusable production method, not project/IP assets.
Frame Contract remains authority. The policy only shapes derived scene prompts,
text placement, safety wording, QA hints, and continuity preference metadata.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
POLICY_REL = Path("config/content-production/common-policy.json")
NEGATION_WORDS = ("不要", "不得", "禁止", "不生成", "不出现", "不入图", "不表现", "避免", "no ", "without ")


def load_policy(path: Path | None = None) -> dict[str, Any]:
    source = Path(path).resolve() if path is not None else (ROOT / POLICY_REL).resolve()
    return json.loads(source.read_text(encoding="utf-8"))


def safe_rewrite_text(value: Any, policy: dict[str, Any] | None = None) -> str:
    text = str(value or "")
    cfg = policy or load_policy()
    rewrite = ((cfg.get("safety") or {}).get("rewrite_map") or {})
    for source, target in rewrite.items():
        text = text.replace(str(source), str(target))
    return text


def _negative_context(line: str) -> bool:
    low = line.lower()
    return any(token.lower() in low for token in NEGATION_WORDS)


def lint_scene_prompt(text: str, *, policy: dict[str, Any] | None = None,
                      allow_text_in_image: bool | None = None) -> list[dict[str, Any]]:
    cfg = policy or load_policy()
    issues: list[dict[str, Any]] = []
    allow_text = ((cfg.get("text_strategy") or {}).get("allow_text_in_image_default")
                  if allow_text_in_image is None else bool(allow_text_in_image))
    forbidden_text = (cfg.get("text_strategy") or {}).get("forbidden_in_image") or []
    active_risks = (cfg.get("safety") or {}).get("active_risk_terms") or []
    for line_no, raw in enumerate(str(text or "").splitlines(), 1):
        line = raw.strip()
        if not line or _negative_context(line):
            continue
        if not allow_text:
            for term in forbidden_text:
                if str(term) in line:
                    issues.append({"level": "error", "line": line_no,
                                   "code": "FORBIDDEN_IN_IMAGE_TEXT", "term": str(term)})
        for term in active_risks:
            if str(term) in line:
                issues.append({"level": "error", "line": line_no,
                               "code": "CONTENT_SAFETY_RISK", "term": str(term)})
    return issues


def continuity_policy(policy: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = policy or load_policy()
    return dict(cfg.get("continuity") or {})


def qa_checklist(contract: dict[str, Any], policy: dict[str, Any] | None = None) -> list[str]:
    cfg = policy or load_policy()
    frame = str(contract.get("frame") or "").zfill(2)
    text_strategy = cfg.get("text_strategy") or {}
    return [
        f"Frame {frame} 必须与当前 Frame Contract 的人物、场景、动作和连续性一致",
        "人物身份参考优先于临时动作和风格修饰",
        "连续帧优先复用首帧锚点/上一帧有效成图，不随机重置人物与场景",
        ("允许按本帧显式策略直接入图文字" if text_strategy.get("allow_text_in_image_default")
         else "默认不直接生成台词、旁白、人物姓名、章节标题或帧序号；文字走后期叠字"),
        "冲突、受伤和未成年人相关画面采用克制、非猎奇表达",
    ]


def build_scene_prompt(contract: dict[str, Any], *, policy: dict[str, Any] | None = None,
                       exact_scene: str | None = None,
                       max_chars: int = 250, max_bytes: int = 860) -> str:
    cfg = policy or load_policy()
    frame = str(contract.get("frame") or "").zfill(2)
    storyboard = contract.get("storyboard_frame") or {}
    beat = str(exact_scene if exact_scene is not None else storyboard.get("text") or "").strip().replace("**", "")
    if beat:
        import re
        beat = re.sub(r"^\s*\d+\.\s*", "", beat).strip()
    if not beat:
        raise ValueError(f"frame {frame} has no localized scene text; refuse generic fallback")
    beat = safe_rewrite_text(beat, cfg)
    suffixes = [
        "按当前Frame Contract生成",
        "真实生活相册感、自然瞬间、普通摄影曝光，避免电影布光和海报摆拍",
    ]
    if not (cfg.get("text_strategy") or {}).get("allow_text_in_image_default"):
        suffixes.append("不生成人物姓名标签、章节标题、帧序号或可读正文，文字留给后期叠字")
    suffixes.append("冲突与受伤只做克制、非猎奇表达")
    suffix = "；".join(suffixes) + "。"
    text = f"{beat} {suffix}".strip()
    while len(text) > int(max_chars) or len(text.encode("utf-8")) > int(max_bytes):
        if len(beat) <= 32:
            compact = "按当前Frame Contract生成；真实生活相册感；不生成姓名标签、标题、帧序号或正文；非猎奇表达。"
            text = f"{beat[:32]} {compact}".strip()
            break
        beat = beat[:-8].rstrip("，。；： ")
        text = f"{beat} {suffix}".strip()
    return text


def self_test() -> None:
    sample = {"frame": "01", "storyboard_frame": {"text": "1. **街口**：两人自然走过街口。"}}
    prompt = build_scene_prompt(sample)
    assert "Frame Contract" in prompt and not lint_scene_prompt(prompt)
    assert len(prompt) <= 250 and len(prompt.encode("utf-8")) <= 860
    print("CONTENT PROMPT POLICY SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
