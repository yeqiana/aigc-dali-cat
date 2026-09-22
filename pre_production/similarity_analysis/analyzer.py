#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Similarity Analysis MVP.

Comparison is evidence-first and dimension-based:

- only contract comparison fields participate,
- a dimension matches when the current and historical DNA literally share a
  canonical token,
- risk level comes from an explicit, documented rule (see classify_level),
  never from a numeric similarity score.

Risk rules (frozen for MVP):
  HIGH   : the core anomaly dimension matches AND (setting OR visual) matches.
           -> same anomaly mechanism expressed in a near-identical space.
  MEDIUM : the anomaly dimension matches alone, OR setting + visual + at least
           one relationship/character dimension all match.
  LOW    : one or more dimensions match without the above conditions.
  (none) : no dimension matched -> no evidence is emitted.
"""
from __future__ import annotations

from ..story_dna.schema import comparison_tokens
from .evidence import build_evidence, sort_evidence


def match_dimensions(current_dna: dict, historical_dna: dict) -> dict:
    cur = comparison_tokens(current_dna)
    hist = comparison_tokens(historical_dna)
    matched: dict = {}
    for dim, cur_tokens in cur.items():
        shared = cur_tokens & hist.get(dim, set())
        if shared:
            matched[dim] = sorted(shared)
    return matched


def classify_level(matches: dict) -> str | None:
    if not matches:
        return None
    dims = set(matches)
    anomaly = "anomaly" in dims
    setting = "setting" in dims
    visual = "visual_pattern" in dims
    if anomaly and (setting or visual):
        return "HIGH"
    if anomaly:
        return "MEDIUM"
    if setting and visual and ("relationship" in dims or "character" in dims):
        return "MEDIUM"
    return "LOW"


def _explain(current_id: str, related_id: str, related_title: str, level: str,
             matches: dict) -> str:
    dims = ", ".join(sorted(matches))
    features = ", ".join(sorted({f for values in matches.values() for f in values}))
    head = ("当前故事 " + current_id + " 与历史《" + (related_title or related_id) + "》("
            + related_id + ") 在 " + dims + " 维度命中相同结构化特征：" + features + "。")
    if level == "HIGH":
        tail = "核心异常机制与空间或视觉表达高度接近，建议重新设计异常机制并拉开空间或视觉差异。"
    elif level == "MEDIUM":
        tail = "部分结构接近，建议增加机制或空间上的差异化。"
    else:
        tail = "仅存在少量共性特征，属于低风险提示。"
    return head + tail + "风险等级由实际命中的特征规则得出，不使用相似度分数。"


def analyze_similarity(current_dna: dict, history: list) -> list[dict]:
    """Return sorted Similarity Evidence for every historical sample."""
    current_id = str(current_dna.get("story_id") or "")
    items: list[dict] = []
    for sample in history:
        historical_dna = sample.dna if hasattr(sample, "dna") else sample
        related_id = str(sample.episode_id if hasattr(sample, "episode_id")
                         else historical_dna.get("story_id"))
        related_title = str(sample.title if hasattr(sample, "title")
                            else historical_dna.get("title") or "")
        source_path = str(sample.source_path if hasattr(sample, "source_path") else "")
        matches = match_dimensions(current_dna, historical_dna)
        level = classify_level(matches)
        if level is None:
            continue
        features = sorted({f for values in matches.values() for f in values})
        items.append(build_evidence(
            current_story_id=current_id,
            related_episode_id=related_id,
            related_title=related_title,
            risk_level=level,
            matched_dimensions=sorted(matches),
            matched_features=features,
            explanation=_explain(current_id, related_id, related_title, level, matches),
            source_path=source_path,
        ))
    return sort_evidence(items)


__all__ = ["match_dimensions", "classify_level", "analyze_similarity"]

