#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Risk assessment: evidence in, risks out.

Only MEDIUM/HIGH evidence becomes a risk. Every risk keeps the evidence record
that produced it, so nothing is asserted without a traceable source.
"""
from __future__ import annotations

DEFAULT_HOOK_RISK = "MEDIUM"


def assess_similarity_risks(evidence: list[dict]) -> list[dict]:
    """One risk per MEDIUM/HIGH similarity evidence record."""
    risks: list[dict] = []
    for item in evidence:
        level = item.get("risk_level")
        if level not in {"MEDIUM", "HIGH"}:
            continue
        related = item.get("related_episode_id")
        title = item.get("related_title") or related
        dims = ", ".join(item.get("matched_dimensions") or [])
        summary = ("与历史《" + str(title) + "》(" + str(related) + ") 存在 " + str(level)
                   + " 结构性相似，命中维度：" + dims + "。")
        risks.append({
            "type": "similarity",
            "level": level,
            "related_episode": related,
            "matched_dimensions": list(item.get("matched_dimensions") or []),
            "summary": summary,
            "evidence": [item],
        })
    return risks


def assess_hook_risk(dna: dict) -> dict | None:
    """Hook risk from the narrative hook tokens actually present in the DNA."""
    narrative = dna.get("narrative") or {}
    hook_tokens = narrative.get("hook_type")
    if isinstance(hook_tokens, str):
        hook_tokens = [hook_tokens]
    hook_tokens = [str(t) for t in (hook_tokens or [])]
    if not hook_tokens:
        return None

    if "observational_witness_hook" in hook_tokens and "active_choice_hook" not in hook_tokens:
        level = DEFAULT_HOOK_RISK
        summary = "第一帧以远距观察或目击为主，缺少人物主动行为，开头冲突强度偏低。"
    elif "active_choice_hook" in hook_tokens:
        level = "LOW"
        summary = "开头包含人物主动行为，Hook 结构暂无明显风险。"
    else:
        return None

    hook_evidence = [e for e in (dna.get("evidence") or [])
                     if e.get("field") == "narrative.hook_type"]
    if not hook_evidence:
        return None
    hook_evidence = [{
        "kind": "story_dna",
        "field": e.get("field"),
        "token": e.get("token"),
        "keyword": e.get("keyword"),
        "anchor": e.get("anchor"),
        "snippet": e.get("snippet"),
    } for e in hook_evidence]
    return {
        "type": "hook",
        "level": level,
        "matched_dimensions": ["narrative.hook_type"],
        "summary": summary,
        "evidence": hook_evidence,
    }


def assess_risks(dna: dict, evidence: list[dict]) -> list[dict]:
    """All risks for one story: similarity risks plus an optional hook risk."""
    risks = assess_similarity_risks(evidence)
    hook = assess_hook_risk(dna)
    if hook is not None:
        risks.append(hook)
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    return sorted(risks, key=lambda r: (order.get(r.get("level"), 9), str(r.get("type"))))


__all__ = ["assess_similarity_risks", "assess_hook_risk", "assess_risks"]

